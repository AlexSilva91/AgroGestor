import json
from pathlib import Path

from django.apps import apps
from django.conf import settings
from django.forms.models import model_to_dict
from django.utils import timezone

from .models import BackupExecucao


def _json_default(value):
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _model_rows_for_farm(model, farm):
    fields = {field.name: field for field in model._meta.fields}
    if "farm" in fields:
        queryset = model.objects.filter(farm=farm)
    elif "plantel" in fields:
        queryset = model.objects.filter(plantel__farm=farm)
    elif "animal" in fields:
        queryset = model.objects.filter(animal__farm=farm)
    elif "ocorrencia" in fields:
        queryset = model.objects.filter(ocorrencia__farm=farm)
    elif "formula" in fields:
        queryset = model.objects.filter(formula__farm=farm)
    elif "tratamento" in fields:
        queryset = model.objects.filter(tratamento__ocorrencia__farm=farm)
    else:
        return []

    rows = []
    for obj in queryset[:100000]:
        data = model_to_dict(obj)
        data["pk"] = str(obj.pk)
        rows.append(data)
    return rows


def executar_backup_config(config):
    execucao = BackupExecucao.objects.create(config=config, farm=config.farm, status="ERRO")
    try:
        root = Path(config.destino or settings.BACKUP_ROOT)
        if not root.is_absolute():
            root = settings.BASE_DIR / root
        root.mkdir(parents=True, exist_ok=True)

        timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
        safe_farm = str(config.farm_id)
        arquivo = root / f"agrogestor_fazenda_{safe_farm}_{timestamp}.json"
        payload = {
            "gerado_em": timezone.now().isoformat(),
            "fazenda": {"id": str(config.farm.id), "nome": config.farm.nome, "localizacao": config.farm.localizacao},
            "modelos": {},
        }

        for model in apps.get_models():
            rows = _model_rows_for_farm(model, config.farm)
            if rows:
                payload["modelos"][model._meta.label] = rows

        arquivo.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default))
        execucao.status = "SUCESSO"
        execucao.arquivo = str(arquivo)
        execucao.mensagem = "Backup da fazenda gerado com sucesso."
        config.ultima_execucao_em = timezone.now()
        config.save(update_fields=["ultima_execucao_em"])
        _limpar_backups_antigos(config)
    except Exception as exc:
        execucao.status = "ERRO"
        execucao.mensagem = str(exc)
    finally:
        execucao.finalizado_em = timezone.now()
        execucao.save(update_fields=["status", "arquivo", "mensagem", "finalizado_em"])
    return execucao


def _limpar_backups_antigos(config):
    manter = max(config.manter_ultimos or 1, 1)
    antigos = list(BackupExecucao.objects.filter(config=config, status="SUCESSO").order_by("-iniciado_em")[manter:])
    for item in antigos:
        if item.arquivo:
            try:
                Path(item.arquivo).unlink(missing_ok=True)
            except Exception:
                pass
        item.delete()

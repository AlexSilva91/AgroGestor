import json
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.forms.models import model_to_dict
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_http_methods

from core.permissions import (
    active_farm_queryset,
    ensure_farm_permission,
    ensure_super_admin_confirmation,
    get_request_farm,
    module_queryset,
    permission_error_response,
    tenant_get_or_404,
    user_is_super_admin,
)
from financeiro.models import LancamentoFinanceiro
from . import models


MODEL_REGISTRY = {
    "culturas": {"model": models.Cultura, "module": "gestao", "farm_field": None, "fields": ["codigo", "nome", "descricao", "ativo"]},
    "especies": {"model": models.Especie, "module": "gestao", "farm_field": None, "fields": ["cultura", "nome", "nome_cientifico", "ativo"]},
    "finalidades": {"model": models.FinalidadeProdutiva, "module": "gestao", "farm_field": None, "fields": ["cultura", "nome", "descricao", "ativo"]},
    "instalacoes": {"model": models.Instalacao, "module": "gestao", "fields": ["cultura", "nome", "tipo", "area_m2", "capacidade_informada", "ativo", "observacoes"]},
    "regras-capacidade": {"model": models.RegraCapacidade, "module": "gestao", "farm_field": None, "fields": ["cultura", "finalidade", "fase", "animais_por_m2", "area_minima_por_animal_m2", "comedouros_por_animal", "bebedouros_por_animal", "observacoes", "ativo"]},
    "planteis": {"model": models.Plantel, "module": "gestao", "fields": ["cultura", "especie", "finalidade", "instalacao", "codigo", "nome", "data_alojamento", "quantidade_inicial", "quantidade_atual", "idade_inicial_dias", "peso_medio_inicial", "status", "origem", "observacoes"]},
    "animais": {"model": models.AnimalIndividual, "module": "gestao", "fields": ["plantel", "codigo", "sexo", "nascimento", "peso_atual", "status", "observacoes"]},
    "movimentacoes": {"model": models.MovimentacaoPlantel, "module": "gestao", "fields": ["plantel", "tipo", "origem", "destino", "quantidade", "data_movimento", "motivo", "observacoes"]},
    "protocolos": {"model": models.ProtocoloManejo, "module": "manejo", "farm_field": None, "fields": ["cultura", "finalidade", "nome", "descricao", "ativo"]},
    "etapas-manejo": {"model": models.EtapaManejo, "module": "manejo", "farm_field": None, "fields": ["protocolo", "nome", "semana_inicio", "semana_fim", "objetivo", "ordem"]},
    "tarefas-manejo": {"model": models.TarefaManejo, "module": "manejo", "farm_field": None, "fields": ["etapa", "tipo", "titulo", "descricao", "semana", "dia_da_semana", "obrigatoria"]},
    "agendas": {"model": models.AgendaManejo, "module": "manejo", "fields": ["plantel", "tarefa", "data_prevista", "status", "observacoes"]},
    "ingredientes": {"model": models.Ingrediente, "module": "nutricao", "fields": ["nome", "unidade", "custo_unitario", "ativo"]},
    "formulas-racao": {"model": models.FormulaRacao, "module": "nutricao", "fields": ["cultura", "finalidade", "nome", "fase", "objetivo", "ativo"]},
    "formula-racao-itens": {"model": models.FormulaRacaoItem, "module": "nutricao", "farm_field": "formula__farm", "fields": ["formula", "ingrediente", "percentual", "observacoes"]},
    "ordens-racao": {"model": models.OrdemFabricacaoRacao, "module": "nutricao", "fields": ["formula", "quantidade_kg", "custo_total", "data_fabricacao", "validade", "status", "observacoes"]},
    "consumos-racao": {"model": models.ConsumoRacao, "module": "nutricao", "fields": ["plantel", "formula", "quantidade_kg", "data_consumo", "observacoes"]},
    "ocorrencias-sanitarias": {"model": models.OcorrenciaSanitaria, "module": "sanidade", "fields": ["plantel", "animal", "data_ocorrencia", "sintomas", "diagnostico", "severidade", "status", "observacoes"]},
    "isolamentos": {"model": models.IsolamentoSanitario, "module": "sanidade", "fields": ["ocorrencia", "plantel", "animal", "origem", "enfermaria", "data_entrada", "data_saida", "motivo", "ativo"]},
    "tratamentos": {"model": models.TratamentoSanitario, "module": "sanidade", "farm_field": "ocorrencia__farm", "fields": ["ocorrencia", "medicamento", "dose", "via_aplicacao", "frequencia", "dias_tratamento", "carencia_dias", "observacoes"]},
    "calendario-tratamento": {"model": models.CalendarioTratamento, "module": "sanidade", "farm_field": "tratamento__ocorrencia__farm", "fields": ["tratamento", "data_prevista", "data_aplicacao", "status", "observacoes"]},
    "pesagens": {"model": models.PesagemPlantel, "module": "producao", "fields": ["plantel", "data_pesagem", "quantidade_amostrada", "peso_medio", "observacoes"]},
    "producao-ovos": {"model": models.ProducaoOvos, "module": "producao", "fields": ["plantel", "data_producao", "ovos_total", "ovos_comerciais", "ovos_descartados", "ovos_trincados", "observacoes"]},
    "producao-corte": {"model": models.ProducaoCorte, "module": "producao", "fields": ["plantel", "data_registro", "peso_medio", "ganho_peso_dia", "conversao_alimentar", "mortalidade_periodo", "observacoes"]},
}


def _config(nome):
    if nome not in MODEL_REGISTRY:
        raise ValidationError("Recurso não encontrado.")
    return MODEL_REGISTRY[nome]


def _payload(request):
    return json.loads(request.body or "{}")


def _decimal(value, default="0"):
    if value in (None, ""):
        return Decimal(default)
    return Decimal(str(value))


def _get_nested_attr(obj, attr_path):
    current = obj
    for part in attr_path.split("__"):
        current = getattr(current, part)
    return current


def _queryset_for(config, request, action="view"):
    model = config["model"]
    farm_field = config.get("farm_field", "farm")
    if farm_field is None:
        return model.objects.all()
    queryset = module_queryset(model.objects.all(), request.user, config["module"], action=action, farm_field=farm_field)
    return active_farm_queryset(queryset, request, farm_field=farm_field)


def _serialize(obj):
    data = model_to_dict(obj)
    data["id"] = str(obj.pk)
    for key, value in list(data.items()):
        if hasattr(value, "isoformat"):
            data[key] = value.isoformat()
        elif value is not None and not isinstance(value, (str, int, float, bool, list, dict)):
            data[key] = str(value)
    if hasattr(obj, "farm_id"):
        data["farm_id"] = str(obj.farm_id) if obj.farm_id else None
    return data


def _coerce_value(field, value):
    if value in ("", None):
        return None if field.null or field.blank else value
    if field.get_internal_type() == "DateField":
        return parse_date(value)
    return value


def _assign_fields(instance, fields, payload):
    for field_name in fields:
        if field_name not in payload:
            continue
        field = instance._meta.get_field(field_name)
        value = _coerce_value(field, payload.get(field_name))
        if field.is_relation and value:
            setattr(instance, field_name, field.remote_field.model.objects.get(pk=value))
        else:
            setattr(instance, field_name, value)


def _validate_related_farms(instance):
    farm = getattr(instance, "farm", None)
    if not farm:
        return
    for field in instance._meta.fields:
        if not field.is_relation:
            continue
        related = getattr(instance, field.name, None)
        related_farm_id = getattr(related, "farm_id", None)
        if related_farm_id and related_farm_id != farm.id:
            raise ValidationError(f"{field.verbose_name} pertence a outra fazenda.")


def _after_create(instance, payload, request):
    if isinstance(instance, models.MovimentacaoPlantel):
        plantel = instance.plantel
        if instance.tipo in {"MORTALIDADE", "DESCARTE", "VENDA", "ABATE"}:
            plantel.quantidade_atual = max(plantel.quantidade_atual - max(instance.quantidade, 0), 0)
        if instance.tipo in {"TRANSFERENCIA", "ISOLAMENTO", "RETORNO"} and instance.destino:
            plantel.instalacao = instance.destino
        if instance.tipo == "ISOLAMENTO":
            plantel.status = "ISOLADO"
        if instance.tipo == "RETORNO" and plantel.status == "ISOLADO":
            plantel.status = "ATIVO"
        plantel.save(update_fields=["quantidade_atual", "instalacao", "status"])

    if isinstance(instance, models.OcorrenciaSanitaria) and not instance.responsavel_id:
        instance.responsavel = request.user
        instance.save(update_fields=["responsavel"])

    if isinstance(instance, models.ProducaoOvos) and payload.get("valor_receita"):
        LancamentoFinanceiro.objects.create(
            farm=instance.farm,
            plantel=instance.plantel,
            tipo="RECEITA",
            categoria="Produção de ovos",
            valor=_decimal(payload.get("valor_receita")).quantize(Decimal("0.01")),
            descricao=f"Produção de ovos em {instance.data_producao}",
            data_movimento=instance.data_producao,
        )


@login_required
@require_http_methods(["GET"])
def listar(request, recurso):
    try:
        config = _config(recurso)
        return JsonResponse([_serialize(obj) for obj in _queryset_for(config, request).order_by("-pk")], safe=False)
    except (PermissionDenied, ValidationError) as e:
        return permission_error_response(e)


@login_required
@require_http_methods(["GET"])
def detalhar(request, recurso, pk):
    try:
        config = _config(recurso)
        return JsonResponse(_serialize(get_object_or_404(_queryset_for(config, request), pk=pk)))
    except (PermissionDenied, ValidationError) as e:
        return permission_error_response(e)


@login_required
@require_http_methods(["POST"])
def criar(request, recurso):
    try:
        ensure_super_admin_confirmation(request)
        config = _config(recurso)
        payload = _payload(request)
        farm_field = config.get("farm_field", "farm")
        obj = config["model"]()
        if farm_field is not None:
            farm = get_request_farm(request, payload)
            ensure_farm_permission(request.user, farm, config["module"], "create")
            setattr(obj, farm_field, farm)
        elif not user_is_super_admin(request.user):
            raise PermissionDenied("Apenas o super admin pode alterar cadastros globais.")
        _assign_fields(obj, config["fields"], payload)
        if hasattr(obj, "criado_por_id"):
            obj.criado_por = request.user
        _validate_related_farms(obj)
        obj.save()
        _after_create(obj, payload, request)
        return JsonResponse({"success": True, "id": str(obj.pk)})
    except (PermissionDenied, ValidationError) as e:
        return permission_error_response(e)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)


@login_required
@require_http_methods(["PUT", "PATCH"])
def editar(request, recurso, pk):
    try:
        ensure_super_admin_confirmation(request)
        config = _config(recurso)
        payload = _payload(request)
        farm_field = config.get("farm_field", "farm")
        if farm_field is None:
            if not user_is_super_admin(request.user):
                raise PermissionDenied("Apenas o super admin pode alterar cadastros globais.")
            obj = get_object_or_404(config["model"], pk=pk)
        else:
            obj = tenant_get_or_404(config["model"].objects.all(), request.user, farm_field=farm_field, pk=pk)
            ensure_farm_permission(request.user, _get_nested_attr(obj, farm_field), config["module"], "update")
        _assign_fields(obj, config["fields"], payload)
        _validate_related_farms(obj)
        obj.save()
        return JsonResponse({"success": True})
    except (PermissionDenied, ValidationError) as e:
        return permission_error_response(e)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)


@login_required
@require_http_methods(["DELETE"])
def excluir(request, recurso, pk):
    try:
        ensure_super_admin_confirmation(request)
        config = _config(recurso)
        farm_field = config.get("farm_field", "farm")
        if farm_field is None:
            if not user_is_super_admin(request.user):
                raise PermissionDenied("Apenas o super admin pode alterar cadastros globais.")
            obj = get_object_or_404(config["model"], pk=pk)
        else:
            obj = tenant_get_or_404(config["model"].objects.all(), request.user, farm_field=farm_field, pk=pk)
            ensure_farm_permission(request.user, _get_nested_attr(obj, farm_field), config["module"], "delete")
        obj.delete()
        return JsonResponse({"success": True})
    except (PermissionDenied, ValidationError) as e:
        return permission_error_response(e)


@login_required
@require_http_methods(["GET"])
def calcular_capacidade(request):
    try:
        farm = get_request_farm(request)
        ensure_farm_permission(request.user, farm, "gestao", "view")
        instalacao = get_object_or_404(models.Instalacao, pk=request.GET.get("instalacao"), farm=farm)
        cultura_id = request.GET.get("cultura") or instalacao.cultura_id
        finalidade_id = request.GET.get("finalidade")
        quantidade = int(request.GET.get("quantidade") or 0)
        regras = models.RegraCapacidade.objects.filter(cultura_id=cultura_id, ativo=True)
        if finalidade_id:
            regras = regras.filter(finalidade_id=finalidade_id)
        regra = regras.order_by("fase").first()
        capacidade = instalacao.capacidade_informada or 0
        if regra and instalacao.area_m2 and regra.animais_por_m2:
            capacidade = int(Decimal(instalacao.area_m2) * regra.animais_por_m2)
        return JsonResponse({
            "instalacao_id": str(instalacao.id),
            "capacidade_recomendada": capacidade,
            "quantidade": quantidade,
            "excedente": max(quantidade - capacidade, 0) if capacidade else 0,
            "superlotado": bool(capacidade and quantidade > capacidade),
            "regra": regra.fase if regra else None,
        })
    except (PermissionDenied, ValidationError) as e:
        return permission_error_response(e)


@login_required
@require_http_methods(["POST"])
def aplicar_protocolo(request):
    try:
        ensure_super_admin_confirmation(request)
        payload = _payload(request)
        plantel = tenant_get_or_404(models.Plantel.objects.all(), request.user, pk=payload.get("plantel"))
        ensure_farm_permission(request.user, plantel.farm, "manejo", "create")
        protocolo = get_object_or_404(models.ProtocoloManejo, pk=payload.get("protocolo"))
        criadas = 0
        for tarefa in models.TarefaManejo.objects.filter(etapa__protocolo=protocolo).select_related("etapa"):
            dias = ((tarefa.semana - 1) * 7) + max(tarefa.dia_da_semana - 1, 0)
            _, created = models.AgendaManejo.objects.get_or_create(
                farm=plantel.farm,
                plantel=plantel,
                tarefa=tarefa,
                data_prevista=plantel.data_alojamento + timedelta(days=dias),
                defaults={"status": "PENDENTE"},
            )
            criadas += int(created)
        return JsonResponse({"success": True, "tarefas_criadas": criadas})
    except (PermissionDenied, ValidationError) as e:
        return permission_error_response(e)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)


@login_required
@require_http_methods(["POST"])
def concluir_tarefa_manejo(request, pk):
    try:
        ensure_super_admin_confirmation(request)
        payload = _payload(request)
        agenda = tenant_get_or_404(models.AgendaManejo.objects.all(), request.user, pk=pk)
        ensure_farm_permission(request.user, agenda.farm, "manejo", "update")
        execucao, _ = models.ExecucaoManejo.objects.update_or_create(
            agenda=agenda,
            defaults={"executado_em": timezone.now(), "executado_por": request.user, "resultado": payload.get("resultado"), "observacoes": payload.get("observacoes")},
        )
        agenda.status = "CONCLUIDA"
        agenda.save(update_fields=["status"])
        return JsonResponse({"success": True, "execucao_id": str(execucao.id)})
    except (PermissionDenied, ValidationError) as e:
        return permission_error_response(e)


@login_required
@require_http_methods(["POST"])
def fabricar_racao(request):
    try:
        ensure_super_admin_confirmation(request)
        payload = _payload(request)
        farm = get_request_farm(request, payload)
        ensure_farm_permission(request.user, farm, "nutricao", "create")
        formula = get_object_or_404(models.FormulaRacao, pk=payload.get("formula"), farm=farm)
        quantidade_kg = _decimal(payload.get("quantidade_kg"))
        ordem = models.OrdemFabricacaoRacao.objects.create(
            farm=farm,
            formula=formula,
            quantidade_kg=quantidade_kg,
            data_fabricacao=parse_date(payload.get("data_fabricacao")) or timezone.localdate(),
            validade=parse_date(payload.get("validade")) if payload.get("validade") else None,
            status="PRODUZIDA",
        )
        return JsonResponse({"success": True, "ordem_id": str(ordem.id), "custo_total": float(ordem.custo_total or 0)})
    except (PermissionDenied, ValidationError) as e:
        return permission_error_response(e)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)


@login_required
@require_http_methods(["POST"])
def registrar_consumo_racao(request):
    try:
        ensure_super_admin_confirmation(request)
        payload = _payload(request)
        plantel = tenant_get_or_404(models.Plantel.objects.all(), request.user, pk=payload.get("plantel"))
        ensure_farm_permission(request.user, plantel.farm, "nutricao", "create")
        consumo = models.ConsumoRacao.objects.create(
            farm=plantel.farm,
            plantel=plantel,
            formula=models.FormulaRacao.objects.filter(pk=payload.get("formula"), farm=plantel.farm).first(),
            quantidade_kg=_decimal(payload.get("quantidade_kg")),
            data_consumo=parse_date(payload.get("data_consumo")) or timezone.localdate(),
            observacoes=payload.get("observacoes"),
        )
        return JsonResponse({"success": True, "consumo_id": str(consumo.id)})
    except (PermissionDenied, ValidationError) as e:
        return permission_error_response(e)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)


@login_required
@require_http_methods(["POST"])
def isolar_sanitario(request):
    try:
        ensure_super_admin_confirmation(request)
        payload = _payload(request)
        ocorrencia = tenant_get_or_404(models.OcorrenciaSanitaria.objects.all(), request.user, pk=payload.get("ocorrencia"))
        ensure_farm_permission(request.user, ocorrencia.farm, "sanidade", "create")
        enfermaria = get_object_or_404(models.Instalacao, pk=payload.get("enfermaria"), farm=ocorrencia.farm, tipo__in=["ENFERMARIA", "QUARENTENA"])
        isolamento = models.IsolamentoSanitario.objects.create(
            farm=ocorrencia.farm,
            ocorrencia=ocorrencia,
            plantel=ocorrencia.plantel,
            animal=ocorrencia.animal,
            origem=ocorrencia.plantel.instalacao if ocorrencia.plantel else None,
            enfermaria=enfermaria,
            data_entrada=parse_date(payload.get("data_entrada")) or timezone.localdate(),
            motivo=payload.get("motivo") or ocorrencia.sintomas,
        )
        if ocorrencia.plantel:
            ocorrencia.plantel.instalacao = enfermaria
            ocorrencia.plantel.status = "ISOLADO"
            ocorrencia.plantel.save(update_fields=["instalacao", "status"])
        ocorrencia.status = "EM_TRATAMENTO"
        ocorrencia.save(update_fields=["status"])
        return JsonResponse({"success": True, "isolamento_id": str(isolamento.id)})
    except (PermissionDenied, ValidationError) as e:
        return permission_error_response(e)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)


@login_required
@require_http_methods(["POST"])
def gerar_calendario_tratamento(request):
    try:
        ensure_super_admin_confirmation(request)
        payload = _payload(request)
        tratamento = get_object_or_404(models.TratamentoSanitario, pk=payload.get("tratamento"))
        ensure_farm_permission(request.user, tratamento.ocorrencia.farm, "sanidade", "create")
        inicio = parse_date(payload.get("data_inicio")) or timezone.localdate()
        criados = 0
        for offset in range(tratamento.dias_tratamento):
            _, created = models.CalendarioTratamento.objects.get_or_create(
                tratamento=tratamento,
                data_prevista=inicio + timedelta(days=offset),
                defaults={"status": "PENDENTE"},
            )
            criados += int(created)
        return JsonResponse({"success": True, "aplicacoes_criadas": criados})
    except (PermissionDenied, ValidationError) as e:
        return permission_error_response(e)


@login_required
@require_http_methods(["GET"])
def relatorio_plantel(request):
    try:
        farm = get_request_farm(request)
        ensure_farm_permission(request.user, farm, "financeiro", "view")
        data = []
        for plantel in module_queryset(models.Plantel.objects.filter(farm=farm), request.user, "gestao"):
            lancamentos = LancamentoFinanceiro.objects.filter(farm=farm, plantel=plantel)
            receita = sum(item.valor for item in lancamentos.filter(tipo="RECEITA"))
            custo = sum(item.valor for item in lancamentos.filter(tipo="CUSTO"))
            data.append({"plantel_id": str(plantel.id), "codigo": plantel.codigo, "nome": plantel.nome, "receita": float(receita), "custo": float(custo), "lucro": float(receita - custo)})
        return JsonResponse(data, safe=False)
    except (PermissionDenied, ValidationError) as e:
        return permission_error_response(e)


@login_required
@require_http_methods(["GET"])
def dashboard_operacional(request):
    try:
        farm = get_request_farm(request)
        ensure_farm_permission(request.user, farm, "gestao", "view")
        hoje = timezone.localdate()
        tarefas = models.AgendaManejo.objects.filter(farm=farm)
        ocorrencias = models.OcorrenciaSanitaria.objects.filter(farm=farm)
        return JsonResponse({
            "farm_id": str(farm.id),
            "planteis_ativos": models.Plantel.objects.filter(farm=farm, status__in=["ATIVO", "ISOLADO"]).count(),
            "tarefas_pendentes": tarefas.filter(status="PENDENTE").count(),
            "tarefas_atrasadas": tarefas.filter(status="PENDENTE", data_prevista__lt=hoje).count(),
            "ocorrencias_abertas": ocorrencias.exclude(status="ENCERRADA").count(),
            "producoes_ovos_hoje": sum(item.ovos_total for item in models.ProducaoOvos.objects.filter(farm=farm, data_producao=hoje)),
            "plantel_isolado": models.Plantel.objects.filter(farm=farm, status="ISOLADO").count(),
        })
    except (PermissionDenied, ValidationError) as e:
        return permission_error_response(e)

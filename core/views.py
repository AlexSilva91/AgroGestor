import json
from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.forms.models import model_to_dict
from django.db.models import Count, Sum
from django.db import transaction
from django.http import JsonResponse, QueryDict
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime
from django.views.decorators.http import require_http_methods

from core.audit import registrar_acao
from core.backups import executar_backup_config
from core.models import BackupConfig, BackupExecucao, Fazenda, FazendaAcesso, FazendaModulo, LogAcao, ModuloSistema
from financeiro.models import LancamentoFinanceiro
from gestao import models as gestao_models
from core.permissions import (
    active_farm_id,
    active_farm_queryset,
    ensure_farm_permission,
    ensure_super_admin_confirmation,
    farms_for_user,
    get_request_farm,
    has_farm_permission,
    module_queryset,
    permission_error_response,
    user_farm_ids,
    user_is_super_admin,
)
from pastagem.models import Pastagem
from pastagem.models import MovimentacaoAnimal
from rebanho.models import Animal, HistoricoAnimal, Rebanho


INTERFACE_MODULES = [
    "financeiro",
    "rebanho",
    "pastagem",
    "gestao",
    "manejo",
    "nutricao",
    "sanidade",
    "producao",
    "usuarios",
]

MODULOS_POR_RAMO = {
    "AVICULTURA_POSTURA": {"avicultura", "gestao", "manejo", "nutricao", "sanidade", "producao", "financeiro"},
    "AVICULTURA_CORTE": {"avicultura", "gestao", "manejo", "nutricao", "sanidade", "producao", "financeiro"},
    "SUINOCULTURA": {"suinocultura", "gestao", "manejo", "nutricao", "sanidade", "producao", "financeiro"},
    "OVINOCULTURA": {"ovinocultura", "gestao", "manejo", "nutricao", "sanidade", "producao", "financeiro", "rebanho", "pastagem"},
    "BOVINOCULTURA": {"bovinocultura", "gestao", "manejo", "nutricao", "sanidade", "producao", "financeiro", "rebanho", "pastagem"},
    "CAPRINOCULTURA": {"gestao", "manejo", "nutricao", "sanidade", "producao", "financeiro", "rebanho", "pastagem"},
    "PISCICULTURA": {"gestao", "manejo", "nutricao", "sanidade", "producao", "financeiro"},
    "MULTICULTURA": {"avicultura", "suinocultura", "ovinocultura", "bovinocultura", "gestao", "manejo", "nutricao", "sanidade", "producao", "financeiro", "rebanho", "pastagem"},
    "OUTRA": {"gestao", "manejo", "nutricao", "sanidade", "producao", "financeiro"},
}

MODULOS_BASE = {
    "avicultura": ("Avicultura", "Controle de aves de postura e corte."),
    "suinocultura": ("Suinocultura", "Controle de suínos por fase e lote."),
    "ovinocultura": ("Ovinocultura", "Controle de ovinos por lote ou indivíduo."),
    "bovinocultura": ("Bovinocultura", "Controle de bovinos e rebanhos."),
    "gestao": ("Gestão multi-cultura", "Plantéis, instalações, capacidade e movimentações."),
    "manejo": ("Manejo", "Protocolos e tarefas operacionais."),
    "nutricao": ("Nutrição e ração", "Ingredientes, fórmulas, consumo e estoque."),
    "sanidade": ("Sanidade e enfermaria", "Ocorrências, tratamentos e isolamento."),
    "producao": ("Produção", "Pesagens, ovos, corte e indicadores produtivos."),
    "financeiro": ("Financeiro", "Receitas, custos e resultado por plantel."),
    "rebanho": ("Rebanho", "Controle de rebanhos e animais."),
    "pastagem": ("Pastagem", "Pastos e movimentações em áreas de pastejo."),
    "iot": ("IoT", "Sensores e automações."),
}

CRUD_ENTITIES = {
    "fazendas": {"model": Fazenda, "label": "Fazendas", "module": "usuarios", "farm_field": None, "fields": ["nome", "localizacao", "ramo_atuacao", "responsavel"]},
    "usuarios": {"model": get_user_model(), "label": "Usuários", "module": "usuarios", "farm_field": "farm", "fields": ["username", "email", "first_name", "last_name", "role", "farm", "is_active", "is_staff", "password"]},
    "fazenda-acessos": {"model": FazendaAcesso, "label": "Acessos por Fazenda", "module": "usuarios", "farm_field": "farm", "fields": ["farm", "usuario", "perfil", "ativo", "can_manage_users"]},
    "modulos": {"model": ModuloSistema, "label": "Módulos do Sistema", "module": "usuarios", "farm_field": None, "fields": ["codigo", "nome", "descricao", "ativo"]},
    "fazenda-modulos": {"model": FazendaModulo, "label": "Módulos por Fazenda", "module": "usuarios", "farm_field": "farm", "fields": ["farm", "modulo", "liberado"]},
    "backups": {"model": BackupConfig, "label": "Configurações de Backup", "module": "usuarios", "farm_field": "farm", "fields": ["farm", "ativo", "frequencia", "hora_execucao", "destino", "manter_ultimos"]},
    "logs": {"model": LogAcao, "label": "Logs de Auditoria", "module": "usuarios", "farm_field": "farm", "fields": ["farm", "usuario", "acao", "tabela_afetada", "registro_id", "descricao", "metodo", "caminho", "status_code"]},
    "rebanhos": {"model": Rebanho, "label": "Rebanhos", "module": "rebanho", "farm_field": "farm", "fields": ["farm", "nome_lote", "capacidade", "ativo"]},
    "animais-legado": {"model": Animal, "label": "Animais", "module": "rebanho", "farm_field": "farm", "fields": ["farm", "rebanho", "codigo_brincos", "sexo", "nascimento", "peso_atual", "raca", "status"]},
    "historicos-animais": {"model": HistoricoAnimal, "label": "Histórico Animal", "module": "rebanho", "farm_field": "farm", "fields": ["farm", "animal", "tipo_evento", "valor", "descricao", "data_evento"]},
    "pastagens": {"model": Pastagem, "label": "Pastagens", "module": "pastagem", "farm_field": "farm", "fields": ["farm", "nome", "area", "capacidade_suporte", "ativo"]},
    "movimentacoes-pastagem": {"model": MovimentacaoAnimal, "label": "Movimentações de Pastagem", "module": "pastagem", "farm_field": "animal__farm", "fields": ["animal", "pastagem", "data_entrada", "data_saida", "observacoes"]},
    "lancamentos": {"model": LancamentoFinanceiro, "label": "Lançamentos Financeiros", "module": "financeiro", "farm_field": "farm", "fields": ["farm", "tipo", "categoria", "valor", "descricao", "data_movimento", "animal", "plantel"]},
    "culturas": {"model": gestao_models.Cultura, "label": "Culturas", "module": "gestao", "farm_field": None, "fields": ["codigo", "nome", "descricao", "ativo"]},
    "especies": {"model": gestao_models.Especie, "label": "Espécies", "module": "gestao", "farm_field": None, "fields": ["cultura", "nome", "nome_cientifico", "ativo"]},
    "finalidades": {"model": gestao_models.FinalidadeProdutiva, "label": "Finalidades Produtivas", "module": "gestao", "farm_field": None, "fields": ["cultura", "nome", "descricao", "ativo"]},
    "instalacoes": {"model": gestao_models.Instalacao, "label": "Instalações", "module": "gestao", "farm_field": "farm", "fields": ["farm", "cultura", "nome", "tipo", "area_m2", "capacidade_informada", "ativo", "observacoes"]},
    "regras-capacidade": {"model": gestao_models.RegraCapacidade, "label": "Regras de Capacidade", "module": "gestao", "farm_field": None, "fields": ["cultura", "finalidade", "fase", "animais_por_m2", "area_minima_por_animal_m2", "comedouros_por_animal", "bebedouros_por_animal", "observacoes", "ativo"]},
    "planteis": {"model": gestao_models.Plantel, "label": "Plantéis", "module": "gestao", "farm_field": "farm", "fields": ["farm", "cultura", "especie", "finalidade", "instalacao", "codigo", "nome", "data_alojamento", "quantidade_inicial", "quantidade_atual", "idade_inicial_dias", "peso_medio_inicial", "status", "origem", "observacoes"]},
    "animais-individuais": {"model": gestao_models.AnimalIndividual, "label": "Animais Individuais", "module": "gestao", "farm_field": "farm", "fields": ["farm", "plantel", "codigo", "sexo", "nascimento", "peso_atual", "status", "observacoes"]},
    "movimentacoes-plantel": {"model": gestao_models.MovimentacaoPlantel, "label": "Movimentações de Plantel", "module": "gestao", "farm_field": "farm", "fields": ["farm", "plantel", "tipo", "origem", "destino", "quantidade", "data_movimento", "motivo", "observacoes"]},
    "protocolos": {"model": gestao_models.ProtocoloManejo, "label": "Protocolos de Manejo", "module": "manejo", "farm_field": None, "fields": ["cultura", "finalidade", "nome", "descricao", "ativo"]},
    "etapas-manejo": {"model": gestao_models.EtapaManejo, "label": "Etapas de Manejo", "module": "manejo", "farm_field": None, "fields": ["protocolo", "nome", "semana_inicio", "semana_fim", "objetivo", "ordem"]},
    "tarefas-manejo": {"model": gestao_models.TarefaManejo, "label": "Tarefas de Manejo", "module": "manejo", "farm_field": None, "fields": ["etapa", "tipo", "titulo", "descricao", "semana", "dia_da_semana", "obrigatoria"]},
    "agendas": {"model": gestao_models.AgendaManejo, "label": "Agenda de Manejo", "module": "manejo", "farm_field": "farm", "fields": ["farm", "plantel", "tarefa", "data_prevista", "status", "observacoes"]},
    "execucoes-manejo": {"model": gestao_models.ExecucaoManejo, "label": "Execuções de Manejo", "module": "manejo", "farm_field": "agenda__farm", "fields": ["agenda", "executado_em", "executado_por", "resultado", "observacoes"]},
    "ingredientes": {"model": gestao_models.Ingrediente, "label": "Ingredientes", "module": "nutricao", "farm_field": "farm", "fields": ["farm", "nome", "unidade", "custo_unitario", "ativo"]},
    "formulas-racao": {"model": gestao_models.FormulaRacao, "label": "Fórmulas de Ração", "module": "nutricao", "farm_field": "farm", "fields": ["farm", "cultura", "finalidade", "nome", "fase", "objetivo", "ativo"]},
    "formula-itens": {"model": gestao_models.FormulaRacaoItem, "label": "Itens de Fórmula", "module": "nutricao", "farm_field": "formula__farm", "fields": ["formula", "ingrediente", "percentual", "observacoes"]},
    "ordens-racao": {"model": gestao_models.OrdemFabricacaoRacao, "label": "Ordens de Ração", "module": "nutricao", "farm_field": "farm", "fields": ["farm", "formula", "quantidade_kg", "custo_total", "data_fabricacao", "validade", "status", "observacoes"]},
    "estoque": {"model": gestao_models.MovimentoEstoque, "label": "Movimento de Estoque", "module": "nutricao", "farm_field": "farm", "fields": ["farm", "ingrediente", "ordem_racao", "tipo", "quantidade", "data_movimento", "custo_unitario", "observacoes"]},
    "consumos-racao": {"model": gestao_models.ConsumoRacao, "label": "Consumos de Ração", "module": "nutricao", "farm_field": "farm", "fields": ["farm", "plantel", "formula", "quantidade_kg", "data_consumo", "observacoes"]},
    "ocorrencias-sanitarias": {"model": gestao_models.OcorrenciaSanitaria, "label": "Ocorrências Sanitárias", "module": "sanidade", "farm_field": "farm", "fields": ["farm", "plantel", "animal", "data_ocorrencia", "sintomas", "diagnostico", "severidade", "status", "observacoes"]},
    "isolamentos": {"model": gestao_models.IsolamentoSanitario, "label": "Isolamentos Sanitários", "module": "sanidade", "farm_field": "farm", "fields": ["farm", "ocorrencia", "plantel", "animal", "origem", "enfermaria", "data_entrada", "data_saida", "motivo", "ativo"]},
    "tratamentos": {"model": gestao_models.TratamentoSanitario, "label": "Tratamentos Sanitários", "module": "sanidade", "farm_field": "ocorrencia__farm", "fields": ["ocorrencia", "medicamento", "dose", "via_aplicacao", "frequencia", "dias_tratamento", "carencia_dias", "observacoes"]},
    "calendario-tratamento": {"model": gestao_models.CalendarioTratamento, "label": "Calendário de Tratamento", "module": "sanidade", "farm_field": "tratamento__ocorrencia__farm", "fields": ["tratamento", "data_prevista", "data_aplicacao", "status", "observacoes"]},
    "altas-sanitarias": {"model": gestao_models.AltaSanitaria, "label": "Altas Sanitárias", "module": "sanidade", "farm_field": "ocorrencia__farm", "fields": ["ocorrencia", "data_alta", "destino", "observacoes"]},
    "pesagens": {"model": gestao_models.PesagemPlantel, "label": "Pesagens", "module": "producao", "farm_field": "farm", "fields": ["farm", "plantel", "data_pesagem", "quantidade_amostrada", "peso_medio", "observacoes"]},
    "producao-ovos": {"model": gestao_models.ProducaoOvos, "label": "Produção de Ovos", "module": "producao", "farm_field": "farm", "fields": ["farm", "plantel", "data_producao", "ovos_total", "ovos_comerciais", "ovos_descartados", "ovos_trincados", "observacoes"]},
    "producao-corte": {"model": gestao_models.ProducaoCorte, "label": "Produção de Corte", "module": "producao", "farm_field": "farm", "fields": ["farm", "plantel", "data_registro", "peso_medio", "ganho_peso_dia", "conversao_alimentar", "mortalidade_periodo", "observacoes"]},
}


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    return render(request, "login.html", {"next_url": request.GET.get("next", "")})


@require_http_methods(["POST"])
def login_ajax(request):
    if request.user.is_authenticated:
        return JsonResponse({
            "success": True,
            "message": "Usuário já autenticado",
            "redirect_url": "/dashboard/",
        })

    try:
        data = json.loads(request.body or "{}")
        email_input = data.get("email", data.get("login", "")).strip().lower()
        password = data.get("password", "")
        next_url = data.get("next_url", "/dashboard/").strip()

        if not email_input or not password:
            return JsonResponse({"success": False, "message": "Por favor, preencha todos os campos."}, status=400)

        User = get_user_model()
        users = User.objects.filter(email__iexact=email_input)
        if users.count() != 1:
            registrar_acao(
                request,
                acao="SECURITY",
                descricao="Tentativa de login recusada: e-mail inexistente ou duplicado.",
                dados={"email": email_input},
                status_code=401,
                tabela="auth",
            )
            return JsonResponse({"success": False, "message": "E-mail ou senha incorretos."}, status=401)

        user = users.first()
        if user.is_active and user.check_password(password):
            login(request, user)
            registrar_acao(
                request,
                acao="LOGIN",
                descricao="Login realizado com sucesso.",
                farm=getattr(user, "farm", None),
                dados={"email": email_input},
                status_code=200,
                tabela="auth",
            )
            redirect_url = next_url if next_url else "/dashboard/"
            if not redirect_url.startswith("/") or "//" in redirect_url:
                redirect_url = "/dashboard/"
            return JsonResponse({
                "success": True,
                "message": "Login realizado com sucesso!",
                "redirect_url": redirect_url,
            })

        registrar_acao(
            request,
            acao="SECURITY",
            descricao="Tentativa de login recusada: senha incorreta ou usuário inativo.",
            farm=getattr(user, "farm", None),
            dados={"email": email_input},
            status_code=401,
            tabela="auth",
        )
        return JsonResponse({"success": False, "message": "E-mail ou senha incorretos."}, status=401)
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "message": "Erro no processamento dos dados."}, status=400)
    except Exception:
        return JsonResponse({"success": False, "message": "Erro interno do servidor."}, status=500)


@login_required
def dashboard(request):
    User = get_user_model()
    if user_is_super_admin(request.user):
        usuarios_list = User.objects.all().order_by("-date_joined")
    else:
        farms = user_farm_ids(request.user)
        usuarios_list = (
            User.objects.filter(farm_id__in=farms)
            | User.objects.filter(fazenda_acessos__farm_id__in=farms)
        ).distinct().order_by("-date_joined")

    paginator = Paginator(usuarios_list, 10)
    usuarios = paginator.get_page(request.GET.get("page"))
    fazendas = farms_for_user(request.user).order_by("nome")
    active_id = active_farm_id(request)
    fazenda_ativa = fazendas.filter(id=active_id).first() if active_id else fazendas.first()

    if user_is_super_admin(request.user):
        modulos_liberados = INTERFACE_MODULES
    elif fazenda_ativa:
        modulos_liberados = list(
            FazendaModulo.objects.filter(farm=fazenda_ativa, liberado=True)
            .select_related("modulo")
            .values_list("modulo__codigo", flat=True)
        )
        modulos_liberados.extend(
            module
            for module in INTERFACE_MODULES
            if module not in modulos_liberados and has_farm_permission(request.user, fazenda_ativa, module, "view")
        )
    else:
        modulos_liberados = []

    context = {
        "usuarios": usuarios,
        "rebanhos": active_farm_queryset(module_queryset(Rebanho.objects.filter(ativo=True), request.user, "rebanho"), request),
        "animais": active_farm_queryset(module_queryset(Animal.objects.all(), request.user, "rebanho"), request).order_by("codigo_brincos"),
        "pastagens": active_farm_queryset(module_queryset(Pastagem.objects.filter(ativo=True), request.user, "pastagem"), request).order_by("nome"),
        "is_super_admin": user_is_super_admin(request.user),
        "grupos": Group.objects.all().order_by("name"),
        "fazendas": fazendas,
        "fazenda_ativa": fazenda_ativa,
        "modulos_liberados": modulos_liberados,
        "backup_root": settings.BACKUP_ROOT,
    }
    return render(request, "base/dashboard_content.html", context)


def _chart_rows(queryset, label_field, value_field, limit=8):
    rows = []
    for item in queryset[:limit]:
        rows.append({
            "label": item.get(label_field) or "Não informado",
            "value": float(item.get(value_field) or 0),
        })
    return rows


def _empty_queryset(model):
    return model.objects.none()


def _month_start(date_value):
    return date_value.replace(day=1)


def _add_months(date_value, months):
    month = date_value.month - 1 + months
    year = date_value.year + month // 12
    month = month % 12 + 1
    return date_value.replace(year=year, month=month, day=1)


def _metricas_dashboard_scope(request):
    if user_is_super_admin(request.user):
        return {
            "label": "Todas as fazendas",
            "farm": None,
            "planteis": gestao_models.Plantel.objects.all(),
            "producao_ovos": gestao_models.ProducaoOvos.objects.all(),
            "producao_corte": gestao_models.ProducaoCorte.objects.all(),
            "ocorrencias": gestao_models.OcorrenciaSanitaria.objects.all(),
            "movimentacoes": gestao_models.MovimentacaoPlantel.objects.all(),
            "animais_individuais": gestao_models.AnimalIndividual.objects.all(),
            "animais_legado": Animal.objects.all(),
            "lancamentos": LancamentoFinanceiro.objects.all(),
        }

    farm = get_request_farm(request)
    ensure_farm_permission(request.user, farm, "gestao", "view")
    has_financeiro = has_farm_permission(request.user, farm, "financeiro", "view")
    has_producao = has_farm_permission(request.user, farm, "producao", "view")
    has_sanidade = has_farm_permission(request.user, farm, "sanidade", "view")
    has_rebanho = has_farm_permission(request.user, farm, "rebanho", "view")

    return {
        "label": farm.nome,
        "farm": farm,
        "planteis": gestao_models.Plantel.objects.filter(farm=farm),
        "producao_ovos": gestao_models.ProducaoOvos.objects.filter(farm=farm) if has_producao else _empty_queryset(gestao_models.ProducaoOvos),
        "producao_corte": gestao_models.ProducaoCorte.objects.filter(farm=farm) if has_producao else _empty_queryset(gestao_models.ProducaoCorte),
        "ocorrencias": gestao_models.OcorrenciaSanitaria.objects.filter(farm=farm) if has_sanidade else _empty_queryset(gestao_models.OcorrenciaSanitaria),
        "movimentacoes": gestao_models.MovimentacaoPlantel.objects.filter(farm=farm),
        "animais_individuais": gestao_models.AnimalIndividual.objects.filter(farm=farm),
        "animais_legado": Animal.objects.filter(farm=farm) if has_rebanho else Animal.objects.none(),
        "lancamentos": LancamentoFinanceiro.objects.filter(farm=farm) if has_financeiro else _empty_queryset(LancamentoFinanceiro),
    }


@login_required
@require_http_methods(["GET"])
def metricas_dashboard(request):
    try:
        scope = _metricas_dashboard_scope(request)
        hoje = timezone.localdate()
        inicio = hoje - timedelta(days=13)

        planteis = scope["planteis"]
        producao_ovos = scope["producao_ovos"]
        producao_corte = scope["producao_corte"]
        ocorrencias = scope["ocorrencias"]
        movimentacoes = scope["movimentacoes"]
        animais_individuais = scope["animais_individuais"]
        animais_legado = scope["animais_legado"]
        lancamentos = scope["lancamentos"]

        receita = lancamentos.filter(tipo="RECEITA").aggregate(total=Sum("valor"))["total"] or 0
        custo = lancamentos.filter(tipo="CUSTO").aggregate(total=Sum("valor"))["total"] or 0
        ovos_total = producao_ovos.aggregate(total=Sum("ovos_total"))["total"] or 0
        corte_mortalidade = producao_corte.aggregate(total=Sum("mortalidade_periodo"))["total"] or 0
        movimentacao_mortalidade = movimentacoes.filter(tipo="MORTALIDADE").aggregate(total=Sum("quantidade"))["total"] or 0
        nascimento_total = animais_individuais.exclude(nascimento__isnull=True).count() + animais_legado.exclude(nascimento__isnull=True).count()

        inicio_mes = _add_months(_month_start(hoje), -5)
        serie_sanidade = []
        serie_mortalidade_natalidade = []
        for offset in range(6):
            mes_inicio = _add_months(inicio_mes, offset)
            mes_fim = _add_months(mes_inicio, 1)
            label = mes_inicio.strftime("%m/%Y")
            ocorrencias_mes = ocorrencias.filter(data_ocorrencia__gte=mes_inicio, data_ocorrencia__lt=mes_fim).count()
            mortalidade_mes = (
                (movimentacoes.filter(tipo="MORTALIDADE", data_movimento__gte=mes_inicio, data_movimento__lt=mes_fim).aggregate(total=Sum("quantidade"))["total"] or 0)
                + (producao_corte.filter(data_registro__gte=mes_inicio, data_registro__lt=mes_fim).aggregate(total=Sum("mortalidade_periodo"))["total"] or 0)
            )
            natalidade_mes = (
                animais_individuais.filter(nascimento__gte=mes_inicio, nascimento__lt=mes_fim).count()
                + animais_legado.filter(nascimento__gte=mes_inicio, nascimento__lt=mes_fim).count()
            )
            serie_sanidade.append({"label": label, "value": ocorrencias_mes})
            serie_mortalidade_natalidade.append({"label": label, "mortalidade": int(mortalidade_mes or 0), "natalidade": int(natalidade_mes or 0)})

        producao_por_dia = {
            item["data_producao"].isoformat(): int(item["total"] or 0)
            for item in producao_ovos.filter(data_producao__gte=inicio, data_producao__lte=hoje)
            .values("data_producao")
            .annotate(total=Sum("ovos_total"))
            .order_by("data_producao")
        }
        serie_ovos = []
        for offset in range(14):
            dia = inicio + timedelta(days=offset)
            serie_ovos.append({"label": dia.strftime("%d/%m"), "value": producao_por_dia.get(dia.isoformat(), 0)})

        financeiro_por_plantel = []
        for row in (
            lancamentos.filter(plantel__isnull=False)
            .values("plantel__codigo", "plantel__nome")
            .annotate(total=Sum("valor"))
            .order_by("-total")[:8]
        ):
            financeiro_por_plantel.append({
                "label": f"{row.get('plantel__codigo') or ''} {row.get('plantel__nome') or ''}".strip() or "Plantel",
                "value": float(row["total"] or 0),
            })

        data = {
            "scope": scope["label"],
            "is_super_admin": user_is_super_admin(request.user),
            "cards": {
                "planteis_ativos": planteis.filter(status__in=["ATIVO", "ISOLADO"]).count(),
                "animais_atual": int(planteis.aggregate(total=Sum("quantidade_atual"))["total"] or 0),
                "ovos_total": int(ovos_total or 0),
                "receita": float(receita),
                "custo": float(custo),
                "resultado": float(receita - custo),
                "mortalidade": int((corte_mortalidade or 0) + (movimentacao_mortalidade or 0)),
                "natalidade": int(nascimento_total),
                "ocorrencias_abertas": ocorrencias.exclude(status="ENCERRADA").count(),
            },
            "charts": {
                "plantel_por_cultura": _chart_rows(
                    planteis.values("cultura__nome").annotate(total=Sum("quantidade_atual")).order_by("-total"),
                    "cultura__nome",
                    "total",
                ),
                "plantel_por_status": _chart_rows(
                    planteis.values("status").annotate(total=Count("id")).order_by("-total"),
                    "status",
                    "total",
                ),
                "producao_ovos_14_dias": serie_ovos,
                "financeiro_por_plantel": financeiro_por_plantel,
                "sanidade_por_mes": serie_sanidade,
                "sanidade_por_plantel": _chart_rows(
                    ocorrencias.filter(plantel__isnull=False)
                    .values("plantel__codigo", "plantel__nome")
                    .annotate(total=Count("id"))
                    .order_by("-total"),
                    "plantel__codigo",
                    "total",
                ),
                "mortalidade_vs_natalidade": serie_mortalidade_natalidade,
            },
        }
        return JsonResponse(data)
    except (PermissionDenied, ValidationError) as e:
        return permission_error_response(e)


@login_required
@require_http_methods(["GET"])
def listar_fazendas_usuario(request):
    fazendas = farms_for_user(request.user).order_by("nome")
    return JsonResponse({
        "active_farm_id": active_farm_id(request),
        "is_super_admin": user_is_super_admin(request.user),
        "fazendas": [{"id": str(f.id), "nome": f.nome, "localizacao": f.localizacao} for f in fazendas],
    })


@login_required
@require_http_methods(["POST"])
def definir_fazenda_ativa(request):
    try:
        data = json.loads(request.body or "{}")
        farm = farms_for_user(request.user).get(id=data.get("farm_id"))
        request.session["active_farm_id"] = str(farm.id)
        return JsonResponse({"success": True, "active_farm_id": str(farm.id), "nome": farm.nome})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)


def _ensure_modulos_base():
    for codigo, (nome, descricao) in MODULOS_BASE.items():
        ModuloSistema.objects.update_or_create(
            codigo=codigo,
            defaults={"nome": nome, "descricao": descricao, "ativo": True},
        )


def _modulos_para_ramo(ramo):
    return MODULOS_POR_RAMO.get(ramo or "OUTRA", MODULOS_POR_RAMO["OUTRA"])


@login_required
@require_http_methods(["POST"])
def criar_fazenda_com_admin(request):
    try:
        ensure_super_admin_confirmation(request)
        if not user_is_super_admin(request.user):
            raise PermissionDenied("Apenas o super admin pode cadastrar fazendas.")

        data = json.loads(request.body or "{}")
        nome = (data.get("nome") or "").strip()
        email = (data.get("admin_email") or "").strip().lower()
        username = (data.get("admin_username") or email.split("@")[0]).strip()
        password = data.get("admin_password") or ""
        ramo = data.get("ramo_atuacao") or "MULTICULTURA"

        if not nome:
            return JsonResponse({"success": False, "error": "Informe o nome da fazenda."}, status=400)
        if not email:
            return JsonResponse({"success": False, "error": "Informe o e-mail do admin responsável."}, status=400)

        User = get_user_model()
        with transaction.atomic():
            _ensure_modulos_base()
            admin_user = User.objects.filter(email__iexact=email).first()
            if admin_user:
                admin_user.username = username or admin_user.username
                admin_user.first_name = (data.get("admin_first_name") or admin_user.first_name).strip()
                admin_user.last_name = (data.get("admin_last_name") or admin_user.last_name).strip()
                admin_user.role = "ADMIN"
                admin_user.is_active = True
                if password:
                    admin_user.set_password(password)
                admin_user.save()
            else:
                if not password:
                    return JsonResponse({"success": False, "error": "Informe uma senha para o novo admin."}, status=400)
                admin_user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=(data.get("admin_first_name") or "").strip(),
                    last_name=(data.get("admin_last_name") or "").strip(),
                    role="ADMIN",
                    is_active=True,
                )

            farm = Fazenda.objects.create(
                nome=nome,
                localizacao=(data.get("localizacao") or "").strip(),
                ramo_atuacao=ramo,
                responsavel=admin_user,
            )
            admin_user.farm = farm
            admin_user.role = "ADMIN"
            admin_user.save(update_fields=["farm", "role"])

            FazendaAcesso.objects.update_or_create(
                farm=farm,
                usuario=admin_user,
                defaults={"perfil": "ADMIN", "ativo": True},
            )

            liberados = _modulos_para_ramo(ramo)
            for modulo in ModuloSistema.objects.filter(ativo=True):
                FazendaModulo.objects.update_or_create(
                    farm=farm,
                    modulo=modulo,
                    defaults={"liberado": modulo.codigo in liberados},
                )

        registrar_acao(
            request,
            acao="CREATE",
            descricao="Fazenda cadastrada com admin responsável e módulos iniciais.",
            farm=farm,
            dados={"farm_id": str(farm.id), "admin_id": admin_user.id, "ramo_atuacao": ramo, "modulos": sorted(liberados)},
            status_code=201,
            tabela="fazenda",
        )
        return JsonResponse({
            "success": True,
            "farm": {"id": str(farm.id), "nome": farm.nome, "ramo_atuacao": farm.ramo_atuacao},
            "admin": {"id": admin_user.id, "email": admin_user.email, "username": admin_user.username},
            "modulos_liberados": sorted(liberados),
        }, status=201)
    except (PermissionDenied, ValidationError) as e:
        return permission_error_response(e)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)


@login_required
@require_http_methods(["GET"])
def listar_modulos_fazenda(request):
    try:
        farm = get_request_farm(request)
        ensure_farm_permission(request.user, farm, "usuarios", "manage")
        existentes = {
            str(fm.modulo_id): fm
            for fm in FazendaModulo.objects.filter(farm=farm).select_related("modulo")
        }
        data = []
        for modulo in ModuloSistema.objects.filter(ativo=True).order_by("nome"):
            vinculo = existentes.get(str(modulo.id))
            data.append({
                "id": str(modulo.id),
                "codigo": modulo.codigo,
                "nome": modulo.nome,
                "descricao": modulo.descricao,
                "liberado": True if vinculo is None else vinculo.liberado,
            })
        return JsonResponse({"farm_id": str(farm.id), "modulos": data})
    except (PermissionDenied, ValidationError) as e:
        return permission_error_response(e)


@login_required
@require_http_methods(["POST"])
def salvar_modulos_fazenda(request):
    try:
        ensure_super_admin_confirmation(request)
        if not user_is_super_admin(request.user):
            raise PermissionDenied("Apenas o super admin pode liberar módulos.")
        data = json.loads(request.body or "{}")
        farm = get_request_farm(request, data)
        liberados = set(data.get("modulos", []))
        for modulo in ModuloSistema.objects.filter(ativo=True):
            FazendaModulo.objects.update_or_create(
                farm=farm,
                modulo=modulo,
                defaults={"liberado": modulo.codigo in liberados or str(modulo.id) in liberados},
            )
        return JsonResponse({"success": True})
    except (PermissionDenied, ValidationError) as e:
        return permission_error_response(e)


@login_required
@require_http_methods(["GET"])
def listar_acessos_fazenda(request):
    try:
        farm = get_request_farm(request)
        ensure_farm_permission(request.user, farm, "usuarios", "manage")
        acessos = FazendaAcesso.objects.filter(farm=farm).select_related("usuario").order_by("usuario__username")
        return JsonResponse({
            "farm_id": str(farm.id),
            "acessos": [
                {
                    "id": str(a.id),
                    "usuario_id": a.usuario_id,
                    "usuario": a.usuario.username,
                    "email": a.usuario.email,
                    "perfil": a.perfil,
                    **{field.name: getattr(a, field.name) for field in FazendaAcesso._meta.fields if field.name.startswith("can_")},
                }
                for a in acessos
            ],
        })
    except (PermissionDenied, ValidationError) as e:
        return permission_error_response(e)


@login_required
@require_http_methods(["PUT", "PATCH"])
def editar_acesso_fazenda(request, pk):
    try:
        ensure_super_admin_confirmation(request)
        data = json.loads(request.body or "{}")
        acesso = FazendaAcesso.objects.select_related("farm").get(pk=pk)
        ensure_farm_permission(request.user, acesso.farm, "usuarios", "manage")
        if "perfil" in data:
            acesso.perfil = data["perfil"]
        for field in FazendaAcesso._meta.fields:
            if field.name.startswith("can_") and field.name in data:
                setattr(acesso, field.name, bool(data[field.name]))
        acesso.save()
        return JsonResponse({"success": True})
    except (PermissionDenied, ValidationError) as e:
        return permission_error_response(e)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)


def _usuarios_visiveis(user):
    User = get_user_model()
    if user_is_super_admin(user):
        return User.objects.all()
    farms = user_farm_ids(user)
    return (
        User.objects.filter(farm_id__in=farms)
        | User.objects.filter(fazenda_acessos__farm_id__in=farms)
    ).distinct()


def _serialize_usuario(user):
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "is_active": user.is_active,
        "is_staff": user.is_staff,
        "role": user.role,
        "groups": list(user.groups.values_list("id", flat=True)),
    }


def _perfil_por_role(role):
    return "ADMIN" if role in {"ADMIN", "FAZENDEIRO", "SUPERADMIN"} else "OPERADOR"


def _request_form_data(request):
    if request.method == "POST":
        return request.POST
    return QueryDict(request.body)


def _crud_config(entity):
    if entity not in CRUD_ENTITIES:
        raise ValidationError("Entidade não encontrada.")
    return CRUD_ENTITIES[entity]


def _crud_can_global(user):
    return user_is_super_admin(user)


def _crud_queryset(config, request, action="view"):
    model = config["model"]
    farm_field = config.get("farm_field")
    if farm_field is None:
        if not _crud_can_global(request.user):
            raise PermissionDenied("Apenas o super admin pode acessar esta entidade.")
        return model.objects.all()
    queryset = module_queryset(model.objects.all(), request.user, config["module"], action=action, farm_field=farm_field)
    return active_farm_queryset(queryset, request, farm_field=farm_field)


def _crud_field_schema(model, field_name):
    if field_name == "password":
        return {"name": "password", "label": "Senha", "type": "password", "required": False}
    field = model._meta.get_field(field_name)
    schema = {"name": field_name, "label": field.verbose_name.title(), "required": not field.blank and not field.null}
    if getattr(field, "choices", None):
        schema["type"] = "select"
        schema["choices"] = [{"value": value, "label": label} for value, label in field.choices]
    elif field.is_relation:
        schema["type"] = "relation"
        schema["model"] = field.remote_field.model._meta.verbose_name.title()
    elif field.get_internal_type() in {"BooleanField", "NullBooleanField"}:
        schema["type"] = "checkbox"
    elif field.get_internal_type() in {"DateField"}:
        schema["type"] = "date"
    elif field.get_internal_type() in {"DateTimeField"}:
        schema["type"] = "datetime-local"
    elif field.get_internal_type() in {"IntegerField", "PositiveIntegerField", "PositiveSmallIntegerField", "DecimalField", "FloatField"}:
        schema["type"] = "number"
    elif field.get_internal_type() in {"TextField", "JSONField"}:
        schema["type"] = "textarea"
    else:
        schema["type"] = "text"
    return schema


def _crud_serialize(obj):
    data = model_to_dict(obj)
    data["id"] = str(obj.pk)
    display = str(obj)
    for key, value in list(data.items()):
        if hasattr(value, "isoformat"):
            data[key] = value.isoformat()
        elif value is not None and not isinstance(value, (str, int, float, bool, list, dict)):
            data[key] = str(value)
    return {"id": str(obj.pk), "display": display, "data": data}


def _crud_coerce(field, value):
    if value in ("", None):
        return None if field.null or field.blank else value
    if field.get_internal_type() == "DateField":
        return parse_date(value)
    if field.get_internal_type() == "DateTimeField":
        return parse_datetime(value)
    return value


def _crud_apply(obj, fields, payload):
    User = get_user_model()
    password = payload.get("password")
    for field_name in fields:
        if field_name == "password":
            continue
        if field_name not in payload:
            continue
        field = obj._meta.get_field(field_name)
        value = _crud_coerce(field, payload.get(field_name))
        if field.is_relation and value:
            value = field.remote_field.model.objects.get(pk=value)
        setattr(obj, field_name, value)
    if isinstance(obj, User) and password:
        obj.set_password(password)


def _crud_payload(request):
    return json.loads(request.body or "{}")


@login_required
@require_http_methods(["GET"])
def crud_schema(request):
    entities = []
    for key, config in CRUD_ENTITIES.items():
        try:
            _crud_queryset(config, request)
        except PermissionDenied:
            continue
        entities.append({"key": key, "label": config["label"]})
    return JsonResponse({"entities": entities})


@login_required
@require_http_methods(["GET"])
def crud_listar(request, entity):
    try:
        config = _crud_config(entity)
        model = config["model"]
        fields = [_crud_field_schema(model, field) for field in config["fields"]]
        rows = [_crud_serialize(obj) for obj in _crud_queryset(config, request).order_by("-pk")[:300]]
        return JsonResponse({"entity": entity, "label": config["label"], "fields": fields, "rows": rows})
    except (PermissionDenied, ValidationError) as e:
        return permission_error_response(e)


@login_required
@require_http_methods(["GET"])
def crud_detalhar(request, entity, pk):
    try:
        config = _crud_config(entity)
        obj = _crud_queryset(config, request).get(pk=pk)
        return JsonResponse(_crud_serialize(obj))
    except (PermissionDenied, ValidationError) as e:
        return permission_error_response(e)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=404)


@login_required
@require_http_methods(["POST"])
def crud_criar(request, entity):
    try:
        ensure_super_admin_confirmation(request)
        config = _crud_config(entity)
        payload = _crud_payload(request)
        farm_field = config.get("farm_field")
        if farm_field is None and not user_is_super_admin(request.user):
            raise PermissionDenied("Apenas o super admin pode criar esta entidade.")
        if farm_field is not None:
            farm = get_request_farm(request, payload)
            ensure_farm_permission(request.user, farm, config["module"], "create")
        obj = config["model"]()
        if farm_field == "farm" and "farm" not in payload:
            obj.farm = farm
        _crud_apply(obj, config["fields"], payload)
        obj.save()
        return JsonResponse({"success": True, "id": str(obj.pk)}, status=201)
    except (PermissionDenied, ValidationError) as e:
        return permission_error_response(e)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)


@login_required
@require_http_methods(["PUT", "PATCH"])
def crud_editar(request, entity, pk):
    try:
        ensure_super_admin_confirmation(request)
        config = _crud_config(entity)
        payload = _crud_payload(request)
        obj = _crud_queryset(config, request, action="update").get(pk=pk)
        if config.get("farm_field") is not None:
            ensure_farm_permission(request.user, _get_nested_attr(obj, config["farm_field"]), config["module"], "update")
        _crud_apply(obj, config["fields"], payload)
        obj.save()
        return JsonResponse({"success": True})
    except (PermissionDenied, ValidationError) as e:
        return permission_error_response(e)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)


@login_required
@require_http_methods(["DELETE"])
def crud_excluir(request, entity, pk):
    try:
        ensure_super_admin_confirmation(request)
        config = _crud_config(entity)
        obj = _crud_queryset(config, request, action="delete").get(pk=pk)
        if config.get("farm_field") is not None:
            ensure_farm_permission(request.user, _get_nested_attr(obj, config["farm_field"]), config["module"], "delete")
        obj.delete()
        return JsonResponse({"success": True})
    except (PermissionDenied, ValidationError) as e:
        return permission_error_response(e)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)


@login_required
@require_http_methods(["POST"])
def criar_usuario(request):
    try:
        ensure_super_admin_confirmation(request)
        data = _request_form_data(request)
        farm = get_request_farm(request, data)
        ensure_farm_permission(request.user, farm, "usuarios", "manage")

        password = data.get("password", "")
        if password != data.get("confirm_password", ""):
            return JsonResponse({"success": False, "error": "As senhas não conferem."}, status=400)

        role = data.get("role", "FUNCIONARIO")
        User = get_user_model()
        user = User.objects.create_user(
            username=data.get("username", "").strip(),
            email=data.get("email", "").strip().lower(),
            password=password,
            first_name=data.get("first_name", "").strip(),
            last_name=data.get("last_name", "").strip(),
            farm=farm,
            role=role,
            is_active=data.get("is_active") == "on",
            is_staff=data.get("is_staff") == "on" and user_is_super_admin(request.user),
        )
        user.groups.set(data.getlist("groups"))
        FazendaAcesso.objects.create(usuario=user, farm=farm, perfil=_perfil_por_role(role))
        return JsonResponse({"success": True, "id": user.id})
    except (PermissionDenied, ValidationError) as e:
        return permission_error_response(e)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)


@login_required
@require_http_methods(["GET"])
def detalhar_usuario(request, pk):
    user = _usuarios_visiveis(request.user).filter(pk=pk).first()
    if not user:
        return JsonResponse({"success": False, "error": "Usuário não encontrado."}, status=404)
    return JsonResponse(_serialize_usuario(user))


@login_required
@require_http_methods(["PUT"])
def editar_usuario(request, pk):
    try:
        ensure_super_admin_confirmation(request)
        data = _request_form_data(request)
        target = _usuarios_visiveis(request.user).filter(pk=pk).first()
        if not target:
            return JsonResponse({"success": False, "error": "Usuário não encontrado."}, status=404)

        farm = target.farm or farms_for_user(request.user).first()
        ensure_farm_permission(request.user, farm, "usuarios", "manage")

        target.username = data.get("username", target.username).strip()
        target.email = data.get("email", target.email).strip().lower()
        target.first_name = data.get("first_name", target.first_name).strip()
        target.last_name = data.get("last_name", target.last_name).strip()
        target.is_active = data.get("is_active") == "on"
        if user_is_super_admin(request.user):
            target.is_staff = data.get("is_staff") == "on"

        password = data.get("password", "")
        confirm_password = data.get("confirm_password", "")
        if password or confirm_password:
            if password != confirm_password:
                return JsonResponse({"success": False, "error": "As senhas não conferem."}, status=400)
            target.set_password(password)

        target.groups.set(data.getlist("groups"))
        target.save()
        return JsonResponse({"success": True})
    except (PermissionDenied, ValidationError) as e:
        return permission_error_response(e)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)


@login_required
@require_http_methods(["POST"])
def definir_status_usuario(request, pk, ativo):
    try:
        ensure_super_admin_confirmation(request)
        target = _usuarios_visiveis(request.user).filter(pk=pk).first()
        if not target:
            return JsonResponse({"success": False, "error": "Usuário não encontrado."}, status=404)
        farm = target.farm or farms_for_user(request.user).first()
        ensure_farm_permission(request.user, farm, "usuarios", "manage")
        target.is_active = ativo
        target.save(update_fields=["is_active"])
        return JsonResponse({"success": True})
    except (PermissionDenied, ValidationError) as e:
        return permission_error_response(e)


@login_required
@require_http_methods(["DELETE"])
def excluir_usuario(request, pk):
    try:
        ensure_super_admin_confirmation(request)
        if int(pk) == request.user.id:
            return JsonResponse({"success": False, "error": "Você não pode excluir seu próprio usuário."}, status=400)
        target = _usuarios_visiveis(request.user).filter(pk=pk).first()
        if not target:
            return JsonResponse({"success": False, "error": "Usuário não encontrado."}, status=404)
        farm = target.farm or farms_for_user(request.user).first()
        ensure_farm_permission(request.user, farm, "usuarios", "manage")
        target.delete()
        return JsonResponse({"success": True})
    except (PermissionDenied, ValidationError) as e:
        return permission_error_response(e)


@login_required
@require_http_methods(["GET"])
def listar_logs_auditoria(request):
    try:
        if user_is_super_admin(request.user) and not request.GET.get("farm_id"):
            logs = LogAcao.objects.all()
        else:
            farm = get_request_farm(request)
            if user_is_super_admin(request.user) or has_farm_permission(request.user, farm, "usuarios", "manage"):
                logs = LogAcao.objects.filter(farm=farm)
            else:
                logs = LogAcao.objects.filter(farm=farm, usuario=request.user)
            if user_is_super_admin(request.user) and request.GET.get("globais") == "1":
                logs = LogAcao.objects.filter(farm__isnull=True)
        logs = logs.select_related("usuario", "farm")[:100]
        return JsonResponse({
            "logs": [
                {
                    "id": str(log.id),
                    "data_hora": log.data_hora.isoformat(),
                    "usuario": log.usuario.email if log.usuario_id else "-",
                    "farm": log.farm.nome if log.farm_id else "Global",
                    "acao": log.acao,
                    "descricao": log.descricao,
                    "metodo": log.metodo,
                    "caminho": log.caminho,
                    "status_code": log.status_code,
                    "ip": log.ip_usuario,
                    "dados": log.dados,
                }
                for log in logs
            ]
        })
    except (PermissionDenied, ValidationError) as e:
        return permission_error_response(e)


@login_required
@require_http_methods(["GET", "POST"])
def backup_config(request):
    try:
        farm = get_request_farm(request, json.loads(request.body or "{}") if request.method == "POST" else None)
        ensure_farm_permission(request.user, farm, "usuarios", "manage")
        config, _ = BackupConfig.objects.get_or_create(farm=farm)

        if request.method == "POST":
            ensure_super_admin_confirmation(request)
            data = json.loads(request.body or "{}")
            config.ativo = bool(data.get("ativo", False))
            config.frequencia = data.get("frequencia", config.frequencia)
            config.hora_execucao = data.get("hora_execucao", config.hora_execucao)
            config.destino = data.get("destino", config.destino or "backups")
            config.manter_ultimos = int(data.get("manter_ultimos", config.manter_ultimos or 7))
            config.save()
            return JsonResponse({"success": True})

        execucoes = BackupExecucao.objects.filter(config=config)[:10]
        return JsonResponse({
            "farm_id": str(farm.id),
            "config": {
                "ativo": config.ativo,
                "frequencia": config.frequencia,
                "hora_execucao": config.hora_execucao.strftime("%H:%M"),
                "destino": config.destino,
                "manter_ultimos": config.manter_ultimos,
                "ultima_execucao_em": config.ultima_execucao_em.isoformat() if config.ultima_execucao_em else None,
            },
            "execucoes": [
                {
                    "id": str(item.id),
                    "status": item.status,
                    "arquivo": item.arquivo,
                    "mensagem": item.mensagem,
                    "iniciado_em": item.iniciado_em.isoformat(),
                    "finalizado_em": item.finalizado_em.isoformat() if item.finalizado_em else None,
                }
                for item in execucoes
            ],
        })
    except (PermissionDenied, ValidationError) as e:
        return permission_error_response(e)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)


@login_required
@require_http_methods(["POST"])
def executar_backup_manual(request):
    try:
        ensure_super_admin_confirmation(request)
        data = json.loads(request.body or "{}")
        farm = get_request_farm(request, data)
        ensure_farm_permission(request.user, farm, "usuarios", "manage")
        config, _ = BackupConfig.objects.get_or_create(farm=farm)
        execucao = executar_backup_config(config)
        return JsonResponse({"success": execucao.status == "SUCESSO", "status": execucao.status, "arquivo": execucao.arquivo, "mensagem": execucao.mensagem})
    except (PermissionDenied, ValidationError) as e:
        return permission_error_response(e)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)


@login_required
@require_http_methods(["POST", "GET"])
def logout_view(request):
    registrar_acao(
        request,
        acao="LOGOUT",
        descricao="Logout realizado.",
        farm=getattr(request.user, "farm", None),
        status_code=200,
        tabela="auth",
    )
    logout(request)
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"success": True, "message": "Logout realizado com sucesso!", "redirect_url": "/"})
    messages.success(request, "Logout realizado com sucesso!")
    return redirect("login")

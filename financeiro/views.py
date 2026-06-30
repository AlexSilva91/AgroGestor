import json

from django.core.exceptions import PermissionDenied, ValidationError
from django.forms.models import model_to_dict
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required

from core.permissions import (
    active_farm_queryset,
    ensure_farm_permission,
    ensure_super_admin_confirmation,
    get_request_farm,
    module_queryset,
    permission_error_response,
    tenant_get_or_404,
)
from gestao.models import Plantel
from rebanho.models import Animal
from .models import LancamentoFinanceiro


@login_required
@require_http_methods(["GET"])
def lista_lancamentos(request):
    lancamentos = module_queryset(
        LancamentoFinanceiro.objects.select_related("animal", "plantel", "farm"),
        request.user,
        "financeiro",
    )
    lancamentos = active_farm_queryset(lancamentos, request).order_by("-data_movimento")
    return JsonResponse([
        {
            "id": str(item.id),
            "tipo": item.tipo,
            "categoria": item.categoria,
            "valor": float(item.valor),
            "descricao": item.descricao,
            "data_movimento": item.data_movimento.strftime("%d/%m/%Y"),
            "animal": item.animal.codigo_brincos if item.animal else None,
            "plantel": item.plantel.codigo if item.plantel else None,
        }
        for item in lancamentos
    ], safe=False)


@login_required
@require_http_methods(["GET"])
def detalhar_lancamento(request, pk):
    lancamento = get_object_or_404(
        module_queryset(LancamentoFinanceiro.objects.all(), request.user, "financeiro"),
        pk=pk,
    )
    data = model_to_dict(lancamento)
    data["id"] = str(lancamento.id)
    data["data_movimento"] = lancamento.data_movimento.strftime("%Y-%m-%d")
    return JsonResponse(data)


@login_required
@require_http_methods(["POST"])
def criar_lancamento(request):
    try:
        ensure_super_admin_confirmation(request)
        payload = json.loads(request.body or "{}")
        farm = get_request_farm(request, payload)
        ensure_farm_permission(request.user, farm, "financeiro", "create")
        lancamento = LancamentoFinanceiro.objects.create(
            farm=farm,
            tipo=payload.get("tipo"),
            categoria=payload.get("categoria"),
            valor=payload.get("valor"),
            descricao=payload.get("descricao"),
            data_movimento=parse_date(payload.get("data_movimento")),
            animal=Animal.objects.filter(id=payload.get("animal"), farm=farm).first(),
            plantel=Plantel.objects.filter(id=payload.get("plantel"), farm=farm).first(),
        )
        return JsonResponse({"success": True, "id": str(lancamento.id)})
    except (PermissionDenied, ValidationError) as e:
        return permission_error_response(e)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)


@login_required
@require_http_methods(["PUT"])
def editar_lancamento(request, pk):
    try:
        ensure_super_admin_confirmation(request)
        payload = json.loads(request.body or "{}")
        lancamento = tenant_get_or_404(LancamentoFinanceiro.objects.all(), request.user, pk=pk)
        ensure_farm_permission(request.user, lancamento.farm, "financeiro", "update")
        lancamento.tipo = payload.get("tipo", lancamento.tipo)
        lancamento.categoria = payload.get("categoria", lancamento.categoria)
        lancamento.valor = payload.get("valor", lancamento.valor)
        lancamento.descricao = payload.get("descricao", lancamento.descricao)
        lancamento.data_movimento = parse_date(payload.get("data_movimento")) or lancamento.data_movimento
        lancamento.animal = Animal.objects.filter(id=payload.get("animal"), farm=lancamento.farm).first()
        lancamento.plantel = Plantel.objects.filter(id=payload.get("plantel"), farm=lancamento.farm).first()
        lancamento.save()
        return JsonResponse({"success": True})
    except (PermissionDenied, ValidationError) as e:
        return permission_error_response(e)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)


@login_required
@require_http_methods(["DELETE"])
def excluir_lancamento(request, pk):
    try:
        ensure_super_admin_confirmation(request)
        lancamento = tenant_get_or_404(LancamentoFinanceiro.objects.all(), request.user, pk=pk)
        ensure_farm_permission(request.user, lancamento.farm, "financeiro", "delete")
        lancamento.delete()
        return JsonResponse({"success": True})
    except (PermissionDenied, ValidationError) as e:
        return permission_error_response(e)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)

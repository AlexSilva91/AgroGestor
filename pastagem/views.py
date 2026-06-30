import json
import uuid

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.forms.models import model_to_dict
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
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
)
from rebanho.models import Animal
from .models import MovimentacaoAnimal, Pastagem


@login_required
@require_http_methods(["GET"])
def listar_pastagens(request):
    pastagens = active_farm_queryset(
        module_queryset(Pastagem.objects.select_related("farm"), request.user, "pastagem"),
        request,
    ).order_by("-criado_em")
    return JsonResponse([
        {
            "id": str(item.id),
            "farm_id": str(item.farm_id) if item.farm_id else None,
            "nome": item.nome,
            "area": float(item.area) if item.area else None,
            "capacidade_suporte": item.capacidade_suporte,
            "ativo": item.ativo,
            "criado_em": item.criado_em.strftime("%Y-%m-%d %H:%M"),
        }
        for item in pastagens
    ], safe=False)


@login_required
@require_http_methods(["GET"])
def detalhar_pastagem(request, pk):
    pastagem = get_object_or_404(module_queryset(Pastagem.objects.all(), request.user, "pastagem"), pk=pk)
    data = model_to_dict(pastagem)
    data["id"] = str(pastagem.id)
    return JsonResponse(data)


@login_required
@require_http_methods(["POST"])
def criar_pastagem(request):
    try:
        ensure_super_admin_confirmation(request)
        payload = json.loads(request.body or "{}")
        farm = get_request_farm(request, payload)
        ensure_farm_permission(request.user, farm, "pastagem", "create")
        pastagem = Pastagem.objects.create(
            id=uuid.uuid4(),
            farm=farm,
            nome=payload.get("nome"),
            area=payload.get("area"),
            capacidade_suporte=payload.get("capacidade_suporte"),
            ativo=payload.get("ativo", True),
        )
        return JsonResponse({"success": True, "id": str(pastagem.id)})
    except (PermissionDenied, ValidationError) as e:
        return permission_error_response(e)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)


@login_required
@require_http_methods(["PUT"])
def editar_pastagem(request, pk):
    try:
        ensure_super_admin_confirmation(request)
        payload = json.loads(request.body or "{}")
        pastagem = tenant_get_or_404(Pastagem.objects.all(), request.user, pk=pk)
        ensure_farm_permission(request.user, pastagem.farm, "pastagem", "update")
        for field in ("nome", "area", "capacidade_suporte", "ativo"):
            if field in payload:
                setattr(pastagem, field, payload[field])
        pastagem.save()
        return JsonResponse({"success": True})
    except (PermissionDenied, ValidationError) as e:
        return permission_error_response(e)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)


@login_required
@require_http_methods(["DELETE"])
def excluir_pastagem(request, pk):
    try:
        ensure_super_admin_confirmation(request)
        pastagem = tenant_get_or_404(Pastagem.objects.all(), request.user, pk=pk)
        ensure_farm_permission(request.user, pastagem.farm, "pastagem", "delete")
        pastagem.delete()
        return JsonResponse({"success": True})
    except (PermissionDenied, ValidationError) as e:
        return permission_error_response(e)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)


@login_required
@require_http_methods(["GET"])
def listar_movimentacoes(request):
    movs = active_farm_queryset(
        module_queryset(MovimentacaoAnimal.objects.select_related("animal", "pastagem"), request.user, "pastagem", farm_field="animal__farm"),
        request,
        farm_field="animal__farm",
    ).order_by("-criado_em")
    return JsonResponse([
        {
            "id": str(item.id),
            "animal_id": str(item.animal_id) if item.animal_id else None,
            "animal_codigo": item.animal.codigo_brincos if item.animal else "N/A",
            "pastagem_id": str(item.pastagem_id) if item.pastagem_id else None,
            "pastagem_nome": item.pastagem.nome if item.pastagem else "N/A",
            "data_entrada": item.data_entrada.strftime("%d/%m/%Y") if item.data_entrada else None,
            "data_saida": item.data_saida.strftime("%d/%m/%Y") if item.data_saida else None,
            "observacoes": item.observacoes,
            "criado_em": item.criado_em.strftime("%d/%m/%Y %H:%M"),
        }
        for item in movs
    ], safe=False)


@login_required
@require_http_methods(["GET"])
def detalhar_movimentacao(request, pk):
    mov = get_object_or_404(module_queryset(MovimentacaoAnimal.objects.all(), request.user, "pastagem", farm_field="animal__farm"), pk=pk)
    data = model_to_dict(mov)
    data["id"] = str(mov.id)
    data["data_entrada"] = mov.data_entrada.strftime("%Y-%m-%d") if mov.data_entrada else None
    data["data_saida"] = mov.data_saida.strftime("%Y-%m-%d") if mov.data_saida else None
    return JsonResponse(data)


@login_required
@require_http_methods(["POST"])
def criar_movimentacao(request):
    try:
        ensure_super_admin_confirmation(request)
        payload = json.loads(request.body or "{}")
        farm = get_request_farm(request, payload)
        ensure_farm_permission(request.user, farm, "pastagem", "create")
        mov = MovimentacaoAnimal.objects.create(
            id=uuid.uuid4(),
            animal=get_object_or_404(Animal, pk=payload.get("animal"), farm=farm),
            pastagem=get_object_or_404(Pastagem, pk=payload.get("pastagem"), farm=farm),
            data_entrada=parse_date(payload.get("data_entrada")) or None,
            data_saida=parse_date(payload.get("data_saida")) or None,
            observacoes=payload.get("observacoes"),
        )
        return JsonResponse({"success": True, "id": str(mov.id)})
    except (PermissionDenied, ValidationError) as e:
        return permission_error_response(e)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)


@login_required
@require_http_methods(["PUT"])
def editar_movimentacao(request, pk):
    try:
        ensure_super_admin_confirmation(request)
        payload = json.loads(request.body or "{}")
        mov = get_object_or_404(module_queryset(MovimentacaoAnimal.objects.all(), request.user, "pastagem", farm_field="animal__farm"), pk=pk)
        farm = mov.animal.farm if mov.animal else mov.pastagem.farm
        ensure_farm_permission(request.user, farm, "pastagem", "update")
        if payload.get("animal"):
            mov.animal = get_object_or_404(Animal, pk=payload.get("animal"), farm=farm)
        if payload.get("pastagem"):
            mov.pastagem = get_object_or_404(Pastagem, pk=payload.get("pastagem"), farm=farm)
        mov.data_entrada = parse_date(payload.get("data_entrada")) or mov.data_entrada
        mov.data_saida = parse_date(payload.get("data_saida")) or mov.data_saida
        mov.observacoes = payload.get("observacoes", mov.observacoes)
        mov.save()
        return JsonResponse({"success": True})
    except (PermissionDenied, ValidationError) as e:
        return permission_error_response(e)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)


@login_required
@require_http_methods(["DELETE"])
def excluir_movimentacao(request, pk):
    try:
        ensure_super_admin_confirmation(request)
        mov = get_object_or_404(module_queryset(MovimentacaoAnimal.objects.all(), request.user, "pastagem", farm_field="animal__farm"), pk=pk)
        farm = mov.animal.farm if mov.animal else mov.pastagem.farm
        ensure_farm_permission(request.user, farm, "pastagem", "delete")
        mov.delete()
        return JsonResponse({"success": True})
    except (PermissionDenied, ValidationError) as e:
        return permission_error_response(e)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)

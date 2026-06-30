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
from .models import Animal, HistoricoAnimal, Rebanho


@login_required
@require_http_methods(["GET"])
def listar_rebanhos(request):
    rebanhos = active_farm_queryset(module_queryset(Rebanho.objects.select_related("farm"), request.user, "rebanho"), request).order_by("-criado_em")
    return JsonResponse([
        {
            "id": str(item.id),
            "farm_id": str(item.farm_id) if item.farm_id else None,
            "nome_lote": item.nome_lote,
            "capacidade": item.capacidade,
            "ativo": item.ativo,
            "criado_em": item.criado_em.strftime("%Y-%m-%d %H:%M"),
        }
        for item in rebanhos
    ], safe=False)


@login_required
@require_http_methods(["GET"])
def detalhar_rebanho(request, pk):
    rebanho = get_object_or_404(module_queryset(Rebanho.objects.all(), request.user, "rebanho"), pk=pk)
    data = model_to_dict(rebanho)
    data["id"] = str(rebanho.id)
    return JsonResponse(data)


@login_required
@require_http_methods(["POST"])
def criar_rebanho(request):
    try:
        ensure_super_admin_confirmation(request)
        payload = json.loads(request.body or "{}")
        farm = get_request_farm(request, payload)
        ensure_farm_permission(request.user, farm, "rebanho", "create")
        rebanho = Rebanho.objects.create(id=uuid.uuid4(), farm=farm, nome_lote=payload.get("nome_lote"), capacidade=payload.get("capacidade"), ativo=payload.get("ativo", True))
        return JsonResponse({"success": True, "id": str(rebanho.id)})
    except (PermissionDenied, ValidationError) as e:
        return permission_error_response(e)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)


@login_required
@require_http_methods(["PUT"])
def editar_rebanho(request, pk):
    try:
        ensure_super_admin_confirmation(request)
        payload = json.loads(request.body or "{}")
        rebanho = tenant_get_or_404(Rebanho.objects.all(), request.user, pk=pk)
        ensure_farm_permission(request.user, rebanho.farm, "rebanho", "update")
        for field in ("nome_lote", "capacidade", "ativo"):
            if field in payload:
                setattr(rebanho, field, payload[field])
        rebanho.save()
        return JsonResponse({"success": True})
    except (PermissionDenied, ValidationError) as e:
        return permission_error_response(e)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)


@login_required
@require_http_methods(["DELETE"])
def excluir_rebanho(request, pk):
    try:
        ensure_super_admin_confirmation(request)
        rebanho = tenant_get_or_404(Rebanho.objects.all(), request.user, pk=pk)
        ensure_farm_permission(request.user, rebanho.farm, "rebanho", "delete")
        rebanho.delete()
        return JsonResponse({"success": True})
    except (PermissionDenied, ValidationError) as e:
        return permission_error_response(e)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)


@login_required
@require_http_methods(["GET"])
def listar_animais(request):
    animais = active_farm_queryset(module_queryset(Animal.objects.select_related("farm", "rebanho"), request.user, "rebanho"), request).order_by("-criado_em")
    return JsonResponse([
        {
            "id": str(item.id),
            "farm_id": str(item.farm_id) if item.farm_id else None,
            "rebanho_id": str(item.rebanho_id) if item.rebanho_id else None,
            "codigo_brincos": item.codigo_brincos,
            "sexo": item.sexo,
            "nascimento": item.nascimento.strftime("%d/%m/%Y"),
            "peso_atual": float(item.peso_atual) if item.peso_atual else None,
            "raca": item.raca,
            "status": item.status,
        }
        for item in animais
    ], safe=False)


@login_required
@require_http_methods(["GET"])
def detalhar_animal(request, pk):
    animal = get_object_or_404(module_queryset(Animal.objects.all(), request.user, "rebanho"), pk=pk)
    data = model_to_dict(animal)
    data["id"] = str(animal.id)
    data["nascimento"] = animal.nascimento.strftime("%Y-%m-%d")
    return JsonResponse(data)


@login_required
@require_http_methods(["POST"])
def criar_animal(request):
    try:
        ensure_super_admin_confirmation(request)
        payload = json.loads(request.body or "{}")
        farm = get_request_farm(request, payload)
        ensure_farm_permission(request.user, farm, "rebanho", "create")
        rebanho = Rebanho.objects.filter(id=payload.get("rebanho"), farm=farm).first() if payload.get("rebanho") else None
        animal = Animal.objects.create(
            id=uuid.uuid4(),
            farm=farm,
            rebanho=rebanho,
            codigo_brincos=payload.get("codigo_brincos"),
            sexo=payload.get("sexo"),
            nascimento=parse_date(payload.get("nascimento")),
            peso_atual=payload.get("peso_atual"),
            raca=payload.get("raca"),
            status=payload.get("status", "ativo"),
        )
        return JsonResponse({"success": True, "id": str(animal.id)})
    except (PermissionDenied, ValidationError) as e:
        return permission_error_response(e)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)


@login_required
@require_http_methods(["PUT"])
def editar_animal(request, pk):
    try:
        ensure_super_admin_confirmation(request)
        payload = json.loads(request.body or "{}")
        animal = tenant_get_or_404(Animal.objects.all(), request.user, pk=pk)
        ensure_farm_permission(request.user, animal.farm, "rebanho", "update")
        if payload.get("rebanho"):
            animal.rebanho = get_object_or_404(Rebanho, id=payload.get("rebanho"), farm=animal.farm)
        for field in ("codigo_brincos", "sexo", "peso_atual", "raca", "status"):
            if field in payload:
                setattr(animal, field, payload[field])
        animal.nascimento = parse_date(payload.get("nascimento")) or animal.nascimento
        animal.save()
        return JsonResponse({"success": True})
    except (PermissionDenied, ValidationError) as e:
        return permission_error_response(e)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)


@login_required
@require_http_methods(["DELETE"])
def excluir_animal(request, pk):
    try:
        ensure_super_admin_confirmation(request)
        animal = tenant_get_or_404(Animal.objects.all(), request.user, pk=pk)
        ensure_farm_permission(request.user, animal.farm, "rebanho", "delete")
        animal.delete()
        return JsonResponse({"success": True})
    except (PermissionDenied, ValidationError) as e:
        return permission_error_response(e)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)


@login_required
@require_http_methods(["GET"])
def listar_historicos(request):
    historicos = active_farm_queryset(module_queryset(HistoricoAnimal.objects.select_related("animal", "farm"), request.user, "rebanho"), request).order_by("-data_evento")
    return JsonResponse([
        {
            "id": str(item.id),
            "farm_id": str(item.farm_id),
            "animal_id": str(item.animal_id),
            "tipo_evento": item.tipo_evento,
            "valor": item.valor,
            "descricao": item.descricao,
            "data_evento": item.data_evento.strftime("%Y-%m-%d"),
        }
        for item in historicos
    ], safe=False)


@login_required
@require_http_methods(["GET"])
def detalhar_historico(request, pk):
    historico = get_object_or_404(module_queryset(HistoricoAnimal.objects.all(), request.user, "rebanho"), pk=pk)
    data = model_to_dict(historico)
    data["id"] = str(historico.id)
    data["data_evento"] = historico.data_evento.strftime("%Y-%m-%d")
    return JsonResponse(data)


@login_required
@require_http_methods(["POST"])
def criar_historico(request):
    try:
        ensure_super_admin_confirmation(request)
        payload = json.loads(request.body or "{}")
        farm = get_request_farm(request, payload)
        ensure_farm_permission(request.user, farm, "rebanho", "create")
        historico = HistoricoAnimal.objects.create(
            id=uuid.uuid4(),
            farm=farm,
            animal=get_object_or_404(Animal, id=payload.get("animal"), farm=farm),
            tipo_evento=payload.get("tipo_evento"),
            valor=payload.get("valor"),
            descricao=payload.get("descricao"),
            data_evento=parse_date(payload.get("data_evento")),
        )
        return JsonResponse({"success": True, "id": str(historico.id)})
    except (PermissionDenied, ValidationError) as e:
        return permission_error_response(e)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)


@login_required
@require_http_methods(["PUT"])
def editar_historico(request, pk):
    try:
        ensure_super_admin_confirmation(request)
        payload = json.loads(request.body or "{}")
        historico = tenant_get_or_404(HistoricoAnimal.objects.all(), request.user, pk=pk)
        ensure_farm_permission(request.user, historico.farm, "rebanho", "update")
        if payload.get("animal"):
            historico.animal = get_object_or_404(Animal, id=payload.get("animal"), farm=historico.farm)
        for field in ("tipo_evento", "valor", "descricao"):
            if field in payload:
                setattr(historico, field, payload[field])
        historico.data_evento = parse_date(payload.get("data_evento")) or historico.data_evento
        historico.save()
        return JsonResponse({"success": True})
    except (PermissionDenied, ValidationError) as e:
        return permission_error_response(e)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)


@login_required
@require_http_methods(["DELETE"])
def excluir_historico(request, pk):
    try:
        ensure_super_admin_confirmation(request)
        historico = tenant_get_or_404(HistoricoAnimal.objects.all(), request.user, pk=pk)
        ensure_farm_permission(request.user, historico.farm, "rebanho", "delete")
        historico.delete()
        return JsonResponse({"success": True})
    except (PermissionDenied, ValidationError) as e:
        return permission_error_response(e)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.forms.models import model_to_dict
from core.models import Fazenda
from .models import Pastagem, MovimentacaoAnimal
from rebanho.models import Animal
import json
import uuid
from django.utils.dateparse import parse_date

# =======================
# Pastagem CRUD
# =======================
@login_required
@require_http_methods(["GET"])
def listar_pastagens(request):
    pastagens = Pastagem.objects.select_related("farm").order_by("-criado_em")
    data = [
        {
            "id": str(p.id),
            "farm_id": getattr(p.farm, 'id', None),
            "nome": p.nome,
            "area": float(p.area) if p.area else None,
            "capacidade_suporte": p.capacidade_suporte,
            "ativo": p.ativo,
            "criado_em": p.criado_em.strftime("%Y-%m-%d %H:%M"),
        }
        for p in pastagens
    ]
    return JsonResponse(data, safe=False)


@login_required
@require_http_methods(["GET"])
def detalhar_pastagem(request, pk):
    pastagem = get_object_or_404(Pastagem, pk=pk)
    data = model_to_dict(pastagem)
    data["id"] = str(pastagem.id)
    return JsonResponse(data)


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def criar_pastagem(request):
    try:
        payload = json.loads(request.body)
        farm = Fazenda.objects.first()
        pastagem = Pastagem.objects.create(
            id=uuid.uuid4(),
            farm=farm,
            nome=payload.get("nome"),
            area=payload.get("area"),
            capacidade_suporte=payload.get("capacidade_suporte"),
            ativo=payload.get("ativo", True)
        )
        return JsonResponse({"success": True, "id": str(pastagem.id)})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)


@login_required
@csrf_exempt
@require_http_methods(["PUT"])
def editar_pastagem(request, pk):
    try:
        payload = json.loads(request.body)
        pastagem = get_object_or_404(Pastagem, pk=pk)

        pastagem.nome = payload.get("nome", pastagem.nome)
        pastagem.area = payload.get("area", pastagem.area)
        pastagem.capacidade_suporte = payload.get("capacidade_suporte", pastagem.capacidade_suporte)
        pastagem.ativo = payload.get("ativo", pastagem.ativo)
        pastagem.save()

        return JsonResponse({"success": True})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)


@login_required
@csrf_exempt
@require_http_methods(["DELETE"])
def excluir_pastagem(request, pk):
    try:
        pastagem = get_object_or_404(Pastagem, pk=pk)
        pastagem.delete()
        return JsonResponse({"success": True})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)


# =======================
# MovimentacaoAnimal CRUD
# =======================
@login_required
@require_http_methods(["GET"])
def listar_movimentacoes(request):
    movs = MovimentacaoAnimal.objects.select_related("animal", "pastagem").order_by("-criado_em")
    data = [
        {
            "id": str(m.id),
            "animal_id": getattr(m.animal, 'id', None),
            "animal_codigo": getattr(m.animal, 'codigo_brincos', 'N/A'),
            "pastagem_id": getattr(m.pastagem, 'id', None),
            "pastagem_nome": getattr(m.pastagem, 'nome', 'N/A'), 
            "data_entrada": m.data_entrada.strftime("%d/%m/%Y") if m.data_entrada else None,
            "data_saida": m.data_saida.strftime("%d/%m/%Y") if m.data_saida else None,
            "observacoes": m.observacoes, 
            "criado_em": m.criado_em.strftime("%d/%m/%Y %H:%M"),
        }
        for m in movs
    ]
    return JsonResponse(data, safe=False)

@login_required
@require_http_methods(["GET"])
def detalhar_movimentacao(request, pk):
    mov = get_object_or_404(MovimentacaoAnimal, pk=pk)
    data = model_to_dict(mov)
    data["id"] = str(mov.id)
    data["data_entrada"] = mov.data_entrada.strftime("%Y-%m-%d") if mov.data_entrada else None
    data["data_saida"] = mov.data_saida.strftime("%Y-%m-%d") if mov.data_saida else None
    return JsonResponse(data)


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def criar_movimentacao(request):
    try:
        payload = json.loads(request.body)
        animal = get_object_or_404(Animal, pk=payload.get("animal"))
        pastagem = get_object_or_404(Pastagem, pk=payload.get("pastagem"))

        mov = MovimentacaoAnimal.objects.create(
            id=uuid.uuid4(),
            animal=animal,
            pastagem=pastagem,
            data_entrada=parse_date(payload.get("data_entrada")) or None,
            data_saida=parse_date(payload.get("data_saida")) or None
        )
        return JsonResponse({"success": True, "id": str(mov.id)})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)


@login_required
@csrf_exempt
@require_http_methods(["PUT"])
def editar_movimentacao(request, pk):
    try:
        payload = json.loads(request.body)
        mov = get_object_or_404(MovimentacaoAnimal, pk=pk)

        if payload.get("animal"):
            mov.animal = get_object_or_404(Animal, pk=payload.get("animal"))
        if payload.get("pastagem"):
            mov.pastagem = get_object_or_404(Pastagem, pk=payload.get("pastagem"))

        mov.data_entrada = parse_date(payload.get("data_entrada")) or mov.data_entrada
        mov.data_saida = parse_date(payload.get("data_saida")) or mov.data_saida
        mov.save()
        return JsonResponse({"success": True})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)


@login_required
@csrf_exempt
@require_http_methods(["DELETE"])
def excluir_movimentacao(request, pk):
    try:
        mov = get_object_or_404(MovimentacaoAnimal, pk=pk)
        mov.delete()
        return JsonResponse({"success": True})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)

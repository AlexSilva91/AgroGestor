from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_date
from django.forms.models import model_to_dict
from core.models import Fazenda
from .models import Rebanho, Animal, HistoricoAnimal
import json
import uuid

'''
    VIEWS REBANHO
'''
@login_required
@require_http_methods(["GET"])
def listar_rebanhos(request):
    rebanhos = Rebanho.objects.select_related("farm").order_by("-criado_em")
    data = [
        {
            "id": str(r.id),
            "farm_id": r.farm.id,
            "nome_lote": r.nome_lote,
            "capacidade": r.capacidade,
            "ativo": r.ativo,
            "criado_em": r.criado_em.strftime("%Y-%m-%d %H:%M"),
        }
        for r in rebanhos
    ]
    return JsonResponse(data, safe=False)


@login_required
@require_http_methods(["GET"])
def detalhar_rebanho(request, pk):
    rebanho = get_object_or_404(Rebanho, pk=pk)
    data = model_to_dict(rebanho)
    data["id"] = str(rebanho.id)
    return JsonResponse(data)


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def criar_rebanho(request):
    try:
        payload = json.loads(request.body)
        farm = Fazenda.objects.first()
        rebanho = Rebanho.objects.create(
            id=uuid.uuid4(),
            farm=farm,
            nome_lote=payload.get("nome_lote"),
            capacidade=payload.get("capacidade"),
            ativo=payload.get("ativo", True),
        )
        return JsonResponse({"success": True, "id": str(rebanho.id)})
    except Exception as e:
        print(e)
        return JsonResponse({"success": False, "error": str(e)}, status=400)


@login_required
@csrf_exempt
@require_http_methods(["PUT"])
def editar_rebanho(request, pk):
    try:
        payload = json.loads(request.body)
        rebanho = get_object_or_404(Rebanho, pk=pk)

        rebanho.nome_lote = payload.get("nome_lote", rebanho.nome_lote)
        rebanho.capacidade = payload.get("capacidade", rebanho.capacidade)
        rebanho.ativo = payload.get("ativo", rebanho.ativo)
        rebanho.save()

        return JsonResponse({"success": True})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)


@login_required
@csrf_exempt
@require_http_methods(["DELETE"])
def excluir_rebanho(request, pk):
    try:
        rebanho = get_object_or_404(Rebanho, pk=pk)
        rebanho.delete()
        return JsonResponse({"success": True})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)


'''
    VIEWS ANIMAL
'''
@login_required
@require_http_methods(["GET"])
def listar_animais(request):
    animais = Animal.objects.select_related("farm", "rebanho").order_by("-criado_em")
    data = [
        {
            "id": str(a.id),
            "farm_id": getattr(a.farm, 'id', None),
            "rebanho_id": getattr(a.rebanho, 'id', None),
            "codigo_brincos": a.codigo_brincos,
            "sexo": a.sexo,
            "nascimento": a.nascimento.strftime("%d/%m/%Y"),
            "peso_atual": float(a.peso_atual) if a.peso_atual else None,
            "raca": a.raca,
            "status": a.status,
        }
        for a in animais
    ]

    return JsonResponse(data, safe=False)


@login_required
@require_http_methods(["GET"])
def detalhar_animal(request, pk):
    animal = get_object_or_404(Animal, pk=pk)
    data = model_to_dict(animal)
    data["id"] = str(animal.id)
    data["nascimento"] = animal.nascimento.strftime("%Y-%m-%d")
    return JsonResponse(data)


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def criar_animal(request):
    try:
        payload = json.loads(request.body)
        farm = Fazenda.objects.first()
        rebanho_id = payload.get("rebanho")
        rebanho = Rebanho.objects.filter(id=rebanho_id).first() if rebanho_id else None

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
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)


@login_required
@csrf_exempt
@require_http_methods(["PUT"])
def editar_animal(request, pk):
    try:
        payload = json.loads(request.body)
        animal = get_object_or_404(Animal, pk=pk)

        if payload.get("rebanho"):
            animal.rebanho = get_object_or_404(Rebanho, id=payload.get("rebanho"))

        animal.codigo_brincos = payload.get("codigo_brincos", animal.codigo_brincos)
        animal.sexo = payload.get("sexo", animal.sexo)
        animal.nascimento = parse_date(payload.get("nascimento")) or animal.nascimento
        animal.peso_atual = payload.get("peso_atual", animal.peso_atual)
        animal.raca = payload.get("raca", animal.raca)
        animal.status = payload.get("status", animal.status)
        animal.save()

        return JsonResponse({"success": True})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)


@login_required
@csrf_exempt
@require_http_methods(["DELETE"])
def excluir_animal(request, pk):
    try:
        animal = get_object_or_404(Animal, pk=pk)
        animal.delete()
        return JsonResponse({"success": True})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)

'''
    VIEWS HITÓRICO ANIMAL
'''
@login_required
@require_http_methods(["GET"])
def listar_historicos(request):
    historicos = HistoricoAnimal.objects.select_related("animal", "farm").order_by("-data_evento")
    data = [
        {
            "id": str(h.id),
            "farm_id": h.farm.id,
            "animal_id": h.animal.id,
            "tipo_evento": h.tipo_evento,
            "valor": h.valor,
            "descricao": h.descricao,
            "data_evento": h.data_evento.strftime("%Y-%m-%d"),
        }
        for h in historicos
    ]
    return JsonResponse(data, safe=False)


@login_required
@require_http_methods(["GET"])
def detalhar_historico(request, pk):
    historico = get_object_or_404(HistoricoAnimal, pk=pk)
    data = model_to_dict(historico)
    data["id"] = str(historico.id)
    data["data_evento"] = historico.data_evento.strftime("%Y-%m-%d")
    return JsonResponse(data)


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def criar_historico(request):
    try:
        payload = json.loads(request.body)
        farm = Fazenda.objects.first()
        animal = get_object_or_404(Animal, id=payload.get("animal"))

        historico = HistoricoAnimal.objects.create(
            id=uuid.uuid4(),
            farm=farm,
            animal=animal,
            tipo_evento=payload.get("tipo_evento"),
            valor=payload.get("valor"),
            descricao=payload.get("descricao"),
            data_evento=parse_date(payload.get("data_evento")),
        )
        return JsonResponse({"success": True, "id": str(historico.id)})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)


@login_required
@csrf_exempt
@require_http_methods(["PUT"])
def editar_historico(request, pk):
    try:
        payload = json.loads(request.body)
        historico = get_object_or_404(HistoricoAnimal, pk=pk)

        if payload.get("animal"):
            historico.animal = get_object_or_404(Animal, id=payload.get("animal"))

        historico.tipo_evento = payload.get("tipo_evento", historico.tipo_evento)
        historico.valor = payload.get("valor", historico.valor)
        historico.descricao = payload.get("descricao", historico.descricao)
        historico.data_evento = parse_date(payload.get("data_evento")) or historico.data_evento
        historico.save()

        return JsonResponse({"success": True})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)


@login_required
@csrf_exempt
@require_http_methods(["DELETE"])
def excluir_historico(request, pk):
    try:
        historico = get_object_or_404(HistoricoAnimal, pk=pk)
        historico.delete()
        return JsonResponse({"success": True})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)



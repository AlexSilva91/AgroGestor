from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils.dateparse import parse_date
from django.shortcuts import get_object_or_404
from django.forms.models import model_to_dict
from .models import LancamentoFinanceiro
from core.models import Fazenda
from rebanho.models import Animal
import json


@login_required
@require_http_methods(["GET"])
def lista_lancamentos(request):
    """Retorna todos os lançamentos em formato JSON."""
    lancamentos = LancamentoFinanceiro.objects.select_related('animal').order_by('-data_movimento')
   
    data = [
        {
            "id": str(l.id),
            "tipo": l.tipo,
            "categoria": l.categoria,
            "valor": float(l.valor),
            "descricao": l.descricao,
            "data_movimento": l.data_movimento.strftime('%d/%m/%Y'),
            "animal": l.animal.codigo if l.animal else None,
        }
        for l in lancamentos
    ]
    return JsonResponse(data, safe=False)


@login_required
@require_http_methods(["GET"])
def detalhar_lancamento(request, pk):
    """Retorna os dados de um único lançamento."""
    lancamento = get_object_or_404(LancamentoFinanceiro, pk=pk)
    data = model_to_dict(lancamento)
    data['data_movimento'] = lancamento.data_movimento.strftime('%Y-%m-%d')
    return JsonResponse(data)


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def criar_lancamento(request):
    """Cria um lançamento via JSON."""
    try:
        payload = json.loads(request.body)
        farm = Fazenda.objects.first()  # Pega a fazenda padrão (ajuste se necessário)

        lancamento = LancamentoFinanceiro.objects.create(
            farm=farm,
            tipo=payload.get('tipo'),
            categoria=payload.get('categoria'),
            valor=payload.get('valor'),
            descricao=payload.get('descricao'),
            data_movimento=parse_date(payload.get('data_movimento')),
            animal=Animal.objects.filter(id=payload.get('animal')).first()
        )

        return JsonResponse({'success': True, 'id': str(lancamento.id)})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@csrf_exempt
@require_http_methods(["PUT"])
def editar_lancamento(request, pk):
    """Atualiza um lançamento existente."""
    try:
        payload = json.loads(request.body)
        lancamento = get_object_or_404(LancamentoFinanceiro, pk=pk)

        lancamento.tipo = payload.get('tipo')
        lancamento.categoria = payload.get('categoria')
        lancamento.valor = payload.get('valor')
        lancamento.descricao = payload.get('descricao')
        lancamento.data_movimento = parse_date(payload.get('data_movimento'))
        lancamento.animal = Animal.objects.filter(id=payload.get('animal')).first()
        lancamento.save()

        return JsonResponse({'success': True})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@csrf_exempt
@require_http_methods(["DELETE"])
def excluir_lancamento(request, pk):
    """Remove um lançamento financeiro."""
    try:
        lancamento = get_object_or_404(LancamentoFinanceiro, pk=pk)
        lancamento.delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

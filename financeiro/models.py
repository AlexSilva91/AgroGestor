from django.db import models
from core.models import Fazenda
from rebanho.models import Animal
import uuid

class LancamentoFinanceiro(models.Model):
    TIPO_CHOICES = [("CUSTO", "Custo"), ("RECEITA", "Receita")]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    farm = models.ForeignKey(Fazenda, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    categoria = models.CharField(max_length=50)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    descricao = models.TextField(blank=True, null=True)
    data_movimento = models.DateField()
    animal = models.ForeignKey(Animal, on_delete=models.SET_NULL, null=True, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

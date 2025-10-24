from django.db import models
from core.models import Fazenda
from rebanho.models import Animal
import uuid

class Pastagem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    farm = models.ForeignKey(Fazenda, on_delete=models.CASCADE, null=True, blank=True)
    nome = models.CharField(max_length=100)
    area = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    capacidade_suporte = models.IntegerField(null=True, blank=True)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)


class MovimentacaoAnimal(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    animal = models.ForeignKey(Animal, on_delete=models.CASCADE, null=True, blank=True)
    pastagem = models.ForeignKey(Pastagem, on_delete=models.CASCADE, null=True, blank=True)
    data_entrada = models.DateField(auto_now_add=True)
    data_saida = models.DateField(null=True, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

from django.db import models
from core.models import Fazenda
import uuid

class Rebanho(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    farm = models.ForeignKey(Fazenda, on_delete=models.CASCADE, null=True, blank=True)
    nome_lote = models.CharField(max_length=100)
    capacidade = models.IntegerField(null=True, blank=True)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)


class Animal(models.Model):
    SEXO_CHOICES = [("M", "Macho"), ("F", "Fêmea")]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    farm = models.ForeignKey(Fazenda, on_delete=models.CASCADE,  null=True, blank=True)
    rebanho = models.ForeignKey(Rebanho, on_delete=models.CASCADE, related_name="animais",  null=True, blank=True)
    codigo_brincos = models.CharField(max_length=50, unique=True)
    sexo = models.CharField(max_length=1, choices=SEXO_CHOICES)
    nascimento = models.DateField()
    peso_atual = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    raca = models.CharField(max_length=50, null=True, blank=True)
    status = models.CharField(max_length=20, default="ativo")
    criado_em = models.DateTimeField(auto_now_add=True)


class HistoricoAnimal(models.Model):
    EVENTO_CHOICES = [
        ("PESO", "Peso"),
        ("VACINA", "Vacina"),
        ("MOV", "Movimentação"),
        ("REPROD", "Reprodução"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    farm = models.ForeignKey(Fazenda, on_delete=models.CASCADE)
    animal = models.ForeignKey(Animal, on_delete=models.CASCADE, related_name="historico")
    tipo_evento = models.CharField(max_length=20, choices=EVENTO_CHOICES)
    valor = models.CharField(max_length=100, blank=True, null=True)
    descricao = models.TextField(blank=True, null=True)
    data_evento = models.DateField()
    criado_em = models.DateTimeField(auto_now_add=True)

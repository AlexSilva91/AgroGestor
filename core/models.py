from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid

class Fazenda(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nome = models.CharField(max_length=100)
    localizacao = models.CharField(max_length=255, blank=True, null=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nome


class Usuario(AbstractUser):
    ROLE_CHOICES = [
        ("ADMIN", "Administrador"),
        ("FAZENDEIRO", "Fazendeiro"),
        ("FUNCIONARIO", "Funcionário"),
        ("VETERINARIO", "Veterinário"),
    ]
    farm = models.ForeignKey(Fazenda, on_delete=models.CASCADE, null=True, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="FUNCIONARIO")
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.username} ({self.role})"

class LogAcao(models.Model):
    ACOES = [
        ("CREATE", "Criação"),
        ("UPDATE", "Atualização"),
        ("DELETE", "Remoção"),
        ("LOGIN", "Login"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    farm = models.ForeignKey(Fazenda, on_delete=models.CASCADE)
    usuario = models.ForeignKey("Usuario", on_delete=models.SET_NULL, null=True)
    acao = models.CharField(max_length=20, choices=ACOES)
    tabela_afetada = models.CharField(max_length=50)
    registro_id = models.UUIDField(null=True, blank=True)
    descricao = models.TextField(blank=True, null=True)
    data_hora = models.DateTimeField(auto_now_add=True)
    ip_usuario = models.GenericIPAddressField(null=True, blank=True)

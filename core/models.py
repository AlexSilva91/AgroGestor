from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid

class Fazenda(models.Model):
    RAMO_CHOICES = [
        ("AVICULTURA_POSTURA", "Avicultura de postura"),
        ("AVICULTURA_CORTE", "Avicultura de corte"),
        ("SUINOCULTURA", "Suinocultura"),
        ("OVINOCULTURA", "Ovinocultura"),
        ("BOVINOCULTURA", "Bovinocultura"),
        ("CAPRINOCULTURA", "Caprinocultura"),
        ("PISCICULTURA", "Piscicultura"),
        ("MULTICULTURA", "Multicultura"),
        ("OUTRA", "Outra"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nome = models.CharField(max_length=100)
    localizacao = models.CharField(max_length=255, blank=True, null=True)
    ramo_atuacao = models.CharField(max_length=40, choices=RAMO_CHOICES, default="MULTICULTURA")
    responsavel = models.ForeignKey(
        "Usuario",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="fazendas_responsavel",
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nome


class Usuario(AbstractUser):
    ROLE_CHOICES = [
        ("SUPERADMIN", "Super administrador"),
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


class FazendaAcesso(models.Model):
    PERFIL_CHOICES = [
        ("ADMIN", "Administrador da fazenda"),
        ("OPERADOR", "Operador"),
        ("VETERINARIO", "Veterinário"),
        ("CONSULTOR", "Consultor"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    farm = models.ForeignKey(Fazenda, on_delete=models.CASCADE, related_name="acessos")
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="fazenda_acessos")
    perfil = models.CharField(max_length=20, choices=PERFIL_CHOICES, default="OPERADOR")
    ativo = models.BooleanField(default=True)

    can_view_rebanho = models.BooleanField(default=True)
    can_create_rebanho = models.BooleanField(default=False)
    can_update_rebanho = models.BooleanField(default=False)
    can_delete_rebanho = models.BooleanField(default=False)

    can_view_pastagem = models.BooleanField(default=True)
    can_create_pastagem = models.BooleanField(default=False)
    can_update_pastagem = models.BooleanField(default=False)
    can_delete_pastagem = models.BooleanField(default=False)

    can_view_financeiro = models.BooleanField(default=False)
    can_create_financeiro = models.BooleanField(default=False)
    can_update_financeiro = models.BooleanField(default=False)
    can_delete_financeiro = models.BooleanField(default=False)

    can_manage_users = models.BooleanField(default=False)
    can_view_gestao = models.BooleanField(default=True)
    can_create_gestao = models.BooleanField(default=False)
    can_update_gestao = models.BooleanField(default=False)
    can_delete_gestao = models.BooleanField(default=False)
    can_view_manejo = models.BooleanField(default=True)
    can_create_manejo = models.BooleanField(default=False)
    can_update_manejo = models.BooleanField(default=False)
    can_delete_manejo = models.BooleanField(default=False)
    can_view_nutricao = models.BooleanField(default=True)
    can_create_nutricao = models.BooleanField(default=False)
    can_update_nutricao = models.BooleanField(default=False)
    can_delete_nutricao = models.BooleanField(default=False)
    can_view_sanidade = models.BooleanField(default=True)
    can_create_sanidade = models.BooleanField(default=False)
    can_update_sanidade = models.BooleanField(default=False)
    can_delete_sanidade = models.BooleanField(default=False)
    can_view_producao = models.BooleanField(default=True)
    can_create_producao = models.BooleanField(default=False)
    can_update_producao = models.BooleanField(default=False)
    can_delete_producao = models.BooleanField(default=False)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["farm", "usuario"], name="unique_fazenda_usuario_acesso")
        ]

    def __str__(self):
        return f"{self.usuario} - {self.farm} ({self.perfil})"

    def save(self, *args, **kwargs):
        if self.perfil == "ADMIN":
            self.can_view_rebanho = True
            self.can_create_rebanho = True
            self.can_update_rebanho = True
            self.can_delete_rebanho = True
            self.can_view_pastagem = True
            self.can_create_pastagem = True
            self.can_update_pastagem = True
            self.can_delete_pastagem = True
            self.can_view_financeiro = True
            self.can_create_financeiro = True
            self.can_update_financeiro = True
            self.can_delete_financeiro = True
            self.can_manage_users = True
            self.can_view_gestao = True
            self.can_create_gestao = True
            self.can_update_gestao = True
            self.can_delete_gestao = True
            self.can_view_manejo = True
            self.can_create_manejo = True
            self.can_update_manejo = True
            self.can_delete_manejo = True
            self.can_view_nutricao = True
            self.can_create_nutricao = True
            self.can_update_nutricao = True
            self.can_delete_nutricao = True
            self.can_view_sanidade = True
            self.can_create_sanidade = True
            self.can_update_sanidade = True
            self.can_delete_sanidade = True
            self.can_view_producao = True
            self.can_create_producao = True
            self.can_update_producao = True
            self.can_delete_producao = True
        super().save(*args, **kwargs)


class ModuloSistema(models.Model):
    CODIGO_CHOICES = [
        ("avicultura", "Avicultura"),
        ("suinocultura", "Suinocultura"),
        ("ovinocultura", "Ovinocultura"),
        ("bovinocultura", "Bovinocultura"),
        ("gestao", "Gestão multi-cultura"),
        ("manejo", "Manejo"),
        ("nutricao", "Nutrição e ração"),
        ("sanidade", "Sanidade e enfermaria"),
        ("producao", "Produção"),
        ("financeiro", "Financeiro"),
        ("iot", "IoT"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo = models.CharField(max_length=40, choices=CODIGO_CHOICES, unique=True)
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True, null=True)
    ativo = models.BooleanField(default=True)

    def __str__(self):
        return self.nome


class FazendaModulo(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    farm = models.ForeignKey(Fazenda, on_delete=models.CASCADE, related_name="modulos")
    modulo = models.ForeignKey(ModuloSistema, on_delete=models.CASCADE, related_name="fazendas")
    liberado = models.BooleanField(default=True)
    liberado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["farm", "modulo"], name="unique_fazenda_modulo")
        ]

    def __str__(self):
        status = "liberado" if self.liberado else "bloqueado"
        return f"{self.farm} - {self.modulo} ({status})"


class LogAcao(models.Model):
    ACOES = [
        ("CREATE", "Criação"),
        ("UPDATE", "Atualização"),
        ("DELETE", "Remoção"),
        ("LOGIN", "Login"),
        ("LOGOUT", "Logout"),
        ("BACKUP", "Backup"),
        ("SECURITY", "Segurança"),
        ("OTHER", "Outra"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    farm = models.ForeignKey(Fazenda, on_delete=models.CASCADE, null=True, blank=True)
    usuario = models.ForeignKey("Usuario", on_delete=models.SET_NULL, null=True)
    acao = models.CharField(max_length=20, choices=ACOES)
    tabela_afetada = models.CharField(max_length=50)
    registro_id = models.CharField(max_length=80, null=True, blank=True)
    descricao = models.TextField(blank=True, null=True)
    data_hora = models.DateTimeField(auto_now_add=True)
    ip_usuario = models.GenericIPAddressField(null=True, blank=True)
    metodo = models.CharField(max_length=10, blank=True, null=True)
    caminho = models.CharField(max_length=255, blank=True, null=True)
    status_code = models.PositiveIntegerField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)
    dados = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-data_hora"]

    def __str__(self):
        usuario = self.usuario.email if self.usuario_id and self.usuario.email else self.usuario
        farm = self.farm.nome if self.farm_id else "global"
        return f"{self.acao} - {usuario} - {farm} - {self.data_hora}"


class BackupConfig(models.Model):
    FREQUENCIAS = [
        ("DIARIO", "Diário"),
        ("SEMANAL", "Semanal"),
        ("MENSAL", "Mensal"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    farm = models.OneToOneField(Fazenda, on_delete=models.CASCADE, related_name="backup_config")
    ativo = models.BooleanField(default=False)
    frequencia = models.CharField(max_length=20, choices=FREQUENCIAS, default="DIARIO")
    hora_execucao = models.TimeField(default="02:00")
    destino = models.CharField(max_length=255, default="backups")
    manter_ultimos = models.PositiveIntegerField(default=7)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    ultima_execucao_em = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        status = "ativo" if self.ativo else "inativo"
        return f"Backup {self.farm} ({status})"


class BackupExecucao(models.Model):
    STATUS = [
        ("SUCESSO", "Sucesso"),
        ("ERRO", "Erro"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    config = models.ForeignKey(BackupConfig, on_delete=models.CASCADE, related_name="execucoes")
    farm = models.ForeignKey(Fazenda, on_delete=models.CASCADE, related_name="backup_execucoes")
    status = models.CharField(max_length=20, choices=STATUS)
    arquivo = models.CharField(max_length=500, blank=True, null=True)
    mensagem = models.TextField(blank=True, null=True)
    iniciado_em = models.DateTimeField(auto_now_add=True)
    finalizado_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-iniciado_em"]

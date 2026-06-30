import uuid

from django.conf import settings
from django.db import models

from core.models import Fazenda


class Cultura(models.Model):
    TIPO_CHOICES = [
        ("AVICULTURA_POSTURA", "Avicultura de postura"),
        ("AVICULTURA_CORTE", "Avicultura de corte"),
        ("SUINOCULTURA", "Suinocultura"),
        ("OVINOCULTURA", "Ovinocultura"),
        ("BOVINOCULTURA", "Bovinocultura"),
        ("CAPRINOCULTURA", "Caprinocultura"),
        ("PISCICULTURA", "Piscicultura"),
        ("OUTRA", "Outra"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo = models.CharField(max_length=40, choices=TIPO_CHOICES, unique=True)
    nome = models.CharField(max_length=120)
    descricao = models.TextField(blank=True, null=True)
    ativo = models.BooleanField(default=True)

    def __str__(self):
        return self.nome


class Especie(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cultura = models.ForeignKey(Cultura, on_delete=models.PROTECT, related_name="especies")
    nome = models.CharField(max_length=120)
    nome_cientifico = models.CharField(max_length=160, blank=True, null=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["cultura", "nome"], name="unique_especie_por_cultura")
        ]

    def __str__(self):
        return self.nome


class FinalidadeProdutiva(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cultura = models.ForeignKey(Cultura, on_delete=models.PROTECT, related_name="finalidades")
    nome = models.CharField(max_length=120)
    descricao = models.TextField(blank=True, null=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["cultura", "nome"], name="unique_finalidade_por_cultura")
        ]

    def __str__(self):
        return f"{self.cultura} - {self.nome}"


class Instalacao(models.Model):
    TIPO_CHOICES = [
        ("GALPAO", "Galpão"),
        ("BAIA", "Baia"),
        ("PIQUETE", "Piquete"),
        ("PASTO", "Pasto"),
        ("MATERNIDADE", "Maternidade"),
        ("ENFERMARIA", "Enfermaria"),
        ("QUARENTENA", "Quarentena"),
        ("FABRICA_RACAO", "Fábrica de ração"),
        ("DEPOSITO", "Depósito"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    farm = models.ForeignKey(Fazenda, on_delete=models.CASCADE, related_name="instalacoes")
    cultura = models.ForeignKey(Cultura, on_delete=models.PROTECT, related_name="instalacoes", null=True, blank=True)
    nome = models.CharField(max_length=120)
    tipo = models.CharField(max_length=30, choices=TIPO_CHOICES)
    area_m2 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    capacidade_informada = models.PositiveIntegerField(null=True, blank=True)
    ativo = models.BooleanField(default=True)
    observacoes = models.TextField(blank=True, null=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["farm", "nome"], name="unique_instalacao_por_fazenda")
        ]

    def __str__(self):
        return f"{self.farm} - {self.nome}"


class RegraCapacidade(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cultura = models.ForeignKey(Cultura, on_delete=models.CASCADE, related_name="regras_capacidade")
    finalidade = models.ForeignKey(FinalidadeProdutiva, on_delete=models.CASCADE, null=True, blank=True)
    fase = models.CharField(max_length=100)
    animais_por_m2 = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True)
    area_minima_por_animal_m2 = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True)
    comedouros_por_animal = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True)
    bebedouros_por_animal = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True)
    observacoes = models.TextField(blank=True, null=True)
    ativo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.cultura} - {self.fase}"


class Plantel(models.Model):
    STATUS_CHOICES = [
        ("ATIVO", "Ativo"),
        ("ISOLADO", "Isolado"),
        ("ENCERRADO", "Encerrado"),
        ("VENDIDO", "Vendido"),
        ("ABATIDO", "Abatido"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    farm = models.ForeignKey(Fazenda, on_delete=models.CASCADE, related_name="planteis")
    cultura = models.ForeignKey(Cultura, on_delete=models.PROTECT, related_name="planteis")
    especie = models.ForeignKey(Especie, on_delete=models.PROTECT, null=True, blank=True)
    finalidade = models.ForeignKey(FinalidadeProdutiva, on_delete=models.PROTECT, null=True, blank=True)
    instalacao = models.ForeignKey(Instalacao, on_delete=models.PROTECT, related_name="planteis", null=True, blank=True)
    codigo = models.CharField(max_length=80)
    nome = models.CharField(max_length=140)
    data_alojamento = models.DateField()
    quantidade_inicial = models.PositiveIntegerField()
    quantidade_atual = models.PositiveIntegerField()
    idade_inicial_dias = models.PositiveIntegerField(default=0)
    peso_medio_inicial = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="ATIVO")
    origem = models.CharField(max_length=160, blank=True, null=True)
    observacoes = models.TextField(blank=True, null=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["farm", "codigo"], name="unique_plantel_codigo_por_fazenda")
        ]

    def __str__(self):
        return f"{self.codigo} - {self.nome}"


class AnimalIndividual(models.Model):
    SEXO_CHOICES = [("M", "Macho"), ("F", "Fêmea"), ("NI", "Não informado")]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    farm = models.ForeignKey(Fazenda, on_delete=models.CASCADE, related_name="animais_individuais")
    plantel = models.ForeignKey(Plantel, on_delete=models.SET_NULL, related_name="animais", null=True, blank=True)
    codigo = models.CharField(max_length=80)
    sexo = models.CharField(max_length=2, choices=SEXO_CHOICES, default="NI")
    nascimento = models.DateField(null=True, blank=True)
    peso_atual = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True)
    status = models.CharField(max_length=30, default="ATIVO")
    observacoes = models.TextField(blank=True, null=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["farm", "codigo"], name="unique_animal_individual_por_fazenda")
        ]

    def __str__(self):
        return self.codigo


class MovimentacaoPlantel(models.Model):
    TIPO_CHOICES = [
        ("ENTRADA", "Entrada"),
        ("TRANSFERENCIA", "Transferência"),
        ("MORTALIDADE", "Mortalidade"),
        ("DESCARTE", "Descarte"),
        ("VENDA", "Venda"),
        ("ABATE", "Abate"),
        ("ISOLAMENTO", "Isolamento"),
        ("RETORNO", "Retorno"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    farm = models.ForeignKey(Fazenda, on_delete=models.CASCADE, related_name="movimentacoes_plantel")
    plantel = models.ForeignKey(Plantel, on_delete=models.CASCADE, related_name="movimentacoes")
    tipo = models.CharField(max_length=30, choices=TIPO_CHOICES)
    origem = models.ForeignKey(Instalacao, on_delete=models.PROTECT, related_name="movimentacoes_origem", null=True, blank=True)
    destino = models.ForeignKey(Instalacao, on_delete=models.PROTECT, related_name="movimentacoes_destino", null=True, blank=True)
    quantidade = models.IntegerField()
    data_movimento = models.DateField()
    motivo = models.CharField(max_length=180, blank=True, null=True)
    observacoes = models.TextField(blank=True, null=True)
    criado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.plantel} - {self.tipo}"


class ProtocoloManejo(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cultura = models.ForeignKey(Cultura, on_delete=models.CASCADE, related_name="protocolos")
    finalidade = models.ForeignKey(FinalidadeProdutiva, on_delete=models.CASCADE, null=True, blank=True)
    nome = models.CharField(max_length=140)
    descricao = models.TextField(blank=True, null=True)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nome


class EtapaManejo(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    protocolo = models.ForeignKey(ProtocoloManejo, on_delete=models.CASCADE, related_name="etapas")
    nome = models.CharField(max_length=140)
    semana_inicio = models.PositiveIntegerField()
    semana_fim = models.PositiveIntegerField()
    objetivo = models.TextField(blank=True, null=True)
    ordem = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["ordem", "semana_inicio"]

    def __str__(self):
        return f"{self.protocolo} - {self.nome}"


class TarefaManejo(models.Model):
    TIPO_CHOICES = [
        ("RACAO", "Ração"),
        ("VACINA", "Vacina"),
        ("PESAGEM", "Pesagem"),
        ("SANIDADE", "Sanidade"),
        ("LIMPEZA", "Limpeza"),
        ("PRODUCAO", "Produção"),
        ("INSPECAO", "Inspeção"),
        ("OUTRA", "Outra"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    etapa = models.ForeignKey(EtapaManejo, on_delete=models.CASCADE, related_name="tarefas")
    tipo = models.CharField(max_length=30, choices=TIPO_CHOICES)
    titulo = models.CharField(max_length=140)
    descricao = models.TextField(blank=True, null=True)
    semana = models.PositiveIntegerField()
    dia_da_semana = models.PositiveIntegerField(default=1)
    obrigatoria = models.BooleanField(default=True)

    def __str__(self):
        return self.titulo


class AgendaManejo(models.Model):
    STATUS_CHOICES = [
        ("PENDENTE", "Pendente"),
        ("CONCLUIDA", "Concluída"),
        ("ATRASADA", "Atrasada"),
        ("CANCELADA", "Cancelada"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    farm = models.ForeignKey(Fazenda, on_delete=models.CASCADE, related_name="agendas_manejo")
    plantel = models.ForeignKey(Plantel, on_delete=models.CASCADE, related_name="agenda_manejo")
    tarefa = models.ForeignKey(TarefaManejo, on_delete=models.PROTECT, related_name="agendamentos")
    data_prevista = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDENTE")
    observacoes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.plantel} - {self.tarefa}"


class ExecucaoManejo(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agenda = models.OneToOneField(AgendaManejo, on_delete=models.CASCADE, related_name="execucao")
    executado_em = models.DateTimeField()
    executado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    resultado = models.TextField(blank=True, null=True)
    observacoes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Execução - {self.agenda}"


class Ingrediente(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    farm = models.ForeignKey(Fazenda, on_delete=models.CASCADE, related_name="ingredientes")
    nome = models.CharField(max_length=120)
    unidade = models.CharField(max_length=20, default="kg")
    custo_unitario = models.DecimalField(max_digits=12, decimal_places=4, default=0)
    ativo = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["farm", "nome"], name="unique_ingrediente_por_fazenda")
        ]

    def __str__(self):
        return self.nome


class FormulaRacao(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    farm = models.ForeignKey(Fazenda, on_delete=models.CASCADE, related_name="formulas_racao")
    cultura = models.ForeignKey(Cultura, on_delete=models.PROTECT, related_name="formulas_racao")
    finalidade = models.ForeignKey(FinalidadeProdutiva, on_delete=models.PROTECT, null=True, blank=True)
    nome = models.CharField(max_length=140)
    fase = models.CharField(max_length=100, blank=True, null=True)
    objetivo = models.TextField(blank=True, null=True)
    ativo = models.BooleanField(default=True)

    def __str__(self):
        return self.nome


class FormulaRacaoItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    formula = models.ForeignKey(FormulaRacao, on_delete=models.CASCADE, related_name="itens")
    ingrediente = models.ForeignKey(Ingrediente, on_delete=models.PROTECT)
    percentual = models.DecimalField(max_digits=7, decimal_places=4)
    observacoes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.formula} - {self.ingrediente}"


class OrdemFabricacaoRacao(models.Model):
    STATUS_CHOICES = [
        ("PLANEJADA", "Planejada"),
        ("PRODUZIDA", "Produzida"),
        ("CANCELADA", "Cancelada"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    farm = models.ForeignKey(Fazenda, on_delete=models.CASCADE, related_name="ordens_racao")
    formula = models.ForeignKey(FormulaRacao, on_delete=models.PROTECT, related_name="ordens")
    quantidade_kg = models.DecimalField(max_digits=12, decimal_places=3)
    custo_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    data_fabricacao = models.DateField()
    validade = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PLANEJADA")
    observacoes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.formula} - {self.quantidade_kg} kg"


class MovimentoEstoque(models.Model):
    TIPO_CHOICES = [
        ("ENTRADA", "Entrada"),
        ("SAIDA", "Saída"),
        ("AJUSTE", "Ajuste"),
        ("FABRICACAO", "Fabricação"),
        ("CONSUMO", "Consumo"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    farm = models.ForeignKey(Fazenda, on_delete=models.CASCADE, related_name="movimentos_estoque")
    ingrediente = models.ForeignKey(Ingrediente, on_delete=models.PROTECT, null=True, blank=True)
    ordem_racao = models.ForeignKey(OrdemFabricacaoRacao, on_delete=models.SET_NULL, null=True, blank=True)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    quantidade = models.DecimalField(max_digits=12, decimal_places=3)
    data_movimento = models.DateField()
    custo_unitario = models.DecimalField(max_digits=12, decimal_places=4, default=0)
    observacoes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.tipo} - {self.quantidade}"


class ConsumoRacao(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    farm = models.ForeignKey(Fazenda, on_delete=models.CASCADE, related_name="consumos_racao")
    plantel = models.ForeignKey(Plantel, on_delete=models.CASCADE, related_name="consumos_racao")
    formula = models.ForeignKey(FormulaRacao, on_delete=models.PROTECT, null=True, blank=True)
    quantidade_kg = models.DecimalField(max_digits=12, decimal_places=3)
    data_consumo = models.DateField()
    observacoes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.plantel} - {self.quantidade_kg} kg"


class OcorrenciaSanitaria(models.Model):
    STATUS_CHOICES = [
        ("ABERTA", "Aberta"),
        ("EM_TRATAMENTO", "Em tratamento"),
        ("ENCERRADA", "Encerrada"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    farm = models.ForeignKey(Fazenda, on_delete=models.CASCADE, related_name="ocorrencias_sanitarias")
    plantel = models.ForeignKey(Plantel, on_delete=models.CASCADE, related_name="ocorrencias_sanitarias", null=True, blank=True)
    animal = models.ForeignKey(AnimalIndividual, on_delete=models.CASCADE, related_name="ocorrencias_sanitarias", null=True, blank=True)
    data_ocorrencia = models.DateField()
    sintomas = models.TextField()
    diagnostico = models.CharField(max_length=180, blank=True, null=True)
    severidade = models.CharField(max_length=40, default="MEDIA")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="ABERTA")
    responsavel = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    observacoes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Ocorrência {self.data_ocorrencia}"


class IsolamentoSanitario(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    farm = models.ForeignKey(Fazenda, on_delete=models.CASCADE, related_name="isolamentos")
    ocorrencia = models.ForeignKey(OcorrenciaSanitaria, on_delete=models.CASCADE, related_name="isolamentos")
    plantel = models.ForeignKey(Plantel, on_delete=models.CASCADE, related_name="isolamentos", null=True, blank=True)
    animal = models.ForeignKey(AnimalIndividual, on_delete=models.CASCADE, related_name="isolamentos", null=True, blank=True)
    origem = models.ForeignKey(Instalacao, on_delete=models.PROTECT, related_name="isolamentos_origem", null=True, blank=True)
    enfermaria = models.ForeignKey(Instalacao, on_delete=models.PROTECT, related_name="isolamentos_enfermaria")
    data_entrada = models.DateField()
    data_saida = models.DateField(null=True, blank=True)
    motivo = models.TextField()
    ativo = models.BooleanField(default=True)

    def __str__(self):
        return f"Isolamento - {self.ocorrencia}"


class TratamentoSanitario(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ocorrencia = models.ForeignKey(OcorrenciaSanitaria, on_delete=models.CASCADE, related_name="tratamentos")
    medicamento = models.CharField(max_length=140)
    dose = models.CharField(max_length=80)
    via_aplicacao = models.CharField(max_length=80, blank=True, null=True)
    frequencia = models.CharField(max_length=120)
    dias_tratamento = models.PositiveIntegerField()
    carencia_dias = models.PositiveIntegerField(default=0)
    observacoes = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.medicamento


class CalendarioTratamento(models.Model):
    STATUS_CHOICES = [
        ("PENDENTE", "Pendente"),
        ("APLICADO", "Aplicado"),
        ("ATRASADO", "Atrasado"),
        ("CANCELADO", "Cancelado"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tratamento = models.ForeignKey(TratamentoSanitario, on_delete=models.CASCADE, related_name="calendario")
    data_prevista = models.DateField()
    data_aplicacao = models.DateTimeField(null=True, blank=True)
    aplicado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDENTE")
    observacoes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.tratamento} - {self.data_prevista}"


class AltaSanitaria(models.Model):
    DESTINO_CHOICES = [
        ("RETORNO", "Retorno ao plantel"),
        ("OBITO", "Óbito"),
        ("DESCARTE", "Descarte"),
        ("VENDA", "Venda"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ocorrencia = models.OneToOneField(OcorrenciaSanitaria, on_delete=models.CASCADE, related_name="alta")
    data_alta = models.DateField()
    destino = models.CharField(max_length=20, choices=DESTINO_CHOICES)
    observacoes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Alta - {self.ocorrencia}"


class PesagemPlantel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    farm = models.ForeignKey(Fazenda, on_delete=models.CASCADE, related_name="pesagens")
    plantel = models.ForeignKey(Plantel, on_delete=models.CASCADE, related_name="pesagens")
    data_pesagem = models.DateField()
    quantidade_amostrada = models.PositiveIntegerField()
    peso_medio = models.DecimalField(max_digits=8, decimal_places=3)
    observacoes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.plantel} - {self.data_pesagem}"


class ProducaoOvos(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    farm = models.ForeignKey(Fazenda, on_delete=models.CASCADE, related_name="producoes_ovos")
    plantel = models.ForeignKey(Plantel, on_delete=models.CASCADE, related_name="producoes_ovos")
    data_producao = models.DateField()
    ovos_total = models.PositiveIntegerField()
    ovos_comerciais = models.PositiveIntegerField(default=0)
    ovos_descartados = models.PositiveIntegerField(default=0)
    ovos_trincados = models.PositiveIntegerField(default=0)
    observacoes = models.TextField(blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["plantel", "data_producao"], name="unique_producao_ovos_por_dia")
        ]

    def __str__(self):
        return f"{self.plantel} - {self.data_producao}"


class ProducaoCorte(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    farm = models.ForeignKey(Fazenda, on_delete=models.CASCADE, related_name="producoes_corte")
    plantel = models.ForeignKey(Plantel, on_delete=models.CASCADE, related_name="producoes_corte")
    data_registro = models.DateField()
    peso_medio = models.DecimalField(max_digits=8, decimal_places=3)
    ganho_peso_dia = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True)
    conversao_alimentar = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True)
    mortalidade_periodo = models.PositiveIntegerField(default=0)
    observacoes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.plantel} - {self.data_registro}"


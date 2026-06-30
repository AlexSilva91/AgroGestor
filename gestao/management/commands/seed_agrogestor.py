from django.core.management.base import BaseCommand

from core.models import Fazenda, FazendaModulo, ModuloSistema
from gestao.models import Cultura, Especie, FinalidadeProdutiva


MODULOS = [
    ("avicultura", "Avicultura", "Controle de aves de postura e corte."),
    ("suinocultura", "Suinocultura", "Controle de suínos por fase e lote."),
    ("ovinocultura", "Ovinocultura", "Controle de ovinos por lote ou indivíduo."),
    ("bovinocultura", "Bovinocultura", "Controle de bovinos e rebanhos."),
    ("gestao", "Gestão multi-cultura", "Plantéis, instalações, capacidade e movimentações."),
    ("manejo", "Manejo", "Protocolos, tarefas e calendário de manejo."),
    ("nutricao", "Nutrição e ração", "Formulação, fabricação, estoque e consumo de ração."),
    ("sanidade", "Sanidade e enfermaria", "Ocorrências, isolamento, tratamentos e altas."),
    ("producao", "Produção", "Ovos, corte, pesagens e índices produtivos."),
    ("financeiro", "Financeiro", "Receitas, custos e margens por atividade."),
    ("iot", "IoT", "Sensores e automações."),
]

CULTURAS = [
    ("AVICULTURA_POSTURA", "Avicultura de postura", ["Poedeiras comerciais"], ["Postura"]),
    ("AVICULTURA_CORTE", "Avicultura de corte", ["Frango de corte"], ["Corte"]),
    ("SUINOCULTURA", "Suinocultura", ["Suínos"], ["Reprodução", "Creche", "Crescimento", "Terminação"]),
    ("OVINOCULTURA", "Ovinocultura", ["Ovinos"], ["Cria", "Recria", "Engorda", "Reprodução"]),
    ("BOVINOCULTURA", "Bovinocultura", ["Bovinos"], ["Leite", "Corte", "Recria", "Engorda"]),
]


class Command(BaseCommand):
    help = "Cria módulos e cadastros iniciais do AgroGestor."

    def handle(self, *args, **options):
        for codigo, nome, descricao in MODULOS:
            ModuloSistema.objects.update_or_create(
                codigo=codigo,
                defaults={"nome": nome, "descricao": descricao, "ativo": True},
            )

        for codigo, nome, especies, finalidades in CULTURAS:
            cultura, _ = Cultura.objects.update_or_create(
                codigo=codigo,
                defaults={"nome": nome, "ativo": True},
            )
            for especie in especies:
                Especie.objects.update_or_create(
                    cultura=cultura,
                    nome=especie,
                    defaults={"ativo": True},
                )
            for finalidade in finalidades:
                FinalidadeProdutiva.objects.update_or_create(
                    cultura=cultura,
                    nome=finalidade,
                    defaults={"ativo": True},
                )

        for fazenda in Fazenda.objects.all():
            for modulo in ModuloSistema.objects.filter(ativo=True):
                FazendaModulo.objects.get_or_create(farm=fazenda, modulo=modulo, defaults={"liberado": True})

        self.stdout.write(self.style.SUCCESS("Cadastros iniciais do AgroGestor criados/atualizados."))


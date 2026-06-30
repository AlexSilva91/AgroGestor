from django.contrib import admin

from . import models


for model in [
    models.Cultura,
    models.Especie,
    models.FinalidadeProdutiva,
    models.Instalacao,
    models.RegraCapacidade,
    models.Plantel,
    models.AnimalIndividual,
    models.MovimentacaoPlantel,
    models.ProtocoloManejo,
    models.EtapaManejo,
    models.TarefaManejo,
    models.AgendaManejo,
    models.ExecucaoManejo,
    models.Ingrediente,
    models.FormulaRacao,
    models.FormulaRacaoItem,
    models.OrdemFabricacaoRacao,
    models.MovimentoEstoque,
    models.ConsumoRacao,
    models.OcorrenciaSanitaria,
    models.IsolamentoSanitario,
    models.TratamentoSanitario,
    models.CalendarioTratamento,
    models.AltaSanitaria,
    models.PesagemPlantel,
    models.ProducaoOvos,
    models.ProducaoCorte,
]:
    admin.site.register(model)


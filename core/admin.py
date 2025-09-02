from django.contrib import admin
from .models import Fazenda, Usuario, LogAcao
from rebanho.models import Rebanho, Animal, HistoricoAnimal
from pastagem.models import Pastagem, MovimentacaoAnimal
from financeiro.models import LancamentoFinanceiro

admin.site.register(Fazenda)
admin.site.register(Usuario)
admin.site.register(LogAcao)
admin.site.register(MovimentacaoAnimal)
admin.site.register(Pastagem)
admin.site.register(Rebanho)
admin.site.register(Animal)
admin.site.register(HistoricoAnimal)
admin.site.register(LancamentoFinanceiro)

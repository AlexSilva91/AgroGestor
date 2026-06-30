from django.urls import path

from . import views


urlpatterns = [
    path("capacidade/calcular/", views.calcular_capacidade, name="calcular_capacidade"),
    path("manejo/aplicar-protocolo/", views.aplicar_protocolo, name="aplicar_protocolo"),
    path("manejo/agendas/<uuid:pk>/concluir/", views.concluir_tarefa_manejo, name="concluir_tarefa_manejo"),
    path("nutricao/fabricar-racao/", views.fabricar_racao, name="fabricar_racao"),
    path("nutricao/consumo-racao/", views.registrar_consumo_racao, name="registrar_consumo_racao"),
    path("sanidade/isolar/", views.isolar_sanitario, name="isolar_sanitario"),
    path("sanidade/gerar-calendario-tratamento/", views.gerar_calendario_tratamento, name="gerar_calendario_tratamento"),
    path("relatorios/plantel/", views.relatorio_plantel, name="relatorio_plantel"),
    path("dashboard-operacional/", views.dashboard_operacional, name="dashboard_operacional"),
    path("<str:recurso>/", views.listar, name="listar"),
    path("<str:recurso>/criar/", views.criar, name="criar"),
    path("<str:recurso>/<uuid:pk>/", views.detalhar, name="detalhar"),
    path("<str:recurso>/<uuid:pk>/editar/", views.editar, name="editar"),
    path("<str:recurso>/<uuid:pk>/excluir/", views.excluir, name="excluir"),
]

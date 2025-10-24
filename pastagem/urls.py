from django.urls import path
from . import views

urlpatterns = [
    # Pastagens
    path("pastagens/", views.listar_pastagens),
    path("pastagens/<uuid:pk>/", views.detalhar_pastagem),
    path("pastagens/criar/", views.criar_pastagem),
    path("pastagens/<uuid:pk>/editar/", views.editar_pastagem),
    path("pastagens/<uuid:pk>/excluir/", views.excluir_pastagem),

    # Movimentações de Animais
    path("movimentacoes/", views.listar_movimentacoes),
    path("movimentacoes/<uuid:pk>/", views.detalhar_movimentacao),
    path("movimentacoes/criar/", views.criar_movimentacao),
    path("movimentacoes/<uuid:pk>/editar/", views.editar_movimentacao),
    path("movimentacoes/<uuid:pk>/excluir/", views.excluir_movimentacao),
]

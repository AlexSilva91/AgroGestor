from django.urls import path
from . import views

urlpatterns = [
    # Rebanhos
    path("rebanhos/", views.listar_rebanhos),
    path("rebanhos/<uuid:pk>/", views.detalhar_rebanho),
    path("rebanhos/criar/", views.criar_rebanho),
    path("rebanhos/<uuid:pk>/editar/", views.editar_rebanho),
    path("rebanhos/<uuid:pk>/excluir/", views.excluir_rebanho),

    # Animais
    path("animais/", views.listar_animais),
    path("animais/<uuid:pk>/", views.detalhar_animal),
    path("animais/criar/", views.criar_animal),
    path("animais/<uuid:pk>/editar/", views.editar_animal),
    path("animais/<uuid:pk>/excluir/", views.excluir_animal),

    # Histórico Animal
    path("historicos/", views.listar_historicos),
    path("historicos/<uuid:pk>/", views.detalhar_historico),
    path("historicos/criar/", views.criar_historico),
    path("historicos/<uuid:pk>/editar/", views.editar_historico),
    path("historicos/<uuid:pk>/excluir/", views.excluir_historico),
]

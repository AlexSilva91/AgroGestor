from django.urls import path
from . import views

app_name = 'financeiro'

urlpatterns = [
    path('lancamentos/', views.lista_lancamentos, name='lista'),
    path('lancamentos/criar/', views.criar_lancamento, name='criar'),
    path('lancamentos/<uuid:pk>/', views.detalhar_lancamento, name='detalhar'),
    path('lancamentos/<uuid:pk>/editar/', views.editar_lancamento, name='editar'),
    path('lancamentos/<uuid:pk>/excluir/', views.excluir_lancamento, name='excluir'),
]

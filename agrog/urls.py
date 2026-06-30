"""
URL configuration for agrog project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path, re_path
from django.contrib import messages
from django.shortcuts import redirect
from core import views

def catch_all_view(request, unused_path):
    """Captura todas as rotas não mapeadas"""
    messages.error(request, f'Página "{request.path}" não encontrada.')
    return redirect('login')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.login_view, name='login'),
    path('login/ajax/', views.login_ajax, name='login_ajax'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('api/dashboard/metricas/', views.metricas_dashboard, name='metricas_dashboard'),
    path('dashboard/logout/', views.logout_view, name='logout'),
    path('api/fazendas/', views.listar_fazendas_usuario, name='listar_fazendas_usuario'),
    path('api/fazendas/criar-com-admin/', views.criar_fazenda_com_admin, name='criar_fazenda_com_admin'),
    path('api/fazendas/ativa/', views.definir_fazenda_ativa, name='definir_fazenda_ativa'),
    path('api/fazendas/modulos/', views.listar_modulos_fazenda, name='listar_modulos_fazenda'),
    path('api/fazendas/modulos/salvar/', views.salvar_modulos_fazenda, name='salvar_modulos_fazenda'),
    path('api/fazendas/acessos/', views.listar_acessos_fazenda, name='listar_acessos_fazenda'),
    path('api/fazendas/acessos/<uuid:pk>/editar/', views.editar_acesso_fazenda, name='editar_acesso_fazenda'),
    path('api/auditoria/logs/', views.listar_logs_auditoria, name='listar_logs_auditoria'),
    path('api/backups/config/', views.backup_config, name='backup_config'),
    path('api/backups/executar/', views.executar_backup_manual, name='executar_backup_manual'),
    path('api/usuarios/', views.criar_usuario, name='criar_usuario'),
    path('api/usuarios/<int:pk>/', views.detalhar_usuario, name='detalhar_usuario'),
    path('api/usuarios/<int:pk>/editar/', views.editar_usuario, name='editar_usuario'),
    path('api/usuarios/<int:pk>/ativar/', views.definir_status_usuario, {"ativo": True}, name='ativar_usuario'),
    path('api/usuarios/<int:pk>/desativar/', views.definir_status_usuario, {"ativo": False}, name='desativar_usuario'),
    path('api/usuarios/<int:pk>/excluir/', views.excluir_usuario, name='excluir_usuario'),
    path('api/crud/', views.crud_schema, name='crud_schema'),
    path('api/crud/<str:entity>/', views.crud_listar, name='crud_listar'),
    path('api/crud/<str:entity>/criar/', views.crud_criar, name='crud_criar'),
    path('api/crud/<str:entity>/<str:pk>/', views.crud_detalhar, name='crud_detalhar'),
    path('api/crud/<str:entity>/<str:pk>/editar/', views.crud_editar, name='crud_editar'),
    path('api/crud/<str:entity>/<str:pk>/excluir/', views.crud_excluir, name='crud_excluir'),
    path('financeiro/', include('financeiro.urls')),
    path('rebanho/', include('rebanho.urls')),
    path('pastagem/', include('pastagem.urls')),  
    path('gestao/', include('gestao.urls')),

    re_path(r'^(?P<unused_path>.*)$', catch_all_view),
]

# Handlers personalizados - devem estar no nível do projeto
def handler404(request, exception):
    """Handler personalizado para 404"""
    messages.error(request, 'Página não encontrada.')
    return redirect('login')

def handler403(request, exception):
    """Handler personalizado para 403 (permissão negada)"""
    messages.error(request, 'Você não tem permissão para acessar esta página.')
    return redirect('login')

def handler500(request):
    """Handler personalizado para 500"""
    messages.error(request, 'Erro interno do servidor.')
    return redirect('login')

# Atribua os handlers
handler404 = handler404
handler403 = handler403
handler500 = handler500

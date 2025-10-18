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
from django.urls import path, re_path
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
    path('dashboard/logout/', views.logout_view, name='logout'),


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
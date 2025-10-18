
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponseForbidden
from django.core.paginator import Paginator
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.contrib.auth import get_user_model
import json

def login_view(request):
    """Renderiza a página de login na rota raiz"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    next_url = request.GET.get('next', '')
    context = {'next_url': next_url}
    
    return render(request, 'login.html', context)

@csrf_exempt
@require_http_methods(["POST"])
def login_ajax(request):
    """Processa o login via AJAX"""
    if request.user.is_authenticated:
        return JsonResponse({
            'success': True,
            'message': 'Usuário já autenticado',
            'redirect_url': '/dashboard/'
        })
    
    try:
        data = json.loads(request.body)
        login_input = data.get('login', '').strip()
        password = data.get('password', '').strip()
        next_url = data.get('next_url', '/dashboard/').strip()
        
        if not login_input or not password:
            return JsonResponse({
                'success': False,
                'message': 'Por favor, preencha todos os campos.'
            }, status=400)
        
        user = authenticate(request, username=login_input, password=password)
        
        if user is not None:
            login(request, user)
            
            redirect_url = next_url if next_url else '/dashboard/'
            
            if not redirect_url.startswith('/') or '//' in redirect_url:
                redirect_url = '/dashboard/'
                
            return JsonResponse({
                'success': True,
                'message': 'Login realizado com sucesso!',
                'redirect_url': redirect_url
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Login ou senha incorretos.'
            }, status=401)
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Erro no processamento dos dados.'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'Erro interno do servidor.'
        }, status=500)

@login_required
def dashboard(request):
    # Buscar todos os usuários
    User = get_user_model()
    usuarios_list = User.objects.all().order_by('-date_joined')
    paginator = Paginator(usuarios_list, 10)
    page = request.GET.get('page')
    usuarios = paginator.get_page(page)
    
    context = {
        'usuarios': usuarios,
    }
    return render(request, 'base/dashboard_content.html', context)

@login_required
@require_http_methods(["POST", "GET"])
def logout_view(request):
    """View para logout"""
    logout(request)
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': 'Logout realizado com sucesso!',
            'redirect_url': '/'
        })
    
    messages.success(request, 'Logout realizado com sucesso!')
    return redirect('login')
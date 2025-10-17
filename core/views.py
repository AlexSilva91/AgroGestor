from django.shortcuts import render, get_object_or_404
from django.contrib.auth.models import User, Group
from django.core.paginator import Paginator
from django.shortcuts import render
from django.contrib.auth import get_user_model
# Create your views here.
def index(request):
    return render(request, 'login.html')

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
    return render(request, 'dashboard_content.html', context)

"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
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
from django.urls import path
from django.views.generic import RedirectView
from django.contrib.auth.decorators import login_required

from config import views

urlpatterns = [
    path('', RedirectView.as_view(url='/dashboard.html', permanent=False), name='home'),
    path('dashboard.html', login_required(views.dashboard), name='dashboard'),
    path('receitas.html', login_required(views.receitas), name='receitas'),
    path('receitas/<int:receita_id>/excluir/', login_required(views.excluir_receita), name='excluir_receita'),
    path('despesas.html', login_required(views.despesas), name='despesas'),
    path('despesas/<int:despesa_id>/excluir/', login_required(views.excluir_despesa), name='excluir_despesa'),
    path('investimentos.html', login_required(views.investimentos), name='investimentos'),
    path('investimentos/<int:investimento_id>/excluir/', login_required(views.excluir_investimento), name='excluir_investimento'),
    path('login/login.html', views.entrar, name='entrar'),
    path('login/registro.html', views.cadastrar, name='cadastrar'),
    path('questionario/', login_required(views.questionario), name='questionario'),
    path('logout/', views.sair, name='sair'),
    path('admin/', admin.site.urls),
]

import json
import logging
from urllib.error import URLError
from urllib.request import urlopen

from django.core.cache import cache
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_http_methods, require_POST

from config.forms import FormularioPerfilFinanceiro
from model.perfil_financeiro import PerfilFinanceiro

logger = logging.getLogger(__name__)
ATIVOS_B3 = ('PETR4', 'VALE3', 'ITUB4', 'B3SA3', 'BOVA11', 'HGLG11')


def _url_de_destino(request):
    destino = request.POST.get('next') or request.GET.get('next')
    if destino and url_has_allowed_host_and_scheme(
        destino,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return destino
    return reverse('dashboard')


@require_http_methods(['GET', 'POST'])
def entrar(request):
    if request.user.is_authenticated:
        if not PerfilFinanceiro.objects.filter(usuario=request.user).exists():
            return redirect('questionario')
        return redirect(_url_de_destino(request))

    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        senha = request.POST.get('senha', '')
        usuario = authenticate(request, username=email, password=senha)

        if usuario:
            login(request, usuario)
            if not PerfilFinanceiro.objects.filter(usuario=usuario).exists():
                request.session['apos_questionario'] = _url_de_destino(request)
                return redirect('questionario')
            return redirect(_url_de_destino(request))

        messages.error(request, 'E-mail ou senha inválidos.')

    return render(
        request,
        'login/login.html',
        {'next': request.POST.get('next') or request.GET.get('next', '')},
    )


@require_http_methods(['GET', 'POST'])
def cadastrar(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        nome = request.POST.get('nome', '').strip()
        sobrenome = request.POST.get('sobrenome', '').strip()
        email = request.POST.get('email', '').strip().lower()
        senha = request.POST.get('senha', '')
        confirmar_senha = request.POST.get('confirmar_senha', '')
        erros = []
        email_valido = False
        usuario_modelo = get_user_model()

        if not nome:
            erros.append('Informe seu nome.')
        try:
            validate_email(email)
            email_valido = True
        except ValidationError:
            erros.append('Informe um e-mail válido.')

        limite_email = usuario_modelo._meta.get_field('username').max_length
        if email_valido and len(email) > limite_email:
            erros.append(f'O e-mail deve ter no máximo {limite_email} caracteres.')
        if email_valido and usuario_modelo.objects.filter(email__iexact=email).exists():
            erros.append('Já existe uma conta cadastrada com esse e-mail.')
        if not senha:
            erros.append('Informe uma senha.')
        elif senha != confirmar_senha:
            erros.append('As senhas não conferem.')

        usuario = usuario_modelo(
            username=email,
            email=email,
            first_name=nome,
            last_name=sobrenome,
        )
        if email_valido and senha:
            try:
                validate_password(senha, user=usuario)
            except ValidationError as erro:
                erros.extend(erro.messages)

        if erros:
            for erro in erros:
                messages.error(request, erro)
            return render(request, 'login/registro.html', {'dados': request.POST})

        usuario = usuario_modelo.objects.create_user(
            username=email,
            email=email,
            password=senha,
            first_name=nome,
            last_name=sobrenome,
        )
        login(request, usuario)
        request.session['apos_questionario'] = reverse('dashboard')
        return redirect('questionario')

    return render(request, 'login/registro.html')


@require_POST
def sair(request):
    logout(request)
    return redirect('entrar')


@require_http_methods(['GET', 'POST'])
def questionario(request):
    perfil = PerfilFinanceiro.objects.filter(usuario=request.user).first()
    formulario = FormularioPerfilFinanceiro(request.POST or None, instance=perfil)

    if request.method == 'POST' and formulario.is_valid():
        perfil = formulario.save(commit=False)
        perfil.usuario = request.user
        perfil.save()
        destino = request.session.pop('apos_questionario', reverse('dashboard'))
        if url_has_allowed_host_and_scheme(
            destino,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        ):
            return redirect(destino)
        return redirect('dashboard')

    return render(request, 'questionario.html', {'formulario': formulario})


def _formatar_real(valor):
    valor_formatado = f'{valor:,.2f}'
    return 'R$ ' + valor_formatado.replace(',', 'X').replace('.', ',').replace('X', '.')


def dashboard(request):
    perfil = PerfilFinanceiro.objects.filter(usuario=request.user).first()
    if perfil is None:
        request.session['apos_questionario'] = reverse('dashboard')
        return redirect('questionario')

    saldo_mensal = perfil.renda_mensal - perfil.despesas_mensais
    percentual_despesas = None
    largura_despesas = 0
    if perfil.renda_mensal:
        percentual_despesas = int(perfil.despesas_mensais * 100 / perfil.renda_mensal)
        largura_despesas = min(100, percentual_despesas)

    return render(
        request,
        'dashboard.html',
        {
            'perfil': perfil,
            'saldo_mensal': _formatar_real(saldo_mensal),
            'renda_mensal': _formatar_real(perfil.renda_mensal),
            'despesas_mensais': _formatar_real(perfil.despesas_mensais),
            'investimentos': _formatar_real(perfil.investimentos),
            'percentual_despesas': percentual_despesas,
            'largura_despesas': largura_despesas,
            'situacao_financeira': 'Saldo positivo' if saldo_mensal >= 0 else 'Atenção ao orçamento',
            'classe_situacao': 'success' if saldo_mensal >= 0 else 'warning',
        },
    )


def investimentos(request):
    if request.GET.get('atualizar') == '1':
        cache.delete('cotacoes_b3')

    ativos = cache.get('cotacoes_b3')
    erro_cotacoes = None

    if ativos is None:
        try:
            with urlopen('https://brapi.dev/api/quote/list', timeout=12) as resposta:
                dados = json.load(resposta)
        except (URLError, TimeoutError, json.JSONDecodeError) as erro:
            logger.warning('Não foi possível consultar as cotações da B3: %s', erro)
            ativos = []
            erro_cotacoes = 'Não foi possível carregar as cotações agora. Tente atualizar a página.'
        else:
            if not isinstance(dados, dict) or not isinstance(dados.get('stocks'), list):
                logger.error('A API de cotações retornou uma resposta inesperada.')
                ativos = []
                erro_cotacoes = 'A API de cotações retornou dados inválidos.'
            else:
                cotacoes = {
                    item.get('stock'): item
                    for item in dados['stocks']
                    if isinstance(item, dict) and item.get('stock') in ATIVOS_B3
                }
                ativos = [cotacoes[codigo] for codigo in ATIVOS_B3 if codigo in cotacoes]
                if not ativos:
                    erro_cotacoes = 'A API não retornou cotações para os ativos selecionados.'
                else:
                    cache.set('cotacoes_b3', ativos, 300)

    return render(
        request,
        'investimentos.html',
        {
            'ativos_b3': ativos,
            'erro_cotacoes': erro_cotacoes,
            'consulta_cotacoes': timezone.localtime(),
        },
    )

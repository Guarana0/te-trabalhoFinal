import json
import logging
from datetime import date, timedelta
from decimal import Decimal
from urllib.error import URLError
from urllib.request import urlopen

from django.core.cache import cache
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.core.validators import validate_email
from django.db.models import Count, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_http_methods, require_POST

from config.forms import (
    FormularioDespesa,
    FormularioInvestimento,
    FormularioPerfilFinanceiro,
    FormularioReceita,
)
from model.despesa import Despesa
from model.investimento import Investimento
from model.perfil_financeiro import PerfilFinanceiro
from model.receita import Receita

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

    hoje = timezone.localdate()
    inicio_mes = date(hoje.year, hoje.month, 1)
    receitas_mes = Receita.objects.filter(
        usuario=request.user,
        data__gte=inicio_mes,
        data__lte=hoje,
    ).aggregate(total=Sum('valor'))['total']
    despesas_mes = Despesa.objects.filter(
        usuario=request.user,
        data__gte=inicio_mes,
        data__lte=hoje,
    ).aggregate(total=Sum('valor'))['total']
    renda_mensal = receitas_mes if receitas_mes is not None else perfil.renda_mensal
    despesas_mensais = despesas_mes if despesas_mes is not None else perfil.despesas_mensais
    saldo_mensal = renda_mensal - despesas_mensais
    percentual_despesas = None
    largura_despesas = 0
    if renda_mensal:
        percentual_despesas = int(despesas_mensais * 100 / renda_mensal)
        largura_despesas = min(100, percentual_despesas)

    total_carteira = Investimento.objects.filter(usuario=request.user).aggregate(
        total=Sum('valor_atual'),
    )['total']
    if total_carteira is not None:
        valor_investimentos = _formatar_real(total_carteira)
        origem_investimentos = 'Valor atual da carteira registrada'
    else:
        valor_investimentos = _formatar_real(perfil.investimentos)
        origem_investimentos = 'Estimativa informada no questionário'

    return render(
        request,
        'dashboard.html',
        {
            'perfil': perfil,
            'saldo_mensal': _formatar_real(saldo_mensal),
            'renda_mensal': _formatar_real(renda_mensal),
            'despesas_mensais': _formatar_real(despesas_mensais),
            'renda_valor': renda_mensal,
            'despesas_valor': despesas_mensais,
            'origem_receita': (
                'Soma das receitas lançadas neste mês'
                if receitas_mes is not None
                else 'Estimativa do questionário'
            ),
            'origem_despesas': (
                'Soma das despesas lançadas neste mês'
                if despesas_mes is not None
                else 'Estimativa do questionário'
            ),
            'investimentos': valor_investimentos,
            'origem_investimentos': origem_investimentos,
            'percentual_despesas': percentual_despesas,
            'largura_despesas': largura_despesas,
            'situacao_financeira': 'Saldo positivo' if saldo_mensal >= 0 else 'Atenção ao orçamento',
            'classe_situacao': 'success' if saldo_mensal >= 0 else 'warning',
        },
    )


def _inicio_do_periodo(periodo, hoje):
    if periodo == '30d':
        return hoje - timedelta(days=29), 1

    meses = {'3m': 3, '6m': 6, '12m': 12}[periodo]
    indice_mes = hoje.year * 12 + hoje.month - meses
    return date(indice_mes // 12, indice_mes % 12 + 1, 1), meses


def _dados_do_grafico(lancamentos, periodo, inicio, quantidade_meses):
    dados = []
    if periodo == '30d':
        for semana in range(5):
            inicio_semana = inicio + timedelta(days=semana * 7)
            fim_semana = min(inicio_semana + timedelta(days=6), timezone.localdate())
            total_semana = lancamentos.filter(
                data__gte=inicio_semana,
                data__lte=fim_semana,
            ).aggregate(total=Sum('valor'))['total'] or Decimal('0.00')
            dados.append({'rotulo': inicio_semana.strftime('%d/%m'), 'valor': float(total_semana)})
        return dados

    nomes_meses = ('Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez')
    indice_mes = inicio.year * 12 + inicio.month - 1
    for deslocamento in range(quantidade_meses):
        ano_mes = indice_mes + deslocamento
        ano, mes_indice = divmod(ano_mes, 12)
        mes = mes_indice + 1
        inicio_mes = date(ano, mes, 1)
        fim_mes = (
            date(ano + 1, 1, 1) - timedelta(days=1)
            if mes == 12
            else date(ano, mes + 1, 1) - timedelta(days=1)
        )
        total_mes = lancamentos.filter(
            data__gte=inicio_mes,
            data__lte=min(fim_mes, timezone.localdate()),
        ).aggregate(total=Sum('valor'))['total'] or Decimal('0.00')
        dados.append({
            'rotulo': f'{nomes_meses[mes_indice]}/{ano % 100:02d}',
            'valor': float(total_mes),
        })
    return dados


@require_http_methods(['GET', 'POST'])
def receitas(request):
    hoje = timezone.localdate()
    periodo = request.GET.get('periodo', '12m')
    if periodo not in ('30d', '3m', '6m', '12m'):
        periodo = '12m'
    inicio, quantidade_meses = _inicio_do_periodo(periodo, hoje)
    receita_edicao = None
    if request.GET.get('editar'):
        receita_edicao = get_object_or_404(
            Receita,
            pk=request.GET['editar'],
            usuario=request.user,
        )
    formulario = FormularioReceita(request.POST or None, instance=receita_edicao)

    if request.method == 'POST' and formulario.is_valid():
        receita = formulario.save(commit=False)
        receita.usuario = request.user
        receita.save()
        messages.success(
            request,
            'Receita atualizada com sucesso.' if receita_edicao else 'Receita registrada com sucesso.',
        )
        return redirect(f"{reverse('receitas')}?periodo={periodo}")

    receitas_periodo = Receita.objects.filter(
        usuario=request.user,
        data__gte=inicio,
        data__lte=hoje,
    )
    total = receitas_periodo.aggregate(total=Sum('valor'))['total'] or Decimal('0.00')
    quantidade_periodos = 1 if periodo == '30d' else quantidade_meses
    perfil = PerfilFinanceiro.objects.filter(usuario=request.user).first()
    meta = perfil.renda_mensal * quantidade_periodos if perfil else Decimal('0.00')
    despesas_periodo = Despesa.objects.filter(
        usuario=request.user,
        data__gte=inicio,
        data__lte=hoje,
    ).aggregate(total=Sum('valor'))['total'] or Decimal('0.00')
    percentual_meta = int(total * 100 / meta) if meta else None

    categorias = []
    for item in receitas_periodo.values('categoria').annotate(
        total=Sum('valor'),
        quantidade=Count('id'),
    ).order_by('-total'):
        valor_categoria = item['total'] or Decimal('0.00')
        percentual = int(valor_categoria * 100 / total) if total else 0
        categorias.append({
            'nome': item['categoria'],
            'valor': _formatar_real(valor_categoria),
            'percentual': percentual,
            'quantidade': item['quantidade'],
            'largura': min(100, percentual),
            'status': 'Principal' if not categorias else 'Outra categoria',
        })

    receitas_paginadas = Paginator(receitas_periodo, 20).get_page(request.GET.get('pagina'))
    return render(
        request,
        'receitas.html',
        {
            'formulario': formulario,
            'edit_id': receita_edicao.pk if receita_edicao else None,
            'periodo': periodo,
            'periodo_rotulo': {
                '30d': 'Últimos 30 dias',
                '3m': 'Últimos 3 meses',
                '6m': 'Últimos 6 meses',
                '12m': 'Últimos 12 meses',
            }[periodo],
            'total_receitas': _formatar_real(total),
            'media_mensal': _formatar_real(total / quantidade_periodos),
            'percentual_meta': percentual_meta,
            'largura_meta': min(100, percentual_meta or 0),
            'situacao_meta': (
                'Defina sua renda no perfil'
                if percentual_meta is None
                else 'Meta atingida'
                if percentual_meta >= 100
                else 'Abaixo da estimativa'
            ),
            'estimativa_renda': _formatar_real(perfil.renda_mensal) if perfil else None,
            'fluxo_liquido': _formatar_real(total - despesas_periodo),
            'quantidade_receitas': receitas_periodo.count(),
            'maior_categoria': categorias[0] if categorias else None,
            'categorias': categorias,
            'dados_grafico': _dados_do_grafico(
                receitas_periodo,
                periodo,
                inicio,
                quantidade_periodos,
            ),
            'receitas_paginadas': receitas_paginadas,
        },
    )


@require_POST
def excluir_receita(request, receita_id):
    receita = get_object_or_404(Receita, pk=receita_id, usuario=request.user)
    receita.delete()
    messages.success(request, 'Receita removida.')
    periodo = request.POST.get('periodo', '12m')
    if periodo not in ('30d', '3m', '6m', '12m'):
        periodo = '12m'
    return redirect(f"{reverse('receitas')}?periodo={periodo}")


@require_http_methods(['GET', 'POST'])
def despesas(request):
    hoje = timezone.localdate()
    periodo = request.GET.get('periodo', '12m')
    if periodo not in ('30d', '3m', '6m', '12m'):
        periodo = '12m'
    inicio, quantidade_meses = _inicio_do_periodo(periodo, hoje)
    despesa_edicao = None
    if request.GET.get('editar'):
        despesa_edicao = get_object_or_404(
            Despesa,
            pk=request.GET['editar'],
            usuario=request.user,
        )

    formulario = FormularioDespesa(request.POST or None, instance=despesa_edicao)
    if request.method == 'POST' and formulario.is_valid():
        despesa = formulario.save(commit=False)
        despesa.usuario = request.user
        despesa.save()
        messages.success(
            request,
            'Despesa atualizada com sucesso.' if despesa_edicao else 'Despesa registrada com sucesso.',
        )
        return redirect(f"{reverse('despesas')}?periodo={periodo}")

    despesas_periodo = Despesa.objects.filter(
        usuario=request.user,
        data__gte=inicio,
        data__lte=hoje,
    )
    total = despesas_periodo.aggregate(total=Sum('valor'))['total'] or Decimal('0.00')
    quantidade_periodos = 1 if periodo == '30d' else quantidade_meses
    orcamento = Decimal('0.00')
    renda = Decimal('0.00')
    perfil = PerfilFinanceiro.objects.filter(usuario=request.user).first()
    if perfil:
        orcamento = perfil.despesas_mensais * quantidade_periodos
        renda = perfil.renda_mensal * quantidade_periodos

    percentual_orcamento = int(total * 100 / orcamento) if orcamento else None
    largura_orcamento = min(100, percentual_orcamento or 0)
    saldo = renda - total

    categorias = []
    for item in despesas_periodo.values('categoria').annotate(total=Sum('valor'), quantidade=Count('id')).order_by('-total'):
        valor_categoria = item['total'] or Decimal('0.00')
        percentual = int(valor_categoria * 100 / total) if total else 0
        categorias.append({
            'nome': item['categoria'],
            'valor': _formatar_real(valor_categoria),
            'percentual': percentual,
            'quantidade': item['quantidade'],
            'largura': min(100, percentual),
            'status': 'Principal' if not categorias else 'Outra categoria',
        })

    despesas_paginadas = Paginator(despesas_periodo, 20).get_page(request.GET.get('pagina'))
    contexto = {
        'formulario': formulario,
        'edit_id': despesa_edicao.pk if despesa_edicao else None,
        'periodo': periodo,
        'periodo_rotulo': {
            '30d': 'Últimos 30 dias',
            '3m': 'Últimos 3 meses',
            '6m': 'Últimos 6 meses',
            '12m': 'Últimos 12 meses',
        }[periodo],
        'total_despesas': _formatar_real(total),
        'media_mensal': _formatar_real(total / quantidade_periodos),
        'percentual_orcamento': percentual_orcamento,
        'largura_orcamento': largura_orcamento,
        'situacao_orcamento': (
            'Defina seu orçamento no perfil'
            if percentual_orcamento is None
            else 'Orçamento ultrapassado'
            if percentual_orcamento > 100
            else 'Dentro do orçamento'
        ),
        'orcamento_mensal': _formatar_real(perfil.despesas_mensais) if perfil else None,
        'saldo_periodo': _formatar_real(saldo),
        'quantidade_despesas': despesas_periodo.count(),
        'quantidade_pendentes': despesas_periodo.filter(status='pendente').count(),
        'maior_categoria': categorias[0] if categorias else None,
        'categorias': categorias,
        'dados_grafico': _dados_do_grafico(
            despesas_periodo,
            periodo,
            inicio,
            quantidade_periodos,
        ),
        'despesas_paginadas': despesas_paginadas,
    }
    return render(request, 'despesas.html', contexto)


@require_POST
def excluir_despesa(request, despesa_id):
    despesa = get_object_or_404(Despesa, pk=despesa_id, usuario=request.user)
    despesa.delete()
    messages.success(request, 'Despesa removida.')
    periodo = request.POST.get('periodo', '12m')
    if periodo not in ('30d', '3m', '6m', '12m'):
        periodo = '12m'
    return redirect(f"{reverse('despesas')}?periodo={periodo}")


@require_POST
def excluir_investimento(request, investimento_id):
    investimento = get_object_or_404(
        Investimento,
        pk=investimento_id,
        usuario=request.user,
    )
    investimento.delete()
    messages.success(request, 'Investimento removido.')
    return redirect('investimentos')


def _destaques_b3(ativos):
    destaques = []
    for ativo in ativos:
        try:
            variacao = float(ativo.get('change'))
            preco = float(ativo.get('close'))
        except (TypeError, ValueError):
            continue
        if variacao > 0 and preco > 0:
            destaques.append({**ativo, 'variacao_numero': variacao, 'preco_numero': preco})
    return sorted(
        destaques,
        key=lambda ativo: ativo['variacao_numero'],
        reverse=True,
    )[:3]


@require_http_methods(['GET', 'POST'])
def investimentos(request):
    investimento_edicao = None
    if request.GET.get('editar'):
        investimento_edicao = get_object_or_404(
            Investimento,
            pk=request.GET['editar'],
            usuario=request.user,
        )
    formulario = FormularioInvestimento(
        request.POST or None,
        instance=investimento_edicao,
    )
    if request.method == 'POST' and formulario.is_valid():
        investimento = formulario.save(commit=False)
        investimento.usuario = request.user
        investimento.save()
        messages.success(
            request,
            'Investimento atualizado com sucesso.'
            if investimento_edicao
            else 'Investimento registrado com sucesso.',
        )
        return redirect('investimentos')

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

    carteira = Investimento.objects.filter(usuario=request.user)
    valores = carteira.aggregate(
        total_aplicado=Sum('valor_aplicado'),
        total_atual=Sum('valor_atual'),
    )
    total_aplicado = valores['total_aplicado'] or Decimal('0.00')
    total_atual = valores['total_atual'] or Decimal('0.00')
    resultado = total_atual - total_aplicado
    rentabilidade = resultado * 100 / total_aplicado if total_aplicado else None
    tipos = dict(Investimento.TIPO_CHOICES)
    distribuicao = []
    for item in carteira.values('tipo').annotate(total=Sum('valor_atual')).order_by('-total'):
        percentual = int(item['total'] * 100 / total_atual) if total_atual else 0
        distribuicao.append({
            'nome': tipos.get(item['tipo'], item['tipo']),
            'valor': _formatar_real(item['total']),
            'percentual': percentual,
            'largura': min(100, percentual),
        })

    return render(
        request,
        'investimentos.html',
        {
            'formulario': formulario,
            'edit_id': investimento_edicao.pk if investimento_edicao else None,
            'ativos_b3': ativos,
            'destaques_b3': _destaques_b3(ativos),
            'erro_cotacoes': erro_cotacoes,
            'consulta_cotacoes': timezone.localtime(),
            'carteira': Paginator(carteira, 20).get_page(request.GET.get('pagina')),
            'quantidade_investimentos': carteira.count(),
            'total_aplicado': _formatar_real(total_aplicado),
            'total_atual': _formatar_real(total_atual),
            'resultado_carteira': _formatar_real(resultado),
            'rentabilidade': f'{rentabilidade:.2f}%' if rentabilidade is not None else None,
            'distribuicao': distribuicao,
        },
    )

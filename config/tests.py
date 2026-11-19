from datetime import timedelta
import json
from io import BytesIO
from unittest.mock import patch
from urllib.error import URLError

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from model.despesa import Despesa
from model.investimento import Investimento
from model.perfil_financeiro import PerfilFinanceiro
from model.receita import Receita


class TestesDeAutenticacao(TestCase):
    def test_paginas_financeiras_pedem_login(self):
        for pagina in ('dashboard', 'receitas', 'despesas', 'investimentos'):
            with self.subTest(pagina=pagina):
                resposta = self.client.get(reverse(pagina))
                self.assertEqual(resposta.status_code, 302)
                self.assertIn(reverse('entrar'), resposta.url)

    def test_cadastro_cria_conta_e_abre_dashboard(self):
        resposta = self.client.post(
            reverse('cadastrar'),
            {
                'nome': 'Ana',
                'sobrenome': 'Silva',
                'email': 'ana@example.com',
                'senha': 'Sup3r!Secure#Pass890',
                'confirmar_senha': 'Sup3r!Secure#Pass890',
            },
        )

        self.assertRedirects(resposta, reverse('questionario'))
        usuario = get_user_model().objects.get(email='ana@example.com')
        self.assertTrue(usuario.check_password('Sup3r!Secure#Pass890'))
        self.assertEqual(self.client.get(reverse('questionario')).status_code, 200)

    def test_dashboard_tem_botao_de_troca_de_tema(self):
        usuario = get_user_model().objects.create_user(
            username='ana@example.com',
            email='ana@example.com',
            password='Sup3r!Secure#Pass890',
        )
        PerfilFinanceiro.objects.create(
            usuario=usuario,
            renda_mensal='5000.00',
            despesas_mensais='3000.00',
            investimentos='10000.00',
            objetivo='reserva',
        )
        self.client.force_login(usuario)

        resposta = self.client.get(reverse('dashboard'))

        self.assertContains(resposta, 'data-botao-tema')
        self.assertContains(resposta, 'role="switch"')
        self.assertContains(resposta, 'bi-moon-stars-fill')

    def test_dashboard_usa_carteira_registrada_quando_existir(self):
        usuario = get_user_model().objects.create_user(
            username='ana@example.com',
            email='ana@example.com',
            password='Sup3r!Secure#Pass890',
        )
        PerfilFinanceiro.objects.create(
            usuario=usuario,
            renda_mensal='5000.00',
            despesas_mensais='3000.00',
            investimentos='10000.00',
            objetivo='reserva',
        )
        Investimento.objects.create(
            usuario=usuario,
            ativo='CDB',
            tipo='renda_fixa',
            valor_aplicado='10000.00',
            valor_atual='12000.00',
            data_aplicacao=timezone.localdate(),
        )
        self.client.force_login(usuario)

        resposta = self.client.get(reverse('dashboard'))

        self.assertContains(resposta, 'R$ 12.000,00')
        self.assertContains(resposta, 'Valor atual da carteira registrada')

    def test_dashboard_usa_receitas_e_despesas_lancadas_no_mes(self):
        usuario = get_user_model().objects.create_user(
            username='ana@example.com',
            email='ana@example.com',
            password='Sup3r!Secure#Pass890',
        )
        PerfilFinanceiro.objects.create(
            usuario=usuario,
            renda_mensal='5000.00',
            despesas_mensais='3000.00',
            investimentos='10000.00',
            objetivo='reserva',
        )
        Receita.objects.create(
            usuario=usuario,
            descricao='Pagamento',
            categoria='Salário',
            valor='4200.00',
            data=timezone.localdate(),
        )
        Despesa.objects.create(
            usuario=usuario,
            descricao='Aluguel',
            categoria='Moradia',
            valor='1500.00',
            data=timezone.localdate(),
            status='pago',
        )
        self.client.force_login(usuario)

        resposta = self.client.get(reverse('dashboard'))

        self.assertContains(resposta, 'R$ 4.200,00')
        self.assertContains(resposta, 'R$ 1.500,00')
        self.assertContains(resposta, 'R$ 2.700,00')
        self.assertContains(resposta, 'Soma das receitas lançadas neste mês')

    def test_questionario_personaliza_dashboard(self):
        usuario = get_user_model().objects.create_user(
            username='ana@example.com',
            email='ana@example.com',
            password='Sup3r!Secure#Pass890',
        )
        self.client.force_login(usuario)

        resposta = self.client.post(
            reverse('questionario'),
            {
                'renda_mensal': '5000.00',
                'despesas_mensais': '3200.00',
                'investimentos': '12000.00',
                'objetivo': 'casa',
            },
        )

        self.assertRedirects(resposta, reverse('dashboard'))
        perfil = PerfilFinanceiro.objects.get(usuario=usuario)
        self.assertEqual(perfil.renda_mensal, 5000)
        resposta = self.client.get(reverse('dashboard'))
        self.assertContains(resposta, 'R$ 5.000,00')
        self.assertContains(resposta, 'R$ 3.200,00')
        self.assertContains(resposta, 'R$ 1.800,00')
        self.assertContains(resposta, 'Comprar uma casa')

    def test_dashboard_sem_perfil_abre_questionario(self):
        usuario = get_user_model().objects.create_user(
            username='ana@example.com',
            email='ana@example.com',
            password='Sup3r!Secure#Pass890',
        )
        self.client.force_login(usuario)

        resposta = self.client.get(reverse('dashboard'))

        self.assertRedirects(resposta, reverse('questionario'))

    def test_usuario_pode_atualizar_respostas(self):
        usuario = get_user_model().objects.create_user(
            username='ana@example.com',
            email='ana@example.com',
            password='Sup3r!Secure#Pass890',
        )
        PerfilFinanceiro.objects.create(
            usuario=usuario,
            renda_mensal='5000.00',
            despesas_mensais='3000.00',
            investimentos='10000.00',
            objetivo='reserva',
        )
        self.client.force_login(usuario)

        resposta = self.client.post(
            reverse('questionario'),
            {
                'renda_mensal': '6000.00',
                'despesas_mensais': '3500.00',
                'investimentos': '15000.00',
                'objetivo': 'investir',
            },
        )

        self.assertRedirects(resposta, reverse('dashboard'))
        perfil = PerfilFinanceiro.objects.get(usuario=usuario)
        self.assertEqual(perfil.renda_mensal, 6000)
        self.assertEqual(perfil.objetivo, 'investir')

    def test_senhas_diferentes_nao_criam_conta(self):
        resposta = self.client.post(
            reverse('cadastrar'),
            {
                'nome': 'Ana',
                'email': 'ana@example.com',
                'senha': 'Sup3r!Secure#Pass890',
                'confirmar_senha': 'outra-senha',
            },
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertFalse(get_user_model().objects.filter(email='ana@example.com').exists())

    def test_login_e_sair(self):
        usuario = get_user_model().objects.create_user(
            username='ana@example.com',
            email='ana@example.com',
            password='Sup3r!Secure#Pass890',
        )

        resposta = self.client.post(
            reverse('entrar'),
            {'email': 'ana@example.com', 'senha': 'Sup3r!Secure#Pass890'},
        )
        self.assertRedirects(resposta, reverse('questionario'))
        PerfilFinanceiro.objects.create(
            usuario=usuario,
            renda_mensal='5000.00',
            despesas_mensais='3000.00',
            investimentos='10000.00',
            objetivo='reserva',
        )
        self.client.logout()

        resposta = self.client.post(
            reverse('entrar'),
            {'email': 'ana@example.com', 'senha': 'Sup3r!Secure#Pass890'},
        )
        self.assertRedirects(resposta, reverse('dashboard'))
        self.assertEqual(self.client.get(reverse('dashboard')).status_code, 200)

        resposta = self.client.post(reverse('sair'))
        self.assertRedirects(resposta, reverse('entrar'))
        self.assertEqual(self.client.get(reverse('dashboard')).status_code, 302)

    def test_senha_errada_nao_entra(self):
        get_user_model().objects.create_user(
            username='ana@example.com',
            email='ana@example.com',
            password='Sup3r!Secure#Pass890',
        )

        self.client.post(
            reverse('entrar'),
            {'email': 'ana@example.com', 'senha': 'senha-errada'},
        )

        self.assertEqual(self.client.get(reverse('dashboard')).status_code, 302)


class TestesDeCotacoes(TestCase):
    def setUp(self):
        usuario = get_user_model().objects.create_user(
            username='ana@example.com',
            email='ana@example.com',
            password='Sup3r!Secure#Pass890',
        )
        self.client.force_login(usuario)
        cache.delete('cotacoes_b3')

    @patch('config.views.urlopen')
    def test_mostra_cotacoes_recebidas_da_api(self, abrir_api):
        abrir_api.return_value = BytesIO(
            json.dumps(
                {
                    'stocks': [
                        {
                            'stock': 'PETR4',
                            'name': 'Petrobras',
                            'close': 43.17,
                            'change': -1.84,
                            'sector': 'Energia',
                        }
                    ]
                }
            ).encode()
        )

        resposta = self.client.get(reverse('investimentos'))

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, 'PETR4')
        self.assertContains(resposta, '43,17')
        self.assertContains(resposta, 'Petrobras')

    @patch('config.views.urlopen', side_effect=URLError('sem conexão'))
    def test_avisa_quando_api_nao_responde(self, abrir_api):
        resposta = self.client.get(reverse('investimentos'))

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, 'Não foi possível carregar as cotações agora')


class TestesDeDespesas(TestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_user(
            username='ana@example.com',
            email='ana@example.com',
            password='Sup3r!Secure#Pass890',
        )
        PerfilFinanceiro.objects.create(
            usuario=self.usuario,
            renda_mensal='5000.00',
            despesas_mensais='3000.00',
            investimentos='10000.00',
            objetivo='reserva',
        )
        self.client.force_login(self.usuario)

    def criar_despesa(self, usuario=None, descricao='Conta de luz', data=None):
        return Despesa.objects.create(
            usuario=usuario or self.usuario,
            descricao=descricao,
            categoria='Contas',
            valor='180.50',
            data=data or timezone.localdate(),
            status='pago',
        )

    def test_painel_mostra_apenas_despesas_da_conta_e_valores_reais(self):
        self.criar_despesa()
        outro_usuario = get_user_model().objects.create_user(
            username='bia@example.com',
            email='bia@example.com',
            password='Sup3r!Secure#Pass890',
        )
        self.criar_despesa(usuario=outro_usuario, descricao='Despesa privada')

        resposta = self.client.get(reverse('despesas'))

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, 'R$ 180,50')
        self.assertContains(resposta, 'Conta de luz')
        self.assertNotContains(resposta, 'Despesa privada')
        self.assertContains(resposta, 'Evolução das despesas')

    def test_nova_despesa_e_salva_para_o_usuario_logado(self):
        resposta = self.client.post(
            reverse('despesas') + '?periodo=3m',
            {
                'descricao': 'Mercado',
                'categoria': 'Alimentação',
                'valor': '245.90',
                'data': timezone.localdate().isoformat(),
                'status': 'pendente',
                'observacao': 'Compra semanal',
                'periodo': '3m',
            },
        )

        self.assertRedirects(resposta, f"{reverse('despesas')}?periodo=3m")
        despesa = Despesa.objects.get(descricao='Mercado')
        self.assertEqual(despesa.usuario, self.usuario)
        self.assertEqual(despesa.status, 'pendente')

    def test_valor_invalido_nao_cria_despesa_e_mostra_erro(self):
        resposta = self.client.post(
            reverse('despesas'),
            {
                'descricao': 'Valor inválido',
                'categoria': 'Outros',
                'valor': '0',
                'data': timezone.localdate().isoformat(),
                'status': 'pago',
            },
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertTrue(resposta.context['formulario'].errors)
        self.assertFalse(Despesa.objects.filter(descricao='Valor inválido').exists())

    def test_usuario_nao_consegue_excluir_despesa_de_outra_conta(self):
        outro_usuario = get_user_model().objects.create_user(
            username='bia@example.com',
            email='bia@example.com',
            password='Sup3r!Secure#Pass890',
        )
        despesa = self.criar_despesa(usuario=outro_usuario)

        resposta = self.client.post(
            reverse('excluir_despesa', args=[despesa.pk]),
            {'periodo': '6m'},
        )

        self.assertEqual(resposta.status_code, 404)
        self.assertTrue(Despesa.objects.filter(pk=despesa.pk).exists())

    def test_usuario_consegue_excluir_propria_despesa(self):
        despesa = self.criar_despesa()

        resposta = self.client.post(
            reverse('excluir_despesa', args=[despesa.pk]),
            {'periodo': '6m'},
        )

        self.assertRedirects(resposta, f"{reverse('despesas')}?periodo=6m")
        self.assertFalse(Despesa.objects.filter(pk=despesa.pk).exists())

    def test_usuario_consegue_editar_propria_despesa(self):
        despesa = self.criar_despesa()

        resposta = self.client.post(
            f"{reverse('despesas')}?periodo=3m&editar={despesa.pk}",
            {
                'descricao': 'Conta atualizada',
                'categoria': 'Contas',
                'valor': '200.00',
                'data': timezone.localdate().isoformat(),
                'status': 'pendente',
                'observacao': '',
                'periodo': '3m',
            },
        )

        self.assertRedirects(resposta, f"{reverse('despesas')}?periodo=3m")
        despesa.refresh_from_db()
        self.assertEqual(despesa.descricao, 'Conta atualizada')
        self.assertEqual(despesa.valor, 200)

    def test_filtro_de_periodo_exclui_lancamentos_antigos(self):
        self.criar_despesa(descricao='Despesa antiga', data=timezone.localdate() - timedelta(days=45))
        self.criar_despesa(descricao='Despesa recente')

        resposta = self.client.get(reverse('despesas'), {'periodo': '30d'})

        self.assertContains(resposta, 'Despesa recente')
        self.assertNotContains(resposta, 'Despesa antiga')

    def test_nao_aceita_data_futura(self):
        resposta = self.client.post(
            reverse('despesas'),
            {
                'descricao': 'Despesa futura',
                'categoria': 'Outros',
                'valor': '40.00',
                'data': (timezone.localdate() + timedelta(days=1)).isoformat(),
                'status': 'pendente',
            },
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, 'A data da despesa não pode ser futura.')
        self.assertFalse(Despesa.objects.filter(descricao='Despesa futura').exists())


class TestesDeReceitas(TestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_user(
            username='ana@example.com',
            email='ana@example.com',
            password='Sup3r!Secure#Pass890',
        )
        PerfilFinanceiro.objects.create(
            usuario=self.usuario,
            renda_mensal='5000.00',
            despesas_mensais='3000.00',
            investimentos='10000.00',
            objetivo='reserva',
        )
        self.client.force_login(self.usuario)

    def criar_receita(self, usuario=None, descricao='Salário'):
        return Receita.objects.create(
            usuario=usuario or self.usuario,
            descricao=descricao,
            categoria='Salário',
            valor='1250.75',
            data=timezone.localdate(),
        )

    def test_painel_mostra_receitas_reais_e_apenas_da_conta(self):
        self.criar_receita()
        outro_usuario = get_user_model().objects.create_user(
            username='bia@example.com',
            email='bia@example.com',
            password='Sup3r!Secure#Pass890',
        )
        self.criar_receita(usuario=outro_usuario, descricao='Receita privada')

        resposta = self.client.get(reverse('receitas'))

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, 'R$ 1.250,75')
        self.assertContains(resposta, 'Evolução das receitas')
        self.assertNotContains(resposta, 'Receita privada')
        self.assertNotContains(resposta, 'R$ 28.450')

    def test_nova_receita_e_salva_para_o_usuario_logado(self):
        resposta = self.client.post(
            reverse('receitas') + '?periodo=3m',
            {
                'descricao': 'Serviço de design',
                'categoria': 'Trabalho autônomo',
                'valor': '750.00',
                'data': timezone.localdate().isoformat(),
                'observacao': 'Projeto entregue',
                'periodo': '3m',
            },
        )

        self.assertRedirects(resposta, f"{reverse('receitas')}?periodo=3m")
        receita = Receita.objects.get(descricao='Serviço de design')
        self.assertEqual(receita.usuario, self.usuario)
        self.assertEqual(receita.categoria, 'Trabalho autônomo')

    def test_usuario_nao_consegue_excluir_receita_de_outra_conta(self):
        outro_usuario = get_user_model().objects.create_user(
            username='bia@example.com',
            email='bia@example.com',
            password='Sup3r!Secure#Pass890',
        )
        receita = self.criar_receita(usuario=outro_usuario)

        resposta = self.client.post(
            reverse('excluir_receita', args=[receita.pk]),
            {'periodo': '6m'},
        )

        self.assertEqual(resposta.status_code, 404)
        self.assertTrue(Receita.objects.filter(pk=receita.pk).exists())

    def test_usuario_consegue_excluir_propria_receita(self):
        receita = self.criar_receita()

        resposta = self.client.post(
            reverse('excluir_receita', args=[receita.pk]),
            {'periodo': '3m'},
        )

        self.assertRedirects(resposta, f"{reverse('receitas')}?periodo=3m")
        self.assertFalse(Receita.objects.filter(pk=receita.pk).exists())

    def test_usuario_consegue_editar_propria_receita(self):
        receita = self.criar_receita()

        resposta = self.client.post(
            f"{reverse('receitas')}?periodo=3m&editar={receita.pk}",
            {
                'descricao': 'Salário atualizado',
                'categoria': 'Salário',
                'valor': '2000.00',
                'data': timezone.localdate().isoformat(),
                'observacao': '',
                'periodo': '3m',
            },
        )

        self.assertRedirects(resposta, f"{reverse('receitas')}?periodo=3m")
        receita.refresh_from_db()
        self.assertEqual(receita.descricao, 'Salário atualizado')
        self.assertEqual(receita.valor, 2000)

    def test_nao_aceita_receita_com_valor_zero(self):
        resposta = self.client.post(
            reverse('receitas'),
            {
                'descricao': 'Valor inválido',
                'categoria': 'Outros',
                'valor': '0',
                'data': timezone.localdate().isoformat(),
            },
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertTrue(resposta.context['formulario'].errors)
        self.assertFalse(Receita.objects.filter(descricao='Valor inválido').exists())


class TestesDeInvestimentosPessoais(TestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_user(
            username='ana@example.com',
            email='ana@example.com',
            password='Sup3r!Secure#Pass890',
        )
        self.client.force_login(self.usuario)
        cache.set('cotacoes_b3', [], 300)

    def criar_investimento(self, usuario=None, ativo='CDB'):
        return Investimento.objects.create(
            usuario=usuario or self.usuario,
            ativo=ativo,
            tipo='renda_fixa',
            valor_aplicado='1000.00',
            valor_atual='1200.00',
            data_aplicacao=timezone.localdate(),
        )

    def test_carteira_mostra_valores_calculados_da_conta(self):
        self.criar_investimento()

        resposta = self.client.get(reverse('investimentos'))

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, 'Minha carteira')
        self.assertContains(resposta, 'R$ 1.200,00')
        self.assertContains(resposta, '20.00%')
        self.assertNotContains(resposta, 'R$ 184.250')

    def test_novo_investimento_e_salvo_para_o_usuario_logado(self):
        resposta = self.client.post(
            reverse('investimentos'),
            {
                'ativo': 'PETR4',
                'tipo': 'acoes',
                'valor_aplicado': '500.00',
                'valor_atual': '550.00',
                'data_aplicacao': timezone.localdate().isoformat(),
            },
        )

        self.assertRedirects(resposta, reverse('investimentos'))
        investimento = Investimento.objects.get(ativo='PETR4')
        self.assertEqual(investimento.usuario, self.usuario)
        self.assertEqual(investimento.rentabilidade, 10)

    def test_usuario_nao_consegue_excluir_investimento_de_outra_conta(self):
        outro_usuario = get_user_model().objects.create_user(
            username='bia@example.com',
            email='bia@example.com',
            password='Sup3r!Secure#Pass890',
        )
        investimento = self.criar_investimento(usuario=outro_usuario)

        resposta = self.client.post(
            reverse('excluir_investimento', args=[investimento.pk]),
        )

        self.assertEqual(resposta.status_code, 404)
        self.assertTrue(Investimento.objects.filter(pk=investimento.pk).exists())

    def test_usuario_consegue_excluir_proprio_investimento(self):
        investimento = self.criar_investimento()

        resposta = self.client.post(
            reverse('excluir_investimento', args=[investimento.pk]),
        )

        self.assertRedirects(resposta, reverse('investimentos'))
        self.assertFalse(Investimento.objects.filter(pk=investimento.pk).exists())

    def test_usuario_consegue_editar_proprio_investimento(self):
        investimento = self.criar_investimento()

        resposta = self.client.post(
            f"{reverse('investimentos')}?editar={investimento.pk}",
            {
                'ativo': 'CDB atualizado',
                'tipo': 'renda_fixa',
                'valor_aplicado': '1100.00',
                'valor_atual': '1300.00',
                'data_aplicacao': timezone.localdate().isoformat(),
            },
        )

        self.assertRedirects(resposta, reverse('investimentos'))
        investimento.refresh_from_db()
        self.assertEqual(investimento.ativo, 'CDB atualizado')
        self.assertEqual(investimento.valor_aplicado, 1100)

    def test_nao_aceita_aplicacao_com_valor_zero(self):
        resposta = self.client.post(
            reverse('investimentos'),
            {
                'ativo': 'PETR4',
                'tipo': 'acoes',
                'valor_aplicado': '0',
                'valor_atual': '0',
                'data_aplicacao': timezone.localdate().isoformat(),
            },
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertTrue(resposta.context['formulario'].errors)
        self.assertFalse(Investimento.objects.filter(ativo='PETR4').exists())

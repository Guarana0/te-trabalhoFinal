import json
from io import BytesIO
from unittest.mock import patch
from urllib.error import URLError

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse


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

        self.assertRedirects(resposta, reverse('dashboard'))
        usuario = get_user_model().objects.get(email='ana@example.com')
        self.assertTrue(usuario.check_password('Sup3r!Secure#Pass890'))
        self.assertEqual(self.client.get(reverse('dashboard')).status_code, 200)

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
        get_user_model().objects.create_user(
            username='ana@example.com',
            email='ana@example.com',
            password='Sup3r!Secure#Pass890',
        )

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

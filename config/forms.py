from decimal import Decimal

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from model.despesa import Despesa
from model.investimento import Investimento
from model.perfil_financeiro import PerfilFinanceiro
from model.receita import Receita


class FormularioReceita(forms.ModelForm):
    valor = forms.DecimalField(
        min_value=Decimal('0.01'),
        max_digits=10,
        decimal_places=2,
        label='Valor',
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '0.01', 'step': '0.01'}),
    )

    class Meta:
        model = Receita
        fields = ('descricao', 'categoria', 'valor', 'data', 'observacao')
        labels = {
            'descricao': 'De onde veio esse dinheiro?',
            'categoria': 'Categoria',
            'data': 'Data',
            'observacao': 'Observação (opcional)',
        }
        widgets = {
            'descricao': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 150}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'data': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'observacao': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['data'].initial = timezone.localdate()

    def clean_data(self):
        data = self.cleaned_data['data']
        if data > timezone.localdate():
            raise ValidationError('A data da receita não pode ser futura.')
        return data


class FormularioInvestimento(forms.ModelForm):
    valor_aplicado = forms.DecimalField(
        min_value=Decimal('0.01'),
        max_digits=12,
        decimal_places=2,
        label='Valor aplicado',
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '0.01', 'step': '0.01'}),
    )
    valor_atual = forms.DecimalField(
        min_value=Decimal('0'),
        max_digits=12,
        decimal_places=2,
        label='Valor atual',
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
    )

    class Meta:
        model = Investimento
        fields = ('ativo', 'tipo', 'valor_aplicado', 'valor_atual', 'data_aplicacao')
        labels = {
            'ativo': 'Nome ou código do ativo',
            'tipo': 'Tipo de investimento',
            'data_aplicacao': 'Data da aplicação',
        }
        widgets = {
            'ativo': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 100}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'data_aplicacao': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['data_aplicacao'].initial = timezone.localdate()

    def clean_data_aplicacao(self):
        data = self.cleaned_data['data_aplicacao']
        if data > timezone.localdate():
            raise ValidationError('A data da aplicação não pode ser futura.')
        return data


class FormularioDespesa(forms.ModelForm):
    valor = forms.DecimalField(
        min_value=Decimal('0.01'),
        max_digits=10,
        decimal_places=2,
        label='Valor',
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '0.01', 'step': '0.01'}),
    )

    class Meta:
        model = Despesa
        fields = ('descricao', 'categoria', 'valor', 'data', 'status', 'observacao')
        labels = {
            'descricao': 'O que você pagou?',
            'categoria': 'Categoria',
            'valor': 'Valor',
            'data': 'Data',
            'status': 'Situação',
            'observacao': 'Observação (opcional)',
        }
        widgets = {
            'descricao': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 150}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'data': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date'},
                format='%Y-%m-%d',
            ),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'observacao': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['data'].initial = timezone.localdate()

    def clean_data(self):
        data = self.cleaned_data['data']
        if data > timezone.localdate():
            raise ValidationError('A data da despesa não pode ser futura.')
        return data


class FormularioPerfilFinanceiro(forms.ModelForm):
    class Meta:
        model = PerfilFinanceiro
        fields = (
            'renda_mensal',
            'despesas_mensais',
            'investimentos',
            'objetivo',
        )
        labels = {
            'renda_mensal': 'Quanto você recebe por mês?',
            'despesas_mensais': 'Quanto gasta por mês?',
            'investimentos': 'Quanto já tem investido?',
            'objetivo': 'Qual é seu principal objetivo financeiro?',
        }
        help_texts = {
            'renda_mensal': 'Salário e outras entradas em um mês comum.',
            'despesas_mensais': 'Uma estimativa do que costuma gastar por mês.',
            'investimentos': 'O valor aproximado da sua carteira hoje.',
            'objetivo': 'Escolha o que mais importa para você neste momento.',
        }
        widgets = {
            'renda_mensal': forms.NumberInput(attrs={'min': '0', 'step': '0.01', 'class': 'form-control form-control-lg'}),
            'despesas_mensais': forms.NumberInput(attrs={'min': '0', 'step': '0.01', 'class': 'form-control form-control-lg'}),
            'investimentos': forms.NumberInput(attrs={'min': '0', 'step': '0.01', 'class': 'form-control form-control-lg'}),
            'objetivo': forms.Select(attrs={'class': 'form-select'}),
        }

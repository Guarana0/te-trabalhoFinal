from django import forms

from model.perfil_financeiro import PerfilFinanceiro


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
        widgets = {
            'renda_mensal': forms.NumberInput(attrs={'min': '0', 'step': '0.01', 'class': 'form-control'}),
            'despesas_mensais': forms.NumberInput(attrs={'min': '0', 'step': '0.01', 'class': 'form-control'}),
            'investimentos': forms.NumberInput(attrs={'min': '0', 'step': '0.01', 'class': 'form-control'}),
            'objetivo': forms.Select(attrs={'class': 'form-select'}),
        }

from django.db import models
from django.conf import settings


class Investimento(models.Model):
    TIPO_CHOICES = [
        ('renda_fixa', 'Renda Fixa'),
        ('acoes', 'Ações'),
        ('fiis', 'Fundos Imobiliários'),
        ('cripto', 'Criptomoedas'),
        ('outros', 'Outros'),
    ]

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='investimentos',
        db_column='usuario_id'
    )
    ativo = models.CharField(max_length=100)
    tipo = models.CharField(max_length=30, choices=TIPO_CHOICES, default='renda_fixa')
    valor_aplicado = models.DecimalField(max_digits=12, decimal_places=2)
    valor_atual = models.DecimalField(max_digits=12, decimal_places=2)
    data_aplicacao = models.DateField()
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'investimentos'
        ordering = ['-data_aplicacao']

    @property
    def rentabilidade(self):
        if self.valor_aplicado > 0:
            return ((self.valor_atual - self.valor_aplicado) / self.valor_aplicado) * 100
        return 0

    def __str__(self):
        return f"{self.ativo} ({self.get_tipo_display()})"

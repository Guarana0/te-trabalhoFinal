from django.conf import settings
from django.db import models


class PerfilFinanceiro(models.Model):
    id = models.AutoField(primary_key=True)

    OBJETIVOS = [
        ('reserva', 'Montar uma reserva de emergência'),
        ('dividas', 'Quitar dívidas'),
        ('casa', 'Comprar uma casa'),
        ('investir', 'Investir para o futuro'),
        ('outro', 'Outro objetivo'),
    ]

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='perfil_financeiro',
    )
    renda_mensal = models.DecimalField(max_digits=12, decimal_places=2)
    despesas_mensais = models.DecimalField(max_digits=12, decimal_places=2)
    investimentos = models.DecimalField(max_digits=12, decimal_places=2)
    objetivo = models.CharField(max_length=20, choices=OBJETIVOS)

    class Meta:
        db_table = 'perfis_financeiros'

    def __str__(self):
        return f'Perfil financeiro de {self.usuario}'

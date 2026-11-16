from django.db import models
from .usuario import Usuario


class Despesa(models.Model):
    STATUS_CHOICES = [
        ('pago', 'Pago'),
        ('pendente', 'Pendente'),
    ]

    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='despesas',
        db_column='usuario_id'
    )
    descricao = models.CharField(max_length=150)
    categoria = models.CharField(max_length=80)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    data = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pago')
    observacao = models.TextField(null=True, blank=True)
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'despesas'
        ordering = ['-data']

    def __str__(self):
        return f"{self.descricao} - R$ {self.valor}"

from django.db import models
from django.conf import settings


class Receita(models.Model):
    CATEGORIAS = [
        ('Salário', 'Salário'),
        ('Trabalho autônomo', 'Trabalho autônomo'),
        ('Investimentos', 'Investimentos'),
        ('Aluguel', 'Aluguel'),
        ('Benefícios', 'Benefícios'),
        ('Vendas', 'Vendas'),
        ('Outros', 'Outros'),
    ]

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='receitas',
        db_column='usuario_id'
    )
    descricao = models.CharField(max_length=150)
    categoria = models.CharField(max_length=80, choices=CATEGORIAS)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    data = models.DateField()
    observacao = models.TextField(null=True, blank=True)
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'receitas'
        ordering = ['-data']

    def __str__(self):
        return f"{self.descricao} - R$ {self.valor}"

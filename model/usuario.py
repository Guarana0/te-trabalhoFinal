from django.db import models
from django.contrib.auth.hashers import make_password, check_password


class Usuario(models.Model):
    id = models.AutoField(primary_key=True)
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)
    nome = models.CharField(max_length=100)
    sobrenome = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField(max_length=254, unique=True)
    senha = models.CharField(max_length=255)

    class Meta:
        db_table = 'usuarios'
        managed = False  # <--- ADICIONE ESTA LINHA AQUI
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'

    def set_senha(self, raw_password):
        """Gera o hash seguro da senha antes de salvar."""
        self.senha = make_password(raw_password)

    def verificar_senha(self, raw_password):
        """Compara a senha digitada no login com o hash salvo no banco."""
        return check_password(raw_password, self.senha)

    def __str__(self):
        return f"{self.nome} {self.sobrenome or ''}".strip()
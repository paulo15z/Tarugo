from django.db import models
from django.contrib.auth import get_user_model

from apps.estoque.models.produto import Produto

User = get_user_model()


class Reserva(models.Model):
    STATUS_CHOICES = [
        ('ativa', 'Ativa'),
        ('consumida', 'Consumida'),
        ('cancelada', 'Cancelada'),
    ]

    produto = models.ForeignKey(Produto, on_delete=models.CASCADE, related_name='reservas')
    projeto = models.CharField(max_length=255, help_text='Nome ou código do projeto')
    quantidade = models.IntegerField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='ativa')
    observacao = models.TextField(blank=True, null=True)
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reservas')
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-criado_em']
        verbose_name = 'Reserva'
        verbose_name_plural = 'Reservas'

    def __str__(self):
        return f"Reserva {self.quantidade}x {self.produto.nome} → {self.projeto} [{self.status}]"

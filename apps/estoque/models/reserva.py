# apps/estoque/models/reserva.py
from django.db import models
from django.contrib.auth import get_user_model

from apps.estoque.models.produto import Produto
from apps.bipagem.models.pedido import Pedido

User = get_user_model()

STATUS_CHOICES = [
    ('ativa', 'Ativa'),
    ('consumida', 'Consumida'),
    ('cancelada', 'Cancelada'),
]


class Reserva(models.Model):
    produto = models.ForeignKey(
        Produto,
        on_delete=models.CASCADE,
        related_name='reservas',
        verbose_name='Produto',
    )
    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.CASCADE,
        related_name='reservas',
        verbose_name='Pedido/Projeto',
        null=True,
        blank=True
    )
    projeto_legado = models.CharField(
        max_length=255,
        verbose_name='Projeto (Legado)',
        null=True,
        blank=True
    )
    quantidade = models.IntegerField(verbose_name='Quantidade')
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='ativa',
        verbose_name='Status',
    )
    usuario = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reservas',
        verbose_name='Usuário',
    )
    observacao = models.TextField(blank=True, null=True, verbose_name='Observação')
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    atualizado_em = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')

    class Meta:
        verbose_name = 'Reserva'
        verbose_name_plural = 'Reservas'
        ordering = ['-criado_em']

    def __str__(self):
        return f"Reserva {self.projeto} — {self.produto.nome} ({self.quantidade})"
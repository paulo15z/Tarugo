from django.db import models
from django.contrib.auth import get_user_model

from apps.estoque.models.produto import Produto

User = get_user_model()


class Movimentacao(models.Model):
    TIPO_CHOICES = (
        ('entrada', 'Entrada'),
        ('saida', 'Saída'),
        ('ajuste', 'Ajuste'),
        ('transferencia', 'Transferência'),
    )

    produto = models.ForeignKey(Produto, on_delete=models.CASCADE, related_name='movimentacoes')
    tipo = models.CharField(max_length=15, choices=TIPO_CHOICES)
    quantidade = models.IntegerField()
    usuario = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='movimentacoes',
    )
    observacao = models.TextField(blank=True, null=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-criado_em']
        verbose_name = 'Movimentação'
        verbose_name_plural = 'Movimentações'

    def __str__(self):
        usuario_str = self.usuario.username if self.usuario else 'sistema'
        return f"{self.get_tipo_display()} - {self.produto.nome} ({self.quantidade}) por {usuario_str}"

"""
Model HistoricoStatusPedido - Auditoria de transições de status.

Responsabilidade: Registro imutável de mudanças de status.
"""

from django.conf import settings
from django.db import models

from apps.pedidos.models.pedido import Pedido


class HistoricoStatusPedido(models.Model):
    """
    Registro auditável de cada transição de status de um Pedido.
    Permite rastreamento completo do ciclo de vida.
    """

    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.CASCADE,
        related_name="historico_status",
        verbose_name="Pedido",
    )

    status_anterior = models.CharField(
        max_length=32,
        blank=True,
        verbose_name="Status Anterior",
    )
    status_novo = models.CharField(
        max_length=32,
        verbose_name="Status Novo",
    )

    motivo = models.TextField(
        blank=True,
        verbose_name="Motivo da Transição",
    )

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="historicos_pedido_criados",
        verbose_name="Usuário",
    )

    data_criacao = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data da Transição",
    )

    class Meta:
        verbose_name = "Histórico de Status do Pedido"
        verbose_name_plural = "Históricos de Status do Pedido"
        ordering = ["-data_criacao"]
        indexes = [
            models.Index(fields=["pedido", "-data_criacao"], name="hist_ped_dt_idx"),
        ]

    def __str__(self) -> str:
        return f"Pedido {self.pedido.numero_pedido}: {self.status_anterior} → {self.status_novo}"

"""
Model Pedido - Entidade central do ciclo de vida do pedido.

Responsabilidade: Dados + ORM (sem lógica de negócio).
Lógica: Em services/
"""

from django.conf import settings
from django.db import models

from apps.pedidos.domain.status import PedidoStatus


class Pedido(models.Model):
    """
    Entidade central que representa um pedido do cliente.
    Identificador único gerado no Comercial (numero_pedido).

    O Pedido é um "gêmeo digital" evolutivo que se enriquece conforme percorre
    as etapas: Comercial → Engenharia → PCP → Produção → Montagem.
    """

    numero_pedido = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        verbose_name="Número do Pedido",
    )
    customer_id = models.CharField(
        max_length=64,
        db_index=True,
        verbose_name="ID Cliente (Dinabox)",
    )
    cliente_nome = models.CharField(max_length=255, verbose_name="Nome do Cliente")

    # Vínculo com o app Comercial
    cliente_comercial = models.ForeignKey(
        "comercial.ClienteComercial",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pedidos",
        verbose_name="Cliente Comercial",
    )

    # Status do Pedido (ciclo de vida)
    status = models.CharField(
        max_length=32,
        choices=PedidoStatus.choices,
        default=PedidoStatus.CONTRATO_FECHADO,
        db_index=True,
        verbose_name="Status",
    )

    # Datas importantes
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")
    data_contrato = models.DateField(
        null=True,
        blank=True,
        verbose_name="Data do Contrato",
    )
    data_entrega_prevista = models.DateField(
        null=True,
        blank=True,
        verbose_name="Data de Entrega Prevista",
    )
    data_conclusao = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Data de Conclusão",
    )

    # Observações gerenciais
    observacoes = models.TextField(
        blank=True,
        verbose_name="Observações",
    )

    # Auditoria
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pedidos_criados",
    )

    class Meta:
        verbose_name = "Pedido"
        verbose_name_plural = "Pedidos"
        ordering = ["-data_criacao"]
        indexes = [
            models.Index(fields=["numero_pedido", "status"], name="pedido_num_st_idx"),
            models.Index(fields=["customer_id", "status"], name="pedido_cli_st_idx"),
            models.Index(fields=["status", "-data_criacao"], name="pedido_st_dt_idx"),
        ]

    def __str__(self) -> str:
        return f"Pedido {self.numero_pedido} - {self.cliente_nome} ({self.get_status_display()})"

    @property
    def total_ambientes(self) -> int:
        """Retorna o total de ambientes neste pedido."""
        return self.ambientes.count()

    @property
    def ambientes_concluidos(self) -> int:
        """Retorna quantos ambientes estão concluídos."""
        from apps.pedidos.domain.status import AmbienteStatus

        return self.ambientes.filter(status=AmbienteStatus.CONCLUIDO).count()

    @property
    def percentual_conclusao(self) -> float:
        """Retorna o percentual de conclusão (ambientes concluídos / total)."""
        total = self.total_ambientes
        if total == 0:
            return 0.0
        return (self.ambientes_concluidos / total) * 100

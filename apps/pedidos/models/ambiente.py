"""
Model AmbientePedido - Sub-unidade de produção dentro de um pedido.

Responsabilidade: Dados + ORM (sem lógica).
Lógica: Em services/
"""

from django.db import models

from apps.pedidos.domain.status import AmbienteStatus
from apps.pedidos.models.pedido import Pedido


class AmbientePedido(models.Model):
    """
    Ambiente dentro de um pedido (ex: COZINHA, DORMITÓRIO, SALA ÍNTIMA).

    Um Pedido contém múltiplos Ambientes. Cada ambiente herda dados do
    AmbienteOrcamento (Comercial) e é expandido progressivamente:
    - Dados de Engenharia (Dinabox API)
    - Métricas de PCP (planejamento de produção)
    - Dados Operacionais (bipagem, expedição)
    """

    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.CASCADE,
        related_name="ambientes",
        verbose_name="Pedido",
    )

    nome_ambiente = models.CharField(
        max_length=255,
        db_index=True,
        verbose_name="Nome do Ambiente",
    )
    descricao = models.TextField(
        blank=True,
        verbose_name="Descrição",
    )

    # ============= Dados do Comercial (denormalizado) =============
    acabamentos = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Acabamentos",
        help_text="Ex: ['Laminado Cinza', 'Vidro Temperado']",
    )
    eletrodomesticos = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Eletrodomésticos",
        help_text="Ex: ['Fogão Consul', 'Geladeira Brastemp']",
    )
    observacoes_especiais = models.TextField(
        blank=True,
        verbose_name="Observações Especiais",
        help_text="Ex: 'Bicama na suite ana'",
    )

    # ============= Dados de Engenharia (Dinabox API) =============
    # Estrutura: {'dimensoes': '2750x1830', 'furacoes': [...], 'usinagens': [...]}
    dados_engenharia = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Dados de Engenharia",
        help_text="Extrahdos da API Dinabox",
    )

    # ============= Métricas PCP (Resumo agregado) =============
    # Estrutura: {'total_pecas_pcp': 120, 'pecas_corte': 100, 'tempo_prod_horas': 8}
    metricas_pcp_resumo = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Métricas PCP (Resumo)",
        help_text="Agregados dos lotes vinculados",
    )

    # ============= Dados Operacionais (Bipagem, Expedição) =============
    # Estrutura: {'pecas_bipadas': 80, 'pecas_expedidas': 70}
    dados_operacionais_resumo = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Dados Operacionais (Resumo)",
        help_text="Agregados de bipagem, expedição, etc",
    )

    # ============= Vínculo com PCP =============
    # Um ambiente pode ter múltiplos lotes associados
    lotes_pcp = models.ManyToManyField(
        "pcp.LotePCP",
        blank=True,
        related_name="ambientes_pedido",
        verbose_name="Lotes PCP",
    )

    # ============= Status e Auditoria =============
    status = models.CharField(
        max_length=20,
        choices=AmbienteStatus.choices,
        default=AmbienteStatus.PENDENTE,
        db_index=True,
        verbose_name="Status",
    )

    data_criacao = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data de Criação",
    )
    data_atualizacao = models.DateTimeField(
        auto_now=True,
        verbose_name="Data de Atualização",
    )

    class Meta:
        verbose_name = "Ambiente do Pedido"
        verbose_name_plural = "Ambientes do Pedido"
        unique_together = ("pedido", "nome_ambiente")
        ordering = ["pedido", "nome_ambiente"]
        indexes = [
            models.Index(fields=["pedido", "status"], name="amb_ped_st_idx"),
            models.Index(fields=["status", "-data_atualizacao"], name="amb_st_dt_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.nome_ambiente} (Pedido {self.pedido.numero_pedido})"

    @property
    def num_pecas_pcp(self) -> int:
        """Retorna o total de peças planejadas pelo PCP para este ambiente."""
        return self.metricas_pcp_resumo.get("total_pecas_pcp", 0)

    @property
    def num_pecas_bipadas(self) -> int:
        """Retorna o total de peças já bipadas."""
        return self.dados_operacionais_resumo.get("pecas_bipadas", 0)

"""
Selectors para o app pedidos.

Responsabilidade: Consultas complexas e reutilizáveis.
Padrão: Centralizar todas as queries aqui.
"""

from typing import Optional, List
import unicodedata
from django.db.models import QuerySet, Q, Prefetch

from apps.pedidos.models import Pedido, AmbientePedido, HistoricoStatusPedido
from apps.pedidos.domain.status import PedidoStatus, AmbienteStatus


class PedidoSelector:
    """Seletores para Pedidos com queries otimizadas."""

    @staticmethod
    def list_pedidos_ativos() -> QuerySet:
        """Lista pedidos não cancelados, ordenados por data recente."""
        return (
            Pedido.objects.exclude(status=PedidoStatus.CANCELADO)
            .select_related("cliente_comercial", "criado_por")
            .prefetch_related("ambientes", "historico_status")
            .order_by("-data_criacao")
        )

    @staticmethod
    def list_pedidos_por_status(status: str) -> QuerySet:
        """Lista pedidos filtrados por status."""
        return (
            Pedido.objects.filter(status=status)
            .select_related("cliente_comercial", "criado_por")
            .prefetch_related("ambientes")
            .order_by("-data_criacao")
        )

    @staticmethod
    def list_pedidos_por_cliente(customer_id: str) -> QuerySet:
        """Lista todos os pedidos de um cliente específico."""
        return (
            Pedido.objects.filter(customer_id=customer_id)
            .select_related("cliente_comercial", "criado_por")
            .prefetch_related("ambientes")
            .order_by("-data_criacao")
        )

    @staticmethod
    def get_pedido_completo(numero_pedido: str) -> Optional[Pedido]:
        """Retorna um pedido com todos seus relacionamentos otimizados."""
        return (
            Pedido.objects.filter(numero_pedido=numero_pedido)
            .select_related("cliente_comercial", "criado_por")
            .prefetch_related(
                Prefetch(
                    "ambientes",
                    queryset=AmbientePedido.objects.select_related("pedido").order_by(
                        "nome_ambiente"
                    ),
                ),
                Prefetch(
                    "historico_status",
                    queryset=HistoricoStatusPedido.objects.order_by("-data_criacao"),
                ),
            )
            .first()
        )

    @staticmethod
    def get_pedido_por_id(pk: int) -> Optional[Pedido]:
        """Retorna um pedido por ID com relacionamentos otimizados."""
        return (
            Pedido.objects.filter(pk=pk)
            .select_related("cliente_comercial", "criado_por")
            .prefetch_related("ambientes", "historico_status")
            .first()
        )

    @staticmethod
    def search_pedidos(query: str) -> QuerySet:
        """Busca pedidos por número, cliente ou customer_id."""
        return (
            Pedido.objects.filter(
                Q(numero_pedido__icontains=query)
                | Q(cliente_nome__icontains=query)
                | Q(customer_id__icontains=query)
            )
            .select_related("cliente_comercial")
            .order_by("-data_criacao")
        )

    @staticmethod
    def list_pedidos_em_atraso() -> QuerySet:
        """Lista pedidos não concluídos com data de entrega vencida."""
        from datetime import date

        return Pedido.objects.filter(
            Q(status__in=[PedidoStatus.CONTRATO_FECHADO, PedidoStatus.ENVIADO_PARA_PROJETOS, PedidoStatus.EM_ENGENHARIA, PedidoStatus.EM_PRODUCAO])
            & Q(data_entrega_prevista__lt=date.today())
        ).order_by("data_entrega_prevista")


class AmbienteSelector:
    """Seletores para AmbientePedido com queries otimizadas."""

    @staticmethod
    def list_ambientes_por_pedido(numero_pedido: str) -> QuerySet:
        """Lista ambientes de um pedido específico."""
        return (
            AmbientePedido.objects.filter(pedido__numero_pedido=numero_pedido)
            .select_related("pedido")
            .order_by("nome_ambiente")
        )

    @staticmethod
    def list_ambientes_por_status(status: str) -> QuerySet:
        """Lista ambientes filtrados por status."""
        return (
            AmbientePedido.objects.filter(status=status)
            .select_related("pedido")
            .order_by("-data_atualizacao")
        )

    @staticmethod
    def get_ambiente_completo(pk: int) -> Optional[AmbientePedido]:
        """Retorna um ambiente com todos seus relacionamentos."""
        return (
            AmbientePedido.objects.filter(pk=pk)
            .select_related("pedido")
            .prefetch_related("lotes_pcp")
            .first()
        )

    @staticmethod
    def list_ambientes_aguardando_pcp() -> QuerySet:
        """Lista ambientes que finalizaram engenharia e aguardam PCP."""
        return (
            AmbientePedido.objects.filter(status=AmbienteStatus.AGUARDANDO_PCP)
            .select_related("pedido")
            .order_by("-data_atualizacao")
        )

    @staticmethod
    def list_ambientes_em_producao() -> QuerySet:
        """Lista ambientes em fase de produção (indústria ou montagem)."""
        return (
            AmbientePedido.objects.filter(
                status__in=[AmbienteStatus.EM_INDUSTRIA, AmbienteStatus.EM_MONTAGEM]
            )
            .select_related("pedido")
            .order_by("-data_atualizacao")
        )

    @staticmethod
    def search_ambientes(query: str) -> QuerySet:
        """Busca ambientes por nome, desc ou pedido relacionado."""
        return (
            AmbientePedido.objects.filter(
                Q(nome_ambiente__icontains=query)
                | Q(descricao__icontains=query)
                | Q(pedido__numero_pedido__icontains=query)
            )
            .select_related("pedido")
            .order_by("pedido", "nome_ambiente")
        )

    @staticmethod
    def get_ambiente_por_cliente_e_nome(customer_id: str, nome_ambiente: str) -> Optional[AmbientePedido]:
        """Localiza um AmbientePedido pelo customer_id e descrição do ambiente."""

        def _normalize(value: str) -> str:
            base = unicodedata.normalize("NFKD", str(value or "").strip().upper())
            return "".join(
                ch for ch in base
                if not unicodedata.combining(ch) and (ch.isalnum() or ch in {" ", "_", "-"})
            ).replace("_", " ").replace("-", " ")

        nome_norm = " ".join(_normalize(nome_ambiente).split())

        candidatos = list(
            AmbientePedido.objects.filter(
                pedido__customer_id=str(customer_id).strip(),
                pedido__status__in=[
                    PedidoStatus.CONTRATO_FECHADO,
                    PedidoStatus.ENVIADO_PARA_PROJETOS,
                    PedidoStatus.EM_ENGENHARIA,
                    PedidoStatus.EM_PRODUCAO,
                ],
            )
            .select_related("pedido")
            .order_by("-pedido__data_criacao", "nome_ambiente")
        )

        encontrados = [
            ambiente
            for ambiente in candidatos
            if " ".join(_normalize(ambiente.nome_ambiente).split()) == nome_norm
        ]
        if len(encontrados) > 1:
            raise ValueError(
                f"Ambiente ambiguo para customer_id={customer_id} e descricao={nome_ambiente}."
            )
        return encontrados[0] if encontrados else None


class HistoricoStatusSelector:
    """Seletores para HistoricoStatusPedido."""

    @staticmethod
    def list_historico_pedido(numero_pedido: str) -> QuerySet:
        """Lista histórico de mudanças de status de um pedido."""
        return (
            HistoricoStatusPedido.objects.filter(pedido__numero_pedido=numero_pedido)
            .select_related("pedido", "usuario")
            .order_by("-data_criacao")
        )

    @staticmethod
    def get_transicoes_recentes(limit: int = 50) -> QuerySet:
        """Lista as transições de status mais recentes do sistema."""
        return (
            HistoricoStatusPedido.objects.select_related("pedido", "usuario")
            .order_by("-data_criacao")[:limit]
        )

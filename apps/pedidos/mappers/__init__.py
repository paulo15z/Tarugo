"""
Mappers para o app pedidos.

Responsabilidade: Conversão entre Models (Django ORM) e Schemas (Pydantic).
Padrão: Manter models limpos, toda transformação aqui.
"""

from typing import List, Optional

from apps.pedidos.models import Pedido, AmbientePedido, HistoricoStatusPedido
from apps.pedidos.schemas import (
    PedidoOutputSchema,
    PedidoDetalheSchema,
    AmbientePedidoOutputSchema,
    HistoricoStatusOutputSchema,
)


class PedidoMapper:
    """Mapeia Pedido (Model) ↔ PedidoSchema (Pydantic)."""

    @staticmethod
    def model_to_output_schema(pedido: Pedido) -> PedidoOutputSchema:
        """Converte Model Pedido para Schema de saída."""
        return PedidoOutputSchema(
            id=pedido.id,
            numero_pedido=pedido.numero_pedido,
            customer_id=pedido.customer_id,
            cliente_nome=pedido.cliente_nome,
            status=pedido.status,
            data_criacao=pedido.data_criacao,
            data_contrato=pedido.data_contrato,
            data_entrega_prevista=pedido.data_entrega_prevista,
            data_conclusao=pedido.data_conclusao,
            observacoes=pedido.observacoes,
            percentual_conclusao=pedido.percentual_conclusao,
        )

    @staticmethod
    def model_to_detalhe_schema(pedido: Pedido) -> PedidoDetalheSchema:
        """Converte Model Pedido para Schema detalhado com ambientes."""
        ambientes = [
            AmbienteMapper.model_to_output_schema(amb) for amb in pedido.ambientes.all()
        ]
        return PedidoDetalheSchema(
            id=pedido.id,
            numero_pedido=pedido.numero_pedido,
            customer_id=pedido.customer_id,
            cliente_nome=pedido.cliente_nome,
            status=pedido.status,
            data_criacao=pedido.data_criacao,
            data_contrato=pedido.data_contrato,
            data_entrega_prevista=pedido.data_entrega_prevista,
            data_conclusao=pedido.data_conclusao,
            observacoes=pedido.observacoes,
            percentual_conclusao=pedido.percentual_conclusao,
            ambientes=ambientes,
        )

    @staticmethod
    def models_to_output_schemas(pedidos: List[Pedido]) -> List[PedidoOutputSchema]:
        """Converte lista de Models para lista de Schemas."""
        return [PedidoMapper.model_to_output_schema(p) for p in pedidos]


class AmbienteMapper:
    """Mapeia AmbientePedido (Model) ↔ AmbientePedidoSchema (Pydantic)."""

    @staticmethod
    def model_to_output_schema(ambiente: AmbientePedido) -> AmbientePedidoOutputSchema:
        """Converte Model AmbientePedido para Schema de saída."""
        return AmbientePedidoOutputSchema(
            id=ambiente.id,
            nome_ambiente=ambiente.nome_ambiente,
            descricao=ambiente.descricao,
            acabamentos=ambiente.acabamentos,
            eletrodomesticos=ambiente.eletrodomesticos,
            observacoes_especiais=ambiente.observacoes_especiais,
            status=ambiente.status,
            dados_engenharia=ambiente.dados_engenharia,
            metricas_pcp_resumo=ambiente.metricas_pcp_resumo,
            dados_operacionais_resumo=ambiente.dados_operacionais_resumo,
            data_criacao=ambiente.data_criacao,
            data_atualizacao=ambiente.data_atualizacao,
        )

    @staticmethod
    def models_to_output_schemas(ambientes: List[AmbientePedido]) -> List[AmbientePedidoOutputSchema]:
        """Converte lista de Models para lista de Schemas."""
        return [AmbienteMapper.model_to_output_schema(a) for a in ambientes]


class HistoricoStatusMapper:
    """Mapeia HistoricoStatusPedido (Model) para Schema."""

    @staticmethod
    def model_to_output_schema(historico: HistoricoStatusPedido) -> HistoricoStatusOutputSchema:
        """Converte Model de histórico para Schema."""
        return HistoricoStatusOutputSchema(
            pedido_numero=historico.pedido.numero_pedido,
            status_anterior=historico.status_anterior,
            status_novo=historico.status_novo,
            motivo=historico.motivo,
            usuario=historico.usuario.username if historico.usuario else None,
            data_criacao=historico.data_criacao,
        )

    @staticmethod
    def models_to_output_schemas(
        historicos: List[HistoricoStatusPedido],
    ) -> List[HistoricoStatusOutputSchema]:
        """Converte lista de Models para lista de Schemas."""
        return [HistoricoStatusMapper.model_to_output_schema(h) for h in historicos]

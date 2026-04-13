"""
Serializers DRF para o app pedidos.

Responsabilidade: Serialização para API REST.
"""

from rest_framework import serializers

from apps.pedidos.models import Pedido, AmbientePedido, HistoricoStatusPedido


class AmbientePedidoSerializer(serializers.ModelSerializer):
    class Meta:
        model = AmbientePedido
        fields = [
            "id",
            "nome_ambiente",
            "descricao",
            "acabamentos",
            "eletrodomesticos",
            "observacoes_especiais",
            "status",
            "dados_engenharia",
            "metricas_pcp_resumo",
            "dados_operacionais_resumo",
            "data_criacao",
            "data_atualizacao",
        ]
        read_only_fields = [
            "id",
            "data_criacao",
            "data_atualizacao",
        ]


class PedidoSerializer(serializers.ModelSerializer):
    ambientes = AmbientePedidoSerializer(many=True, read_only=True)
    percentual_conclusao = serializers.SerializerMethodField()

    class Meta:
        model = Pedido
        fields = [
            "id",
            "numero_pedido",
            "customer_id",
            "cliente_nome",
            "status",
            "data_criacao",
            "data_contrato",
            "data_entrega_prevista",
            "data_conclusao",
            "observacoes",
            "percentual_conclusao",
            "ambientes",
        ]
        read_only_fields = [
            "id",
            "data_criacao",
            "data_conclusao",
            "percentual_conclusao",
        ]

    def get_percentual_conclusao(self, obj):
        return obj.percentual_conclusao


class HistoricoStatusSerializer(serializers.ModelSerializer):
    usuario_nome = serializers.SerializerMethodField()
    pedido_numero = serializers.CharField(source="pedido.numero_pedido", read_only=True)

    class Meta:
        model = HistoricoStatusPedido
        fields = [
            "id",
            "pedido_numero",
            "status_anterior",
            "status_novo",
            "motivo",
            "usuario_nome",
            "data_criacao",
        ]
        read_only_fields = fields

    def get_usuario_nome(self, obj):
        return obj.usuario.username if obj.usuario else "Sistema"

from rest_framework import serializers

from apps.estoque.models.produto import Produto
from apps.estoque.models.movimentacao import Movimentacao


class ProdutoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Produto
        fields = ['id', 'nome', 'sku', 'quantidade', 'estoque_minimo', 'criado_em']
        read_only_fields = ['id', 'criado_em']


class MovimentacaoSerializer(serializers.Serializer):
    """Usado na criação de movimentações via POST."""
    produto_id = serializers.IntegerField()
    quantidade = serializers.IntegerField(min_value=1)
    tipo = serializers.ChoiceField(choices=['entrada', 'saida', 'ajuste', 'transferencia'])
    observacao = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class MovimentacaoListSerializer(serializers.ModelSerializer):
    """Usado na listagem de movimentações."""
    produto_nome = serializers.CharField(source='produto.nome', read_only=True)
    produto_sku = serializers.CharField(source='produto.sku', read_only=True)
    usuario_username = serializers.CharField(source='usuario.username', read_only=True, default=None)
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)

    class Meta:
        model = Movimentacao
        fields = [
            'id',
            'produto',
            'produto_nome',
            'produto_sku',
            'tipo',
            'tipo_display',
            'quantidade',
            'usuario',
            'usuario_username',
            'observacao',
            'criado_em',
        ]
        read_only_fields = fields


class AjusteLoteSerializer(serializers.Serializer):
    """Usado no endpoint de ajuste em lote."""
    movimentacoes = MovimentacaoSerializer(many=True)

from rest_framework import serializers
from apps.estoque.models.produto import Produto
from apps.estoque.models import Movimentacao

class ProdutoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Produto
        fields = '__all__'


class MovimentacaoSerializer(serializers.Serializer):
    produto_id = serializers.IntegerField()
    quantidade = serializers.IntegerField()
    tipo = serializers.ChoiceField(choices=['entrada', 'saida'])


class MovimentacaoListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Movimentacao
        fields = '__all__'
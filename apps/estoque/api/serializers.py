from rest_framework import serializers
from apps.estoque.models.produto import Produto

class ProdutoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Produto
        fields = '__all__'
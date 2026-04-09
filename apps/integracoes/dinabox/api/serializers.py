from rest_framework import serializers
from ..schemas.projeto import ProjetoCompleto, Projeto, Cliente
from ..schemas.modulo import Modulo
from ..schemas.peca import Peca
from ..schemas.insumo import Insumo
from ..schemas.material import Chapa
from ..schemas.base import Metadata


class MetadataSerializer(serializers.Serializer):
    origem = serializers.CharField()
    data_importacao = serializers.DateTimeField()
    versao = serializers.IntegerField()


class ClienteSerializer(serializers.Serializer):
    nome = serializers.CharField(required=False, allow_null=True)


class ProjetoSerializer(serializers.Serializer):
    id = serializers.CharField(required=False, allow_null=True)
    nome = serializers.CharField(required=False, allow_null=True)


class PecaSerializer(serializers.Serializer):
    descricao = serializers.CharField()
    material = serializers.CharField(required=False, allow_null=True)
    largura = serializers.FloatField(required=False, allow_null=True)
    altura = serializers.FloatField(required=False, allow_null=True)
    espessura = serializers.FloatField(required=False, allow_null=True)
    quantidade = serializers.IntegerField()
    modulo = serializers.CharField(required=False, allow_null=True)


class ModuloSerializer(serializers.Serializer):
    nome = serializers.CharField()
    pecas = PecaSerializer(many=True)


class QuantidadeSerializer(serializers.Serializer):
    valor = serializers.FloatField()
    unidade = serializers.CharField()


class InsumoSerializer(serializers.Serializer):
    categoria = serializers.CharField(required=False, allow_null=True)
    descricao = serializers.CharField()
    tipo = serializers.CharField()
    quantidade = QuantidadeSerializer()
    largura = serializers.IntegerField(required=False, allow_null=True)
    altura = serializers.IntegerField(required=False, allow_null=True)
    espessura = serializers.IntegerField(required=False, allow_null=True)
    metadata = serializers.DictField(required=False, allow_null=True)


class ChapaSerializer(serializers.Serializer):
    material = serializers.CharField()
    largura = serializers.IntegerField()
    altura = serializers.IntegerField()
    espessura = serializers.IntegerField()
    area_total = serializers.FloatField()
    area_disponivel = serializers.FloatField()
    identificador = serializers.CharField(required=False, allow_null=True)


class ProjetoCompletoSerializer(serializers.Serializer):
    projeto = ProjetoSerializer()
    cliente = ClienteSerializer()
    pecas = PecaSerializer(many=True)
    modulos = ModuloSerializer(many=True)
    insumos = InsumoSerializer(many=True)
    chapas = ChapaSerializer(many=True)
    metadata = MetadataSerializer()
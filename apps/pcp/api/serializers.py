from rest_framework import serializers
from apps.pcp.models.processamento import ProcessamentoPCP


class ProcessamentoPCPSerializer(serializers.ModelSerializer):
    """ Serializer para listagem/histórico """
    class Meta:
        model = ProcessamentoPCP
        fields = [
            'id',
            'nome_arquivo',
            'data',
            'total_pecas',
            'arquivo_saida',      
        ]
        read_only_fields = ['id', 'data', 'total_pecas', 'arquivo_saida']


class PCPProcessResponseSerializer(serializers.Serializer):
    """ Resposta do processamento (preview + resumo)"""
    pid = serializers.CharField()
    total = serializers.IntegerField()
    previa = serializers.ListField(child=serializers.DictField())
    resumo = serializers.ListField(child=serializers.DictField())
    nome_saida = serializers.CharField(required=False)


class PCPErrorSerializer(serializers.Serializer):
    """Serializer padronizado para erros"""
    erro = serializers.CharField()
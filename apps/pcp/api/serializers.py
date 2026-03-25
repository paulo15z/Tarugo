from rest_framework import serializers
from apps.pcp.models.processamento import ProcessamentoPCP

class ProcessamentoPCPSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcessamentoPCP  # import no topo
        fields = ['id', 'nome_arquivo', 'data', 'total_pecas', 'arquivo_saida']


class PCPProcessResponseSerializer(serializers.Serializer):
    pid = serializers.CharField()
    total = serializers.IntegerField()
    previa = serializers.ListField()
    resumo = serializers.ListField()
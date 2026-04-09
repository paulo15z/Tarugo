# apps/bipagem/api/serializers.py
from rest_framework import serializers
from apps.bipagem.domain.operacional import ETAPAS_AUDITAVEIS_PECA, StatusEnvioExpedicao
from apps.bipagem.models import (
    Pedido,
    OrdemProducao,
    Modulo,
    Peca,
    EventoBipagem,
    LoteProducao,
    EnvioExpedicao,
)


class LoteProducaoSerializer(serializers.ModelSerializer):
    total_pecas = serializers.IntegerField(read_only=True)
    pecas_bipadas = serializers.IntegerField(read_only=True)
    percentual = serializers.FloatField(read_only=True)

    class Meta:
        model = LoteProducao
        fields = [
            'id', 'numero_lote', 'processamento_pcp', 'data_criacao',
            'liberado_para_bipagem', 'bloqueado_motivo', 'observacoes',
            'total_pecas', 'pecas_bipadas', 'percentual'
        ]


class EventoBipagemSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventoBipagem
        fields = ['id', 'momento', 'usuario', 'localizacao']


class PecaListSerializer(serializers.ModelSerializer):
    """Serializer para listagem (mais leve)"""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Peca
        fields = [
            'id', 'id_peca', 'descricao', 'local', 'material',
            'status', 'status_display', 'data_bipagem',
            'quantidade', 'plano_corte'
        ]


class PecaDetailSerializer(serializers.ModelSerializer):
    """Serializer completo com histórico"""
    bipagens = EventoBipagemSerializer(many=True, read_only=True)
    modulo_nome = serializers.CharField(source='modulo.nome_modulo', read_only=True)
    ordem_ambiente = serializers.CharField(source='modulo.ordem_producao.nome_ambiente', read_only=True)
    pedido_numero = serializers.CharField(source='modulo.ordem_producao.pedido.numero_pedido', read_only=True)
    
    class Meta:
        model = Peca
        fields = [
            'id', 'id_peca', 'descricao', 'local', 'material',
            'largura_mm', 'altura_mm', 'espessura_mm', 'quantidade',
            'roteiro', 'plano_corte', 'status', 'data_bipagem',
            'modulo_nome', 'ordem_ambiente', 'pedido_numero',
            'bipagens'
        ]


class ModuloSerializer(serializers.ModelSerializer):
    total_pecas = serializers.SerializerMethodField()
    pecas_bipadas = serializers.SerializerMethodField()
    percentual_concluido = serializers.SerializerMethodField()
    
    class Meta:
        model = Modulo
        fields = ['id', 'referencia_modulo', 'nome_modulo',
                  'total_pecas', 'pecas_bipadas', 'percentual_concluido']
    
    def get_total_pecas(self, obj):
        return obj.total_pecas
    
    def get_pecas_bipadas(self, obj):
        return obj.pecas_bipadas
    
    def get_percentual_concluido(self, obj):
        return obj.percentual_concluido


class OrdemProducaoSerializer(serializers.ModelSerializer):
    total_pecas = serializers.SerializerMethodField()
    pecas_bipadas = serializers.SerializerMethodField()
    percentual_concluido = serializers.SerializerMethodField()
    
    class Meta:
        model = OrdemProducao
        fields = ['id', 'nome_ambiente', 'referencia_principal',
                  'total_pecas', 'pecas_bipadas', 'percentual_concluido']
    
    def get_total_pecas(self, obj):
        return obj.total_pecas  # vai usar property do model
    
    def get_pecas_bipadas(self, obj):
        return obj.pecas_bipadas
    
    def get_percentual_concluido(self, obj):
        return obj.percentual_concluido


class PedidoSerializer(serializers.ModelSerializer):
    total_pecas = serializers.SerializerMethodField()
    pecas_bipadas = serializers.SerializerMethodField()
    percentual_concluido = serializers.SerializerMethodField()
    
    class Meta:
        model = Pedido
        fields = ['id', 'numero_pedido', 'cliente_nome',
                  'total_pecas', 'pecas_bipadas', 'percentual_concluido']
    
    def get_total_pecas(self, obj):
        return obj.total_pecas
    
    def get_pecas_bipadas(self, obj):
        return obj.pecas_bipadas
    
    def get_percentual_concluido(self, obj):
        total = obj.total_pecas
        if total == 0:
            return 0
        return int((obj.pecas_bipadas / total) * 100)


class SeparacaoDestinoSerializer(serializers.Serializer):
    pid = serializers.CharField(min_length=8, max_length=8)
    codigo = serializers.CharField(min_length=1)
    quantidade = serializers.IntegerField(min_value=1, default=1)
    usuario = serializers.CharField(required=False, allow_blank=True, default="OPERADOR")
    localizacao = serializers.CharField(required=False, allow_blank=True, default="SEPARACAO_DESTINOS")


class EnvioExpedicaoCreateSerializer(serializers.Serializer):
    codigo = serializers.CharField(required=False, allow_blank=True, min_length=4, max_length=30)
    descricao = serializers.CharField(required=False, allow_blank=True, max_length=255)
    transportadora = serializers.CharField(required=False, allow_blank=True, max_length=150)
    placa_veiculo = serializers.CharField(required=False, allow_blank=True, max_length=20)
    motorista = serializers.CharField(required=False, allow_blank=True, max_length=150)
    ajudante = serializers.CharField(required=False, allow_blank=True, max_length=150)
    destino_principal = serializers.CharField(required=False, allow_blank=True, max_length=255)
    destinos_secundarios = serializers.CharField(required=False, allow_blank=True)
    observacoes = serializers.CharField(required=False, allow_blank=True)
    usuario = serializers.CharField(required=False, allow_blank=True, default="SISTEMA")


class EnvioExpedicaoAddItemSerializer(serializers.Serializer):
    pid = serializers.CharField(min_length=8, max_length=8)
    codigo = serializers.CharField(min_length=1)
    quantidade = serializers.IntegerField(min_value=1, default=1)
    usuario = serializers.CharField(required=False, allow_blank=True, default="OPERADOR")


class EnvioExpedicaoAddModuloSerializer(serializers.Serializer):
    pid = serializers.CharField(min_length=8, max_length=8)
    codigo_modulo = serializers.CharField(min_length=1, max_length=50)
    ambiente = serializers.CharField(required=False, allow_blank=True)
    usuario = serializers.CharField(required=False, allow_blank=True, default="OPERADOR")


class EnvioExpedicaoMovimentoSerializer(serializers.Serializer):
    usuario = serializers.CharField(required=False, allow_blank=True, default="OPERADOR")
    localizacao = serializers.CharField(required=False, allow_blank=True, default="EXPEDICAO")
    observacao = serializers.CharField(required=False, allow_blank=True)


class EnvioExpedicaoListSerializer(serializers.ModelSerializer):
    total_itens = serializers.IntegerField(read_only=True)
    total_unidades = serializers.IntegerField(read_only=True)

    class Meta:
        model = EnvioExpedicao
        fields = [
            "codigo",
            "descricao",
            "status",
            "transportadora",
            "placa_veiculo",
            "motorista",
            "ajudante",
            "destino_principal",
            "recebido_em",
            "liberado_em",
            "total_itens",
            "total_unidades",
        ]


class EnvioExpedicaoFiltroSerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=[item.value for item in StatusEnvioExpedicao],
        required=False,
        allow_blank=True,
    )


class EventoPecaSerializer(serializers.Serializer):
    pid = serializers.CharField(min_length=8, max_length=8)
    codigo = serializers.CharField(min_length=1)
    etapa = serializers.ChoiceField(choices=[item.value for item in ETAPAS_AUDITAVEIS_PECA])
    quantidade = serializers.IntegerField(min_value=1, default=1)
    usuario = serializers.CharField(required=False, allow_blank=True, default="OPERADOR")
    localizacao = serializers.CharField(required=False, allow_blank=True, default="")
    observacao = serializers.CharField(required=False, allow_blank=True)

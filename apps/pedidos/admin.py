"""
Admin config para o app pedidos.
"""

from django.contrib import admin

from apps.pedidos.models import Pedido, AmbientePedido, HistoricoStatusPedido


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = (
        "numero_pedido",
        "cliente_nome",
        "status",
        "percentual_conclusao",
        "data_criacao",
    )
    list_filter = (
        "status",
        "data_criacao",
    )
    search_fields = (
        "numero_pedido",
        "cliente_nome",
        "customer_id",
    )
    readonly_fields = (
        "data_criacao",
        "data_conclusao",
        "percentual_conclusao",
    )
    fieldsets = (
        ("Informações Básicas", {
            "fields": (
                "numero_pedido",
                "customer_id",
                "cliente_nome",
                "cliente_comercial",
            )
        }),
        ("Status e Ciclo de Vida", {
            "fields": (
                "status",
                "data_contrato",
                "data_entrega_prevista",
                "data_conclusao",
                "percentual_conclusao",
            )
        }),
        ("Observações", {
            "fields": ("observacoes",)
        }),
        ("Auditoria", {
            "fields": (
                "criado_por",
                "data_criacao",
            ),
            "classes": ("collapse",),
        }),
    )


@admin.register(AmbientePedido)
class AmbientePedidoAdmin(admin.ModelAdmin):
    list_display = (
        "nome_ambiente",
        "pedido",
        "status",
        "num_pecas_pcp",
        "num_pecas_bipadas",
        "data_atualizacao",
    )
    list_filter = (
        "status",
        "data_atualizacao",
    )
    search_fields = (
        "nome_ambiente",
        "pedido__numero_pedido",
    )
    readonly_fields = (
        "data_criacao",
        "data_atualizacao",
    )
    fieldsets = (
        ("Informações Básicas", {
            "fields": (
                "pedido",
                "nome_ambiente",
                "descricao",
            )
        }),
        ("Comercial", {
            "fields": (
                "acabamentos",
                "eletrodomesticos",
                "observacoes_especiais",
            )
        }),
        ("Engenharia", {
            "fields": ("dados_engenharia",)
        }),
        ("PCP e Produção", {
            "fields": (
                "metricas_pcp_resumo",
                "lotes_pcp",
            )
        }),
        ("Dados Operacionais", {
            "fields": ("dados_operacionais_resumo",)
        }),
        ("Status", {
            "fields": ("status",)
        }),
        ("Auditoria", {
            "fields": (
                "data_criacao",
                "data_atualizacao",
            ),
            "classes": ("collapse",),
        }),
    )


@admin.register(HistoricoStatusPedido)
class HistoricoStatusPedidoAdmin(admin.ModelAdmin):
    list_display = (
        "pedido",
        "status_anterior",
        "status_novo",
        "usuario",
        "data_criacao",
    )
    list_filter = (
        "status_novo",
        "data_criacao",
    )
    search_fields = (
        "pedido__numero_pedido",
        "motivo",
    )
    readonly_fields = (
        "pedido",
        "data_criacao",
    )
    fieldsets = (
        ("Pedido", {
            "fields": ("pedido",)
        }),
        ("Transição de Status", {
            "fields": (
                "status_anterior",
                "status_novo",
                "motivo",
            )
        }),
        ("Auditoria", {
            "fields": (
                "usuario",
                "data_criacao",
            ),
            "classes": ("collapse",),
        }),
    )

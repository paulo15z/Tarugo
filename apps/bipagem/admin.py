from django.contrib import admin

from apps.bipagem.models import EnvioExpedicao, EnvioExpedicaoItem, EventoOperacional


@admin.register(EnvioExpedicao)
class EnvioExpedicaoAdmin(admin.ModelAdmin):
    list_display = ("codigo", "status", "motorista", "ajudante", "destino_principal", "placa_veiculo", "recebido_em", "liberado_em")
    search_fields = ("codigo", "descricao", "transportadora", "placa_veiculo", "motorista", "ajudante", "destino_principal")
    list_filter = ("status", "transportadora", "destino_principal")


@admin.register(EnvioExpedicaoItem)
class EnvioExpedicaoItemAdmin(admin.ModelAdmin):
    list_display = ("envio", "codigo_peca", "quantidade", "lote_pid", "ambiente_nome", "modulo_nome")
    search_fields = ("envio__codigo", "peca__codigo_peca", "lote_pid", "ambiente_nome", "modulo_nome")
    list_filter = ("lote_pid", "ambiente_nome")

    @admin.display(ordering="peca__codigo_peca", description="Codigo da Peca")
    def codigo_peca(self, obj):
        return obj.peca.codigo_peca


@admin.register(EventoOperacional)
class EventoOperacionalAdmin(admin.ModelAdmin):
    list_display = ("etapa", "movimento", "lote_pid", "codigo_peca", "usuario", "momento")
    search_fields = ("lote_pid", "peca__codigo_peca", "codigo_modulo", "ambiente_nome", "usuario")
    list_filter = ("etapa", "movimento", "escopo")

    @admin.display(ordering="peca__codigo_peca", description="Codigo da Peca")
    def codigo_peca(self, obj):
        return obj.peca.codigo_peca if obj.peca else ""

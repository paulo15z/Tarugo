from django.contrib import admin

from .models import AmbienteOrcamento, ClienteComercial, ObservacaoComercial


class ObservacaoComercialInline(admin.TabularInline):
    model = ObservacaoComercial
    extra = 0
    readonly_fields = ("criado_em",)


class AmbienteOrcamentoInline(admin.TabularInline):
    model = AmbienteOrcamento
    extra = 0


@admin.register(ClienteComercial)
class ClienteComercialAdmin(admin.ModelAdmin):
    list_display = ("customer_id", "numero_pedido", "status", "criado_por", "atualizado_em")
    list_filter = ("status",)
    search_fields = ("customer_id", "numero_pedido")
    inlines = (ObservacaoComercialInline, AmbienteOrcamentoInline)


@admin.register(ObservacaoComercial)
class ObservacaoComercialAdmin(admin.ModelAdmin):
    list_display = ("cliente", "autor", "criado_em")
    search_fields = ("texto",)


@admin.register(AmbienteOrcamento)
class AmbienteOrcamentoAdmin(admin.ModelAdmin):
    list_display = ("cliente", "nome_ambiente", "valor_orcado", "ordem")

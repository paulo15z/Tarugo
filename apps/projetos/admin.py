from django.contrib import admin

from apps.projetos.models import AnexoProjeto, Projeto


@admin.register(Projeto)
class ProjetoAdmin(admin.ModelAdmin):
    list_display = ("nome_projeto", "pedido", "ambiente_pedido", "status", "projetista", "liberador_tecnico", "criado_em")
    list_filter = ("status", "distribuidor", "projetista", "liberador_tecnico", "criado_em")
    search_fields = ("nome_projeto", "pedido__numero_pedido", "ambiente_pedido__nome_ambiente")
    readonly_fields = ("criado_em", "atualizado_em", "data_inicio_real", "data_fim_real")


@admin.register(AnexoProjeto)
class AnexoProjetoAdmin(admin.ModelAdmin):
    list_display = ("nome_arquivo", "projeto", "tipo_anexo", "uploaded_by", "criado_em")
    list_filter = ("tipo_anexo", "criado_em")
    search_fields = ("nome_arquivo", "descricao", "projeto__nome_projeto")
    readonly_fields = ("criado_em",)

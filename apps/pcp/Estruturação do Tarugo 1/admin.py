"""
Admin interface para o app integracoes.
"""

from django.contrib import admin
from .models import MapeamentoMaterial, DinaboxClienteIndex


@admin.register(MapeamentoMaterial)
class MapeamentoMaterialAdmin(admin.ModelAdmin):
    """Admin para mapeamentos de materiais."""
    
    list_display = ('nome_dinabox', 'produto', 'fator_conversao', 'ativo', 'atualizado_em')
    list_filter = ('ativo', 'atualizado_em')
    search_fields = ('nome_dinabox', 'produto__nome')
    readonly_fields = ('criado_em', 'atualizado_em')
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('nome_dinabox', 'produto', 'fator_conversao', 'ativo')
        }),
        ('Auditoria', {
            'fields': ('criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        }),
    )


@admin.register(DinaboxClienteIndex)
class DinaboxClienteIndexAdmin(admin.ModelAdmin):
    """Admin para índice de clientes Dinabox."""
    
    list_display = ('customer_id', 'customer_name', 'customer_type', 'customer_status', 'synced_at')
    list_filter = ('customer_type', 'customer_status', 'synced_at')
    search_fields = ('customer_id', 'customer_name', 'customer_name_normalized')
    readonly_fields = ('customer_name_normalized', 'synced_at', 'raw_payload')
    
    fieldsets = (
        ('Informações do Cliente', {
            'fields': ('customer_id', 'customer_name', 'customer_name_normalized', 'customer_type', 'customer_status')
        }),
        ('Contato', {
            'fields': ('customer_emails_text', 'customer_phones_text'),
            'classes': ('collapse',)
        }),
        ('Dados Brutos', {
            'fields': ('raw_payload',),
            'classes': ('collapse',)
        }),
        ('Sincronização', {
            'fields': ('synced_at',),
            'classes': ('collapse',)
        }),
    )

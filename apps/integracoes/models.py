"""
Models para o app integracoes.

Responsabilidade: Estrutura de dados + ORM (sem regras de negócio).
Regra de Ouro: Sem lógica de negócio aqui; tudo vai para services.
"""

from django.db import models
from apps.estoque.models.produto import Produto


class MapeamentoMaterial(models.Model):
    """
    Vínculo entre o nome do material no Dinabox e o Produto no Estoque.
    Essencial para o Gêmeo Digital: garante que o consumo digital reflita no estoque físico.
    """
    nome_dinabox = models.CharField(
        max_length=255, 
        unique=True, 
        verbose_name="Nome no Dinabox",
        help_text="Exatamente como aparece no JSON/CSV do Dinabox"
    )
    produto = models.ForeignKey(
        Produto, 
        on_delete=models.CASCADE, 
        related_name="mapeamentos",
        verbose_name="Produto Vinculado"
    )
    
    fator_conversao = models.DecimalField(
        max_digits=10, 
        decimal_places=4, 
        default=1.0,
        verbose_name="Fator de Conversão",
        help_text="Multiplicador para o consumo (ex: 1.1 para 10% de margem de erro/perda)"
    )

    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Mapeamento de Material"
        verbose_name_plural = "Mapeamentos de Materiais"
        indexes = [
            models.Index(fields=["nome_dinabox"], name="mapeamento_nome_idx"),
            models.Index(fields=["ativo"], name="mapeamento_ativo_idx"),
        ]

    def __str__(self):
        return f"{self.nome_dinabox} → {self.produto.nome}"


class DinaboxClienteIndex(models.Model):
    """
    Índice local de clientes Dinabox para busca e listagem rápida no Tarugo.
    Sincronizado periodicamente via DinaboxIntegrationService.
    """

    customer_id = models.CharField(
        max_length=64, 
        unique=True, 
        db_index=True,
        verbose_name="ID do Cliente Dinabox"
    )
    customer_name = models.CharField(
        max_length=255, 
        blank=True, 
        default="",
        verbose_name="Nome do Cliente"
    )
    customer_name_normalized = models.CharField(
        max_length=255, 
        blank=True, 
        default="", 
        db_index=True,
        verbose_name="Nome Normalizado (para busca)"
    )
    customer_type = models.CharField(
        max_length=16, 
        blank=True, 
        default="", 
        db_index=True,
        verbose_name="Tipo (PF/PJ)"
    )
    customer_status = models.CharField(
        max_length=16, 
        blank=True, 
        default="", 
        db_index=True,
        verbose_name="Status"
    )
    customer_emails_text = models.TextField(
        blank=True, 
        default="",
        verbose_name="Emails (texto)"
    )
    customer_phones_text = models.TextField(
        blank=True, 
        default="",
        verbose_name="Telefones (texto)"
    )
    raw_payload = models.JSONField(
        default=dict, 
        blank=True,
        verbose_name="Payload Bruto (Dinabox)"
    )
    synced_at = models.DateTimeField(
        auto_now=True, 
        db_index=True,
        verbose_name="Última Sincronização"
    )

    class Meta:
        verbose_name = "Índice Cliente Dinabox"
        verbose_name_plural = "Índices de Clientes Dinabox"
        indexes = [
            models.Index(fields=["customer_name_normalized"], name="dinabox_cli_nome_idx"),
            models.Index(fields=["customer_status", "customer_type"], name="dinabox_cli_st_tp_idx"),
            models.Index(fields=["synced_at"], name="dinabox_cli_sync_idx"),
        ]

    @staticmethod
    def _normalize(value: str) -> str:
        """Normaliza string para busca case-insensitive."""
        return " ".join((value or "").strip().lower().split())

    def save(self, *args, **kwargs):
        self.customer_name_normalized = self._normalize(self.customer_name)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.customer_id} - {self.customer_name}"

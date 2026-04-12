"""
Models do app comercial: dados de fluxo comercial no Tarugo (não substituem o cadastro essencial na Dinabox).
"""

from django.conf import settings
from django.db import models


class StatusClienteComercial(models.TextChoices):
    PRIMEIRO_CONTATO = "primeiro_contato", "Primeiro contato"
    EM_ORCAMENTO = "em_orcamento", "Em orçamento"
    EM_NEGOCIACAO = "em_negociacao", "Em negociação"
    CONTRATO_FECHADO = "contrato_fechado", "Contrato fechado"
    ARQUIVADO = "arquivado", "Arquivado"


class ClienteComercial(models.Model):
    """
    Ficha comercial vinculada ao customer_id da Dinabox.
    Observações ricas e ambientes ficam aqui; nome/tipo/contatos essenciais seguem na API Dinabox.
    """

    customer_id = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        verbose_name="ID cliente Dinabox",
    )
    status = models.CharField(
        max_length=32,
        choices=StatusClienteComercial.choices,
        default=StatusClienteComercial.PRIMEIRO_CONTATO,
        db_index=True,
    )
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="clientes_comerciais_criados",
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Cliente comercial"
        verbose_name_plural = "Clientes comerciais"
        ordering = ["-atualizado_em"]
        indexes = [
            models.Index(fields=["status", "atualizado_em"], name="comercial_cli_st_upd_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.customer_id} ({self.get_status_display()})"


class ObservacaoComercial(models.Model):
    cliente = models.ForeignKey(
        ClienteComercial,
        on_delete=models.CASCADE,
        related_name="observacoes",
    )
    texto = models.TextField()
    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="observacoes_comerciais",
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Observação comercial"
        verbose_name_plural = "Observações comerciais"
        ordering = ["-criado_em"]

    def __str__(self) -> str:
        return f"Obs #{self.pk} — {self.cliente_id}"


class AmbienteOrcamento(models.Model):
    """
    Ambiente com detalhes comerciais: acabamentos, eletrodomésticos e observações.
    Dados estruturados para facilitar handoff para Projetos.
    
    Exemplo desejável em Projetos:
    - qual cliente
    - Quantos ambientes
    - Quais ambientes
    - Quais eletros nos ambientes
    - Quais acabamentos (confirmados)
    - Itens especiais "Bicama na SUITE ANA"
    """

    cliente = models.ForeignKey(
        ClienteComercial,
        on_delete=models.CASCADE,
        related_name="ambientes",
    )
    nome_ambiente = models.CharField(max_length=200)
    valor_orcado = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Valor orçado",
    )
    
    # Acabamentos: lista de strings simples ou dicts com detalhes
    # Ex: ["Pintura branca fosca", "Piso porcelanato 60x60", "Rodapé MDF 15cm"]
    acabamentos = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Acabamentos",
        help_text="Lista de acabamentos (materiais, cores, dimensões, etc)"
    )
    
    # Eletrodomésticos: lista de strings simples ou dicts com marca/modelo
    # Ex: ["Geladeira Brastemp 500L", "Fogão 5 bocas Consul", "Microondas Electrolux"]
    eletrodomesticos = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Eletrodomésticos",
        help_text="Lista de eletrodomésticos (marca, modelo, capacidade)"
    )
    
    # Observações especiais para atenção em Projetos
    # Ex: "Bicama na SUITE ANA", "Nicho no fundo da cozinha", "Painel TV na sala"
    observacoes_especiais = models.TextField(
        blank=True,
        default="",
        verbose_name="Observações especiais",
        help_text="Itens que precisam atenção especial na Engenharia"
    )
    
    ordem = models.PositiveIntegerField(default=0)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Ambiente (orçamento)"
        verbose_name_plural = "Ambientes (orçamento)"
        ordering = ["ordem", "pk"]

    def __str__(self) -> str:
        return f"{self.nome_ambiente} ({self.cliente_id})"

    class Meta:
        verbose_name = "Ambiente (orçamento)"
        verbose_name_plural = "Ambientes (orçamento)"
        ordering = ["ordem", "pk"]

    def __str__(self) -> str:
        return f"{self.nome_ambiente} ({self.cliente_id})"

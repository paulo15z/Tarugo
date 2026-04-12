# apps/pcp/models/ripa.py
"""
Modelos para Gestão de Ripas (Tiras/Retalhos).

Responsabilidade: Representar ripas geradas durante o corte.
Padrão: ORM apenas, sem lógica de negócio.
"""

from django.db import models
from decimal import Decimal
from apps.core.models import BaseModel
from apps.pcp.models.lote import LotePCP


class OrigemRipa(models.TextChoices):
    """Origem da ripa no processo de corte."""
    
    CORTE = "CORTE", "Gerada no Corte"
    FONTE = "FONTE", "Tira-Fonte (Material Bruto)"


class DestinoRipa(models.TextChoices):
    """Destino da ripa após corte."""
    
    ESTOQUE = "ESTOQUE", "Retorna ao Estoque"
    REUSO = "REUSO", "Reutilização em Projeto"
    DESCARTE = "DESCARTE", "Descarte"
    PENDENTE = "PENDENTE", "Pendente Decisão"


class StatusRipa(models.TextChoices):
    """Status da ripa no fluxo."""
    
    PLANEJADA = "PLANEJADA", "Planejada"
    CORTADA = "CORTADA", "Cortada"
    PROCESSADA = "PROCESSADA", "Processada"
    FINALIZADA = "FINALIZADA", "Finalizada"


class Ripa(BaseModel):
    """
    Representa uma ripa (tira/retalho) gerada durante o corte.
    Essencial para otimização de material e rastreamento de reuso.
    """
    
    lote = models.ForeignKey(
        LotePCP,
        on_delete=models.CASCADE,
        related_name='ripas',
        verbose_name="Lote"
    )
    
    # Identificação
    codigo_ripa = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Código da Ripa",
        help_text="Ex: RIP-20260411-001"
    )
    
    # Material
    material_name = models.CharField(
        max_length=255,
        verbose_name="Nome do Material",
        help_text="Ex: Carvalho Poro - ARAUCO"
    )
    
    material_id = models.CharField(
        max_length=50,
        blank=True,
        default="",
        verbose_name="ID do Material (Dinabox)"
    )
    
    espessura_mm = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name="Espessura (mm)"
    )
    
    # Dimensões
    comprimento_mm = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Comprimento (mm)"
    )
    
    largura_mm = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Largura (mm)"
    )
    
    # Quantidade
    quantidade = models.PositiveIntegerField(
        default=1,
        verbose_name="Quantidade de Ripas"
    )
    
    # Origem e Destino
    origem = models.CharField(
        max_length=20,
        choices=OrigemRipa.choices,
        default=OrigemRipa.CORTE,
        verbose_name="Origem"
    )
    
    destino = models.CharField(
        max_length=20,
        choices=DestinoRipa.choices,
        default=DestinoRipa.PENDENTE,
        verbose_name="Destino"
    )
    
    status = models.CharField(
        max_length=20,
        choices=StatusRipa.choices,
        default=StatusRipa.PLANEJADA,
        verbose_name="Status"
    )
    
    # Rastreamento
    observacoes = models.TextField(
        blank=True,
        default="",
        verbose_name="Observações"
    )
    
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Ripa"
        verbose_name_plural = "Ripas"
        indexes = [
            models.Index(fields=['lote'], name='ripa_lote_idx'),
            models.Index(fields=['material_name'], name='ripa_material_idx'),
            models.Index(fields=['status'], name='ripa_status_idx'),
            models.Index(fields=['destino'], name='ripa_destino_idx'),
        ]
        ordering = ['-criado_em']
    
    def __str__(self):
        return f"{self.codigo_ripa} - {self.material_name} ({self.comprimento_mm}x{self.largura_mm}mm)"
    
    @property
    def area_m2(self) -> Decimal:
        """Calcula área em m²."""
        return (self.comprimento_mm * self.largura_mm) / Decimal(1_000_000)
    
    @property
    def volume_m3(self) -> Decimal:
        """Calcula volume em m³."""
        return self.area_m2 * (self.espessura_mm / Decimal(1000))
    
    def marcar_cortada(self) -> None:
        """Marca ripa como cortada."""
        self.status = StatusRipa.CORTADA
        self.save()
    
    def marcar_processada(self) -> None:
        """Marca ripa como processada."""
        self.status = StatusRipa.PROCESSADA
        self.save()
    
    def marcar_finalizada(self) -> None:
        """Marca ripa como finalizada."""
        self.status = StatusRipa.FINALIZADA
        self.save()
    
    def definir_destino(self, destino: str) -> None:
        """Define o destino da ripa."""
        if destino not in dict(DestinoRipa.choices):
            raise ValueError(f"Destino inválido: {destino}")
        self.destino = destino
        self.save()

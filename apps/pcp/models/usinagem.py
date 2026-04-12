# apps/pcp/models/usinagem.py
"""
Modelos para Operações de Usinagem (Furação, Rasgos, etc.).

Responsabilidade: Representar operações de usinagem em peças.
Padrão: ORM apenas, sem lógica de negócio.
"""

from django.db import models
from decimal import Decimal
from apps.core.models import BaseModel
from apps.pcp.models.lote import PecaPCP


class TipoUsinagem(models.TextChoices):
    """Tipos de operações de usinagem."""
    
    FURO = "FURO", "Furação"
    RASGO = "RASGO", "Rasgo"
    REBAIXO = "REBAIXO", "Rebaixo"
    ENCAIXE = "ENCAIXE", "Encaixe"
    CHANFRO = "CHANFRO", "Chanfro"
    OUTRO = "OUTRO", "Outro"


class FaceUsinagem(models.TextChoices):
    """Faces da peça onde a operação ocorre."""
    
    FACE_A = "A", "Face A"
    FACE_B = "B", "Face B"
    FACE_C = "C", "Face C"
    FACE_D = "D", "Face D"
    FACE_E = "E", "Face E"
    FACE_F = "F", "Face F"


class StatusUsinagem(models.TextChoices):
    """Status da operação de usinagem."""
    
    PLANEJADA = "PLANEJADA", "Planejada"
    PROGRAMADA = "PROGRAMADA", "Programada"
    EXECUTADA = "EXECUTADA", "Executada"
    VERIFICADA = "VERIFICADA", "Verificada"
    CANCELADA = "CANCELADA", "Cancelada"


class Usinagem(BaseModel):
    """
    Operação de usinagem (furação, rasgo, etc.) em uma peça.
    Essencial para comunicação com máquinas CNC e controle de qualidade.
    """
    
    peca = models.ForeignKey(
        PecaPCP,
        on_delete=models.CASCADE,
        related_name='usinagens',
        verbose_name="Peça"
    )
    
    # Tipo de Operação
    tipo = models.CharField(
        max_length=20,
        choices=TipoUsinagem.choices,
        default=TipoUsinagem.FURO,
        verbose_name="Tipo de Operação"
    )
    
    # Localização
    face = models.CharField(
        max_length=1,
        choices=FaceUsinagem.choices,
        verbose_name="Face"
    )
    
    # Coordenadas (em mm, origem no canto inferior esquerdo)
    coordenada_x = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Coordenada X (mm)"
    )
    
    coordenada_y = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Coordenada Y (mm)"
    )
    
    # Parâmetros da Operação
    diametro_mm = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Diâmetro (mm)",
        help_text="Para furos e rebaixos"
    )
    
    profundidade_mm = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Profundidade (mm)"
    )
    
    largura_mm = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Largura (mm)",
        help_text="Para rasgos e encaixes"
    )
    
    comprimento_mm = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Comprimento (mm)",
        help_text="Para rasgos e encaixes"
    )
    
    # Quantidade
    quantidade = models.PositiveIntegerField(
        default=1,
        verbose_name="Quantidade de Operações",
        help_text="Ex: 2 furos idênticos"
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=StatusUsinagem.choices,
        default=StatusUsinagem.PLANEJADA,
        verbose_name="Status"
    )
    
    # Observações
    observacoes = models.TextField(
        blank=True,
        default="",
        verbose_name="Observações"
    )
    
    # Rastreamento
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Usinagem"
        verbose_name_plural = "Usinagens"
        indexes = [
            models.Index(fields=['peca'], name='usinagem_peca_idx'),
            models.Index(fields=['tipo'], name='usinagem_tipo_idx'),
            models.Index(fields=['face'], name='usinagem_face_idx'),
            models.Index(fields=['status'], name='usinagem_status_idx'),
        ]
        ordering = ['peca', 'face', 'coordenada_y', 'coordenada_x']
    
    def __str__(self):
        return f"{self.get_tipo_display()} - {self.peca.codigo_peca} (Face {self.face})"
    
    @property
    def descricao_completa(self) -> str:
        """Descrição completa da operação."""
        desc = f"{self.get_tipo_display()} em {self.get_face_display()}"
        
        if self.tipo == TipoUsinagem.FURO:
            desc += f" - Ø{self.diametro_mm}mm"
            if self.profundidade_mm:
                desc += f" x {self.profundidade_mm}mm"
        elif self.tipo == TipoUsinagem.RASGO:
            desc += f" - {self.largura_mm}x{self.comprimento_mm}mm"
        
        if self.quantidade > 1:
            desc += f" (x{self.quantidade})"
        
        return desc
    
    @property
    def coordenadas_str(self) -> str:
        """Coordenadas em formato legível."""
        return f"X:{self.coordenada_x:.1f} Y:{self.coordenada_y:.1f}"
    
    def marcar_programada(self) -> None:
        """Marca operação como programada."""
        self.status = StatusUsinagem.PROGRAMADA
        self.save()
    
    def marcar_executada(self) -> None:
        """Marca operação como executada."""
        self.status = StatusUsinagem.EXECUTADA
        self.save()
    
    def marcar_verificada(self) -> None:
        """Marca operação como verificada."""
        self.status = StatusUsinagem.VERIFICADA
        self.save()
    
    def cancelar(self) -> None:
        """Cancela a operação."""
        self.status = StatusUsinagem.CANCELADA
        self.save()

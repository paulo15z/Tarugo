# apps/pcp/models/roteiro.py
"""
Modelos de Domínio para Roteiros de Fabricação.

Responsabilidade: Representar a sequência de etapas de fabricação para cada peça.
Padrão: ORM apenas, sem lógica de negócio.
"""

from django.db import models
from apps.core.models import BaseModel
from apps.pcp.models.lote import PecaPCP


class EtapaRoteiro(models.TextChoices):
    """Etapas padrão de fabricação."""
    
    CORTE = "COR", "Corte"
    DUPLAGEM = "DUP", "Duplagem"
    BORDA = "BOR", "Aplicação de Borda"
    USINAGEM = "USI", "Usinagem"
    FURACAO = "FUR", "Furação"
    COLAGEM = "CQL", "Colagem"
    EXPEDICAO = "EXP", "Expedição"
    MONTAGEM = "MON", "Montagem"
    ACABAMENTO = "ACA", "Acabamento"
    CONTROLE = "CTL", "Controle de Qualidade"


class Roteiro(BaseModel):
    """
    Roteiro de fabricação para uma peça.
    Define a sequência de operações necessárias.
    """
    
    peca = models.OneToOneField(
        PecaPCP,
        on_delete=models.CASCADE,
        related_name='roteiro',
        verbose_name="Peça"
    )
    
    sequencia = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Sequência de Etapas",
        help_text="Lista ordenada de etapas: ['COR', 'BOR', 'FUR', 'EXP']"
    )
    
    tempo_estimado_minutos = models.PositiveIntegerField(
        default=0,
        verbose_name="Tempo Estimado (minutos)"
    )
    
    observacoes = models.TextField(
        blank=True,
        default="",
        verbose_name="Observações"
    )
    
    ativo = models.BooleanField(
        default=True,
        verbose_name="Ativo"
    )
    
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Roteiro"
        verbose_name_plural = "Roteiros"
        indexes = [
            models.Index(fields=['peca'], name='roteiro_peca_idx'),
            models.Index(fields=['ativo'], name='roteiro_ativo_idx'),
        ]
    
    def __str__(self):
        sequencia_str = " → ".join(self.sequencia) if self.sequencia else "Vazio"
        return f"Roteiro {self.peca.codigo_peca}: {sequencia_str}"
    
    @property
    def total_etapas(self) -> int:
        """Total de etapas no roteiro."""
        return len(self.sequencia)
    
    @property
    def etapas_descricao(self) -> str:
        """Descrição legível das etapas."""
        mapa = dict(EtapaRoteiro.choices)
        return " → ".join(mapa.get(e, e) for e in self.sequencia)
    
    def adicionar_etapa(self, etapa: str, posicao: int = None) -> None:
        """Adiciona uma etapa ao roteiro."""
        if etapa not in dict(EtapaRoteiro.values):
            raise ValueError(f"Etapa inválida: {etapa}")
        
        if posicao is None:
            self.sequencia.append(etapa)
        else:
            self.sequencia.insert(posicao, etapa)
        self.save()
    
    def remover_etapa(self, etapa: str) -> None:
        """Remove uma etapa do roteiro."""
        if etapa in self.sequencia:
            self.sequencia.remove(etapa)
            self.save()
    
    def reordenar_etapas(self, nova_sequencia: list) -> None:
        """Reordena as etapas do roteiro."""
        if set(nova_sequencia) != set(self.sequencia):
            raise ValueError("Nova sequência deve conter as mesmas etapas")
        self.sequencia = nova_sequencia
        self.save()

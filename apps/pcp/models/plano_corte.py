# apps/pcp/models/plano_corte.py
"""
Modelos para Planos de Corte.

Responsabilidade: Representar agrupamentos de peças para otimização de corte.
Padrão: ORM apenas, sem lógica de negócio.
"""

from django.db import models
from apps.core.models import BaseModel
from apps.pcp.models.lote import LotePCP, PecaPCP


class TipoPlanoCorte(models.TextChoices):
    """Tipos de plano de corte."""
    
    CHAPA = "03", "Chapa (MDF, Compensado)"
    PERFIL = "05", "Perfil (Madeira Maciça)"
    PORTA = "06", "Porta"
    GAVETA = "10", "Gaveta"
    TAMPONAMENTO = "11", "Tamponamento"
    FRENTE = "12", "Frente"
    LATERAL = "13", "Lateral"
    FUNDO = "14", "Fundo"
    PRATELEIRA = "15", "Prateleira"
    OUTRO = "99", "Outro"


class StatusPlanoCorte(models.TextChoices):
    """Status do plano de corte."""
    
    PLANEJADO = "PLANEJADO", "Planejado"
    APROVADO = "APROVADO", "Aprovado"
    EM_CORTE = "EM_CORTE", "Em Corte"
    FINALIZADO = "FINALIZADO", "Finalizado"
    CANCELADO = "CANCELADO", "Cancelado"


class PlanoCorte(BaseModel):
    """
    Plano de corte agrupa peças para otimização.
    Essencial para comunicação com máquinas de corte (CNC).
    """
    
    lote = models.ForeignKey(
        LotePCP,
        on_delete=models.CASCADE,
        related_name='planos_corte',
        verbose_name="Lote"
    )
    
    # Identificação
    codigo_plano = models.CharField(
        max_length=10,
        choices=TipoPlanoCorte.choices,
        verbose_name="Código do Plano",
        help_text="Ex: 03 (Chapa), 05 (Perfil), 06 (Porta)"
    )
    
    numero_sequencial = models.PositiveIntegerField(
        verbose_name="Número Sequencial",
        help_text="Ex: 03-001, 03-002"
    )
    
    # Descrição
    descricao = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="Descrição"
    )
    
    # Peças associadas
    pecas = models.ManyToManyField(
        PecaPCP,
        related_name='planos_corte',
        verbose_name="Peças",
        blank=True
    )
    
    # Métricas
    total_pecas = models.PositiveIntegerField(
        default=0,
        verbose_name="Total de Peças"
    )
    
    tempo_estimado_minutos = models.PositiveIntegerField(
        default=0,
        verbose_name="Tempo Estimado (minutos)"
    )
    
    # Status e Prioridade
    status = models.CharField(
        max_length=20,
        choices=StatusPlanoCorte.choices,
        default=StatusPlanoCorte.PLANEJADO,
        verbose_name="Status"
    )
    
    prioridade = models.PositiveIntegerField(
        default=0,
        verbose_name="Prioridade",
        help_text="0 = Baixa, 1 = Normal, 2 = Alta, 3 = Urgente"
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
    data_inicio_corte = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Data de Início do Corte"
    )
    data_fim_corte = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Data de Fim do Corte"
    )
    
    class Meta:
        verbose_name = "Plano de Corte"
        verbose_name_plural = "Planos de Corte"
        unique_together = ('lote', 'codigo_plano', 'numero_sequencial')
        indexes = [
            models.Index(fields=['lote'], name='plano_lote_idx'),
            models.Index(fields=['codigo_plano'], name='plano_codigo_idx'),
            models.Index(fields=['status'], name='plano_status_idx'),
            models.Index(fields=['prioridade'], name='plano_prioridade_idx'),
        ]
        ordering = ['prioridade', 'codigo_plano', 'numero_sequencial']
    
    def __str__(self):
        return f"Plano {self.codigo_plano}-{self.numero_sequencial:03d} ({self.total_pecas} peças)"
    
    @property
    def codigo_completo(self) -> str:
        """Código completo do plano (ex: 03-001)."""
        return f"{self.codigo_plano}-{self.numero_sequencial:03d}"
    
    @property
    def descricao_tipo(self) -> str:
        """Descrição do tipo de plano."""
        return dict(TipoPlanoCorte.choices).get(self.codigo_plano, "Desconhecido")
    
    def adicionar_peca(self, peca: PecaPCP) -> None:
        """Adiciona uma peça ao plano."""
        if not self.pecas.filter(id=peca.id).exists():
            self.pecas.add(peca)
            self.total_pecas = self.pecas.count()
            self.save()
    
    def remover_peca(self, peca: PecaPCP) -> None:
        """Remove uma peça do plano."""
        if self.pecas.filter(id=peca.id).exists():
            self.pecas.remove(peca)
            self.total_pecas = self.pecas.count()
            self.save()
    
    def aprovar(self) -> None:
        """Aprova o plano de corte."""
        self.status = StatusPlanoCorte.APROVADO
        self.save()
    
    def iniciar_corte(self) -> None:
        """Marca início do corte."""
        from django.utils import timezone
        self.status = StatusPlanoCorte.EM_CORTE
        self.data_inicio_corte = timezone.now()
        self.save()
    
    def finalizar_corte(self) -> None:
        """Marca fim do corte."""
        from django.utils import timezone
        self.status = StatusPlanoCorte.FINALIZADO
        self.data_fim_corte = timezone.now()
        self.save()
    
    def cancelar(self) -> None:
        """Cancela o plano de corte."""
        self.status = StatusPlanoCorte.CANCELADO
        self.save()
    
    @property
    def tempo_corte_real_minutos(self) -> int:
        """Calcula tempo real de corte em minutos."""
        if self.data_inicio_corte and self.data_fim_corte:
            delta = self.data_fim_corte - self.data_inicio_corte
            return int(delta.total_seconds() / 60)
        return 0

# apps/pcp/models/processamento.py
from django.db import models
from django.conf import settings
from django.utils import timezone


class ProcessamentoPCP(models.Model):
    """Histórico de processamentos do PCP"""

    id = models.CharField(max_length=8, primary_key=True, editable=False)
    nome_arquivo = models.CharField(max_length=255, verbose_name="Arquivo Original")
    lote = models.PositiveIntegerField(null=True, blank=True, verbose_name="Número do Lote")
    total_pecas = models.PositiveIntegerField(default=0, verbose_name="Total de Peças")
    
    # Controle de liberação para bipagem
    liberado_para_bipagem = models.BooleanField(default=False, verbose_name="Liberado para Bipagem")
    data_liberacao = models.DateTimeField(null=True, blank=True, verbose_name="Data de Liberação")
    
    # Controle de liberação para viagem (Expedição)
    liberado_para_viagem = models.BooleanField(default=False, verbose_name="Liberado para Viagem")
    data_liberacao_viagem = models.DateTimeField(null=True, blank=True, verbose_name="Data de Liberação Viagem")
    
    arquivo_saida = models.FileField(
        upload_to='pcp/outputs/%Y/%m/%d/',
        null=True,
        blank=True,
        verbose_name="Roteiro Gerado"
    )

    criado_em = models.DateTimeField(default=timezone.now, editable=False)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = "Processamento PCP"
        verbose_name_plural = "Processamentos PCP"
        ordering = ['-criado_em']

    def __str__(self):
        lote_str = f"Lote {self.lote}" if self.lote else "Sem lote"
        return f"{self.id} - {lote_str} ({self.total_pecas} peças)"
from django.db import models
from django.utils.timezone import now


class ProcessamentoPCP(models.Model):
    """Histórico de processamentos do Roteiro PCP"""
    id = models.CharField(max_length=8, primary_key=True)
    nome_arquivo = models.CharField(max_length=255)
    data = models.DateTimeField(default=now)
    total_pecas = models.PositiveIntegerField()
    arquivo_saida = models.CharField(max_length=255)

    class Meta:
        ordering = ['-data']
        verbose_name = 'Processamento PCP'
        verbose_name_plural = 'Processamentos PCP'

    def __str__(self):
        return f"{self.id} - {self.nome_arquivo} ({self.total_pecas} peças)"
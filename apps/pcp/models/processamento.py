# apps/pcp/models/processamento.py
from django.db import models
from django.utils.timezone import now


class ProcessamentoPCP(models.Model):
    """Histórico de processamentos do Roteiro PCP"""
    id = models.CharField(max_length=8, primary_key=True)
    nome_arquivo = models.CharField(max_length=255)
    data = models.DateTimeField(default=now)
    total_pecas = models.PositiveIntegerField(default=0)
    
    
    arquivo_saida = models.FileField(
        upload_to='pcp/outputs/%Y/%m/%d/',
        blank=True,
        null=True,
        max_length=500,          # mais espaço para paths longos
    )

    # Campos futuros úteis 
   # usuario = models.ForeignKey(
   #     'core.User',             # ajuste se o usuário for em outro app
   #     on_delete=models.SET_NULL,
   #     null=True,
   #     blank=True,
   #     related_name='processamentos_pcp'
   # )
    status = models.CharField(
        max_length=20,
        default='processado',
        choices=[
            ('processado', 'Processado'),
            ('erro', 'Erro'),
            ('pendente', 'Pendente'),
        ]
    )

    class Meta:
        ordering = ['-data']
        verbose_name = 'Processamento PCP'
        verbose_name_plural = 'Processamentos PCP'
        db_table = 'pcp_processamentopcp'

    def __str__(self):
        return f"{self.id} - {self.nome_arquivo} ({self.total_pecas} peças)"

    @property
    def download_url(self):
        """ para frontend """
        if self.arquivo_saida:
            return self.arquivo_saida.url
        return None
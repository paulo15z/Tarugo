# apps/bipagem/models/evento_bipagem.py
from django.db import models

from .peca import Peca


class EventoBipagem(models.Model):
    """Histórico imutável de cada bipagem"""
    
    peca = models.ForeignKey(Peca, on_delete=models.CASCADE, related_name='bipagens')
    momento = models.DateTimeField(auto_now_add=True, db_index=True)
    usuario = models.CharField(max_length=100, default='SISTEMA')
    localizacao = models.CharField(max_length=100, blank=True)
    
    # Log de sincronização (Gêmeo Digital)
    erro_sincronia = models.TextField(null=True, blank=True, help_text="Erro ao tentar abater estoque automaticamente")

    class Meta:
        verbose_name = "Evento de Bipagem"
        verbose_name_plural = "Eventos de Bipagem"
        ordering = ['-momento']
        indexes = [models.Index(fields=['peca', 'momento'])]

    def __str__(self):
        return f"{self.peca.id_peca} — {self.momento.strftime('%d/%m %H:%M')}"
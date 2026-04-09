from django.db import models

from apps.core.models import BaseModel

from apps.bipagem.domain.operacional import EscopoOperacional, EtapaOperacional, MovimentoOperacional
from apps.pcp.models import PecaPCP


class EventoOperacional(BaseModel):
    etapa = models.CharField(max_length=40, choices=EtapaOperacional.choices(), db_index=True)
    movimento = models.CharField(max_length=20, choices=MovimentoOperacional.choices(), db_index=True)
    escopo = models.CharField(
        max_length=20,
        choices=EscopoOperacional.choices(),
        default=EscopoOperacional.PECA_PCP,
        db_index=True,
    )
    peca = models.ForeignKey(
        PecaPCP,
        on_delete=models.CASCADE,
        related_name="eventos_operacionais",
        null=True,
        blank=True,
    )
    envio = models.ForeignKey(
        "bipagem.EnvioExpedicao",
        on_delete=models.SET_NULL,
        related_name="eventos_operacionais",
        null=True,
        blank=True,
    )
    quantidade = models.PositiveIntegerField(default=1)
    usuario = models.CharField(max_length=100, default="SISTEMA")
    localizacao = models.CharField(max_length=100, blank=True)
    lote_pid = models.CharField(max_length=8, blank=True, db_index=True)
    codigo_modulo = models.CharField(max_length=50, blank=True, db_index=True)
    ambiente_nome = models.CharField(max_length=100, blank=True)
    destino = models.CharField(max_length=100, blank=True)
    observacao = models.TextField(blank=True)
    momento = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "Evento Operacional"
        verbose_name_plural = "Eventos Operacionais"
        ordering = ["-momento"]
        indexes = [
            models.Index(fields=["etapa", "movimento", "momento"], name="bipa_evtop_eta_mov_idx"),
            models.Index(fields=["lote_pid", "etapa"], name="bipa_evtop_lote_eta_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.etapa} {self.movimento} {self.lote_pid or '--'}"

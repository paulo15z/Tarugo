from django.db import models

from apps.core.models import BaseModel

from apps.bipagem.domain.operacional import StatusEnvioExpedicao
from apps.pcp.models import PecaPCP


class EnvioExpedicao(BaseModel):
    codigo = models.CharField(max_length=30, unique=True, db_index=True)
    descricao = models.CharField(max_length=255, blank=True)
    transportadora = models.CharField(max_length=150, blank=True)
    placa_veiculo = models.CharField(max_length=20, blank=True)
    motorista = models.CharField(max_length=150, blank=True)
    ajudante = models.CharField(max_length=150, blank=True)
    destino_principal = models.CharField(max_length=255, blank=True)
    destinos_secundarios = models.JSONField(default=list, blank=True)
    observacoes = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=StatusEnvioExpedicao.choices(),
        default=StatusEnvioExpedicao.ABERTO,
        db_index=True,
    )
    recebido_em = models.DateTimeField(null=True, blank=True)
    liberado_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Viagem de Expedicao"
        verbose_name_plural = "Viagens de Expedicao"
        ordering = ["-criado_em"]

    def __str__(self) -> str:
        return self.codigo


class EnvioExpedicaoItem(BaseModel):
    envio = models.ForeignKey(EnvioExpedicao, on_delete=models.CASCADE, related_name="itens")
    peca = models.ForeignKey(PecaPCP, on_delete=models.PROTECT, related_name="itens_envio")
    quantidade = models.PositiveIntegerField(default=1)
    lote_pid = models.CharField(max_length=8, db_index=True)
    cliente_nome = models.CharField(max_length=255, blank=True)
    ambiente_nome = models.CharField(max_length=100, blank=True)
    modulo_nome = models.CharField(max_length=100, blank=True)
    codigo_modulo = models.CharField(max_length=50, blank=True)

    class Meta:
        verbose_name = "Item de Envio"
        verbose_name_plural = "Itens de Envio"
        ordering = ["ambiente_nome", "modulo_nome", "codigo_modulo", "id"]
        constraints = [
            models.UniqueConstraint(fields=["envio", "peca"], name="bipagem_envio_item_unico"),
        ]

    def __str__(self) -> str:
        return f"{self.envio.codigo} - {self.peca.codigo_peca}"

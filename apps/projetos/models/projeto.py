from django.conf import settings
from django.db import models

from apps.pedidos.models import AmbientePedido, Pedido
from apps.projetos.domain.status import ProjetoStatus


class Projeto(models.Model):
    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.CASCADE,
        related_name="projetos",
        verbose_name="Pedido",
    )
    ambiente_pedido = models.OneToOneField(
        AmbientePedido,
        on_delete=models.CASCADE,
        related_name="projeto",
        verbose_name="Ambiente do Pedido",
    )
    nome_projeto = models.CharField(max_length=255, verbose_name="Nome do Projeto")
    status = models.CharField(
        max_length=32,
        choices=ProjetoStatus.choices,
        default=ProjetoStatus.AGUARDANDO_DEFINICOES,
        db_index=True,
        verbose_name="Status",
    )
    distribuidor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="projetos_distribuidos",
    )
    projetista = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="projetos_designados",
    )
    liberador_tecnico = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="projetos_para_liberacao",
    )
    data_inicio_prevista = models.DateField(null=True, blank=True)
    data_fim_prevista = models.DateField(null=True, blank=True)
    data_inicio_real = models.DateTimeField(null=True, blank=True)
    data_fim_real = models.DateTimeField(null=True, blank=True)
    observacoes = models.TextField(blank=True, default="")
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="projetos_criados",
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Projeto"
        verbose_name_plural = "Projetos"
        ordering = ["-criado_em"]
        indexes = [
            models.Index(fields=["status", "-criado_em"], name="proj_status_idx"),
            models.Index(fields=["projetista", "status"], name="proj_proj_status_idx"),
            models.Index(fields=["pedido", "status"], name="proj_pedido_status_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.nome_projeto} ({self.pedido.numero_pedido})"

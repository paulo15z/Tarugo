from django.conf import settings
from django.db import models


class AnexoProjeto(models.Model):
    projeto = models.ForeignKey(
        "projetos.Projeto",
        on_delete=models.CASCADE,
        related_name="anexos",
        verbose_name="Projeto",
    )
    arquivo = models.FileField(upload_to="projetos/anexos/%Y/%m/%d/")
    nome_arquivo = models.CharField(max_length=255, blank=True, default="")
    tipo_anexo = models.CharField(max_length=50, blank=True, default="")
    descricao = models.TextField(blank=True, default="")
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="anexos_projetos_uploaded",
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Anexo de Projeto"
        verbose_name_plural = "Anexos de Projetos"
        ordering = ["-criado_em"]

    def __str__(self) -> str:
        return self.nome_arquivo or self.arquivo.name

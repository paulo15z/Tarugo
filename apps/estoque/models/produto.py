from django.db import models


class Produto(models.Model):
    nome = models.CharField(max_length=255, verbose_name="Nome")
    sku = models.CharField(max_length=100, unique=True, verbose_name="SKU")
    quantidade = models.PositiveIntegerField(default=0, verbose_name="Quantidade em estoque")
    estoque_minimo = models.PositiveIntegerField(default=0, verbose_name="Estoque mínimo")

    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    atualizado_em = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        ordering = ["nome"]
        verbose_name = "Produto"
        verbose_name_plural = "Produtos"

    def __str__(self):
        return f"{self.nome} ({self.sku})"
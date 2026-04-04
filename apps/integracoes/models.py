# apps/integracoes/models.py
from django.db import models
from apps.estoque.models.produto import Produto

class MapeamentoMaterial(models.Model):
    """
    Vínculo entre o nome do material no Dinabox e o Produto no Estoque.
    Essencial para o Gêmeo Digital: garante que o consumo digital reflita no estoque físico.
    """
    nome_dinabox = models.CharField(
        max_length=255, 
        unique=True, 
        verbose_name="Nome no Dinabox",
        help_text="Exatamente como aparece no CSV/HTML do Dinabox"
    )
    produto = models.ForeignKey(
        Produto, 
        on_delete=models.CASCADE, 
        related_name="mapeamentos",
        verbose_name="Produto Vinculado"
    )
    
    fator_conversao = models.DecimalField(
        max_digits=10, 
        decimal_places=4, 
        default=1.0,
        verbose_name="Fator de Conversão",
        help_text="Multiplicador para o consumo (ex: 1.1 para 10% de margem de erro/perda)"
    )

    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Mapeamento de Material"
        verbose_name_plural = "Mapeamentos de Materiais"

    def __str__(self):
        return f"{self.nome_dinabox} -> {self.produto.nome}"

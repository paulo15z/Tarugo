from django.db import models
from django.utils import timezone


class Pedido(models.Model):
    """Pedido que vem do comercial (ex: número 573 - sergio possenti)"""
    
    numero_pedido = models.CharField(max_length=50, unique=True, db_index=True)  # 573
    cliente_nome = models.CharField(max_length=255, db_index=True)
    data_criacao = models.DateTimeField(default=timezone.now)
    data_importacao = models.DateTimeField(auto_now_add=True) #vou mudar dps, o pedido nasce bem antes

    class Meta:
        verbose_name = "Pedido"
        verbose_name_plural = "Pedidos"
        ordering = ['-data_criacao']

    def __str__(self):
        return f"Pedido {self.numero_pedido} - {self.cliente_nome}"

    @property
    def total_pecas(self):
        return self.ordens_producao.aggregate(total=models.Sum('total_pecas'))['total'] or 0

    @property
    def pecas_bipadas(self):
        return self.ordens_producao.aggregate(bipadas=models.Sum('pecas_bipadas'))['bipadas'] or 0
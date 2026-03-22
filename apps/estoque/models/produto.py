from django.db import models

# bora

class Produto(models.Model):
    nome = models.CharField(max_length=255)
    sku = models.CharField(max_length=100, unique=True)
    quantidade = models.IntegerField(default=0)
    estoque_minimo = models.IntegerField(default=0)
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nome
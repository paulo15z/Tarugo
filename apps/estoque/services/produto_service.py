# apps/estoque/services/produto_service.py
from apps.estoque.models import Produto


def criar_produto(data: dict) -> Produto:
    """Cria um novo produto - mantido para compatibilidade total com a API DRF"""
    return Produto.objects.create(**data)
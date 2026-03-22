from apps.estoque.models.produto import Produto

def criar_produto(data: dict) -> Produto:
    return Produto.objects.create(**data)

def adicionar_estoque(produto: Produto, quantidade: int):
    produto.quantidade += quantidade
    produto.save()

def remover_estoque(produto: Produto, quantidade: int):
    if produto.quantidade < quantidade:
        raise ValueError("Estoque Insuficiente!")
    
    produto.quantidade -= quantidade
    produto.save()

    
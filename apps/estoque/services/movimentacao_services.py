from django.db import transaction #poderoso

from apps.estoque.models import Produto, Movimentacao #traz os models
from apps.estoque.services.schemas import MovimentacaoSchema #traz o validas


@transaction.atomic
def processar_movimentacao(data: dict):
    schema = MovimentacaoSchema(**data)

    produto = Produto.objects.select_for_update().get(id=schema.produto_id)
    # select_for_update trava o banco pra n ter 2 saidas (escalar)

    if schema.tipo == 'entrada':
        produto.quantidade += schema.quantidade

    elif schema.tipo == 'saida':
        if produto.quantidade < schema.quantidade:
            raise ValueError('Estoque insuficiente!')
        
        produto.quantidade -= schema.quantidade

    produto.save()


    Movimentacao.objects.create(
        produto = produto,
        tipo = schema.tipo,
        quantidade = schema.quantidade
    )

    return produto


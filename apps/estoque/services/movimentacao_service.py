# apps/estoque/services/movimentacao_service.py
from django.db import transaction
from django.core.exceptions import ValidationError

from apps.estoque.models import Produto, Movimentacao
from apps.estoque.schemas.movimentacao import MovimentacaoCreateSchema
from apps.estoque.selectors.produto_selector import ProdutoSelector


class MovimentacaoService:
    """Service central do MVP - toda regra de negócio fica aqui"""

    @staticmethod
    @transaction.atomic
    def processar_movimentacao(schema: MovimentacaoCreateSchema, usuario=None) -> Movimentacao:
        # Lock de concorrência (evita race condition)
        produto = ProdutoSelector.get_produto_para_movimentacao(schema.produto_id)

        # Validação de negócio (além da validação do Pydantic)
        if schema.tipo == "saida" and produto.quantidade < schema.quantidade:
            raise ValidationError(f"Estoque insuficiente. Disponível: {produto.quantidade}")

        # Atualiza estoque
        if schema.tipo == "entrada" or schema.tipo == "ajuste" and schema.quantidade > 0:
            produto.quantidade += schema.quantidade
        elif schema.tipo == "saida":
            produto.quantidade -= schema.quantidade
        elif schema.tipo == "ajuste":
            produto.quantidade = schema.quantidade  # ajuste absoluto

        produto.save()

        # Registra movimentação
        movimentacao = Movimentacao.objects.create(
            produto=produto,
            tipo=schema.tipo,
            quantidade=schema.quantidade,
            usuario=usuario,
            observacao=schema.observacao,
        )

        return movimentacao
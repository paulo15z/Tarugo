# apps/estoque/services/movimentacao_service.py
from django.db import transaction
from django.contrib.auth import get_user_model

from apps.estoque.models import Produto, Movimentacao
from apps.estoque.services.schemas import MovimentacaoSchema, AjusteLoteSchema

User = get_user_model()


class MovimentacaoService:
    """
    Service central para todas as regras de negócio de movimentação de estoque.
    Segue o padrão Tarugo: toda lógica de negócio fica aqui (nunca nas views).
    """

    @staticmethod
    @transaction.atomic
    def processar_movimentacao(data: dict, usuario_id: int | None = None) -> Produto:
        """
        Processa uma única movimentação de estoque.
        """
        schema = MovimentacaoSchema(usuario_id=usuario_id, **data)

        produto = Produto.objects.select_for_update().get(id=schema.produto_id)

        if schema.tipo == 'entrada':
            produto.quantidade += schema.quantidade
        elif schema.tipo == 'saida':
            if produto.quantidade < schema.quantidade:
                raise ValueError(
                    f'Estoque insuficiente. Disponível: {produto.quantidade}, solicitado: {schema.quantidade}.'
                )
            produto.quantidade -= schema.quantidade
        elif schema.tipo == 'ajuste':
            produto.quantidade = schema.quantidade
        elif schema.tipo == 'transferencia':
            if produto.quantidade < schema.quantidade:
                raise ValueError(
                    f'Estoque insuficiente para transferência. Disponível: {produto.quantidade}.'
                )
            produto.quantidade -= schema.quantidade

        produto.save()

        usuario = User.objects.get(id=schema.usuario_id) if schema.usuario_id else None

        Movimentacao.objects.create(
            produto=produto,
            tipo=schema.tipo,
            quantidade=schema.quantidade,
            usuario=usuario,
            observacao=schema.observacao,
        )

        return produto

    @staticmethod
    @transaction.atomic
    def processar_ajuste_em_lote(data: dict, usuario_id: int | None = None) -> list[Produto]:
        """
        Processa múltiplas movimentações em lote (atômico).
        """
        schema = AjusteLoteSchema(**data)
        produtos_atualizados = []

        for mov in schema.movimentacoes:
            produto = MovimentacaoService.processar_movimentacao(
                mov.model_dump(), 
                usuario_id=usuario_id
            )
            produtos_atualizados.append(produto)

        return produtos_atualizados
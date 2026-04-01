# apps/estoque/services/movimentacao_service.py
from django.db import transaction
from django.core.exceptions import ValidationError

from apps.estoque.models import Produto, Movimentacao
from apps.estoque.selectors.produto_selector import ProdutoSelector


class MovimentacaoService:
    """Service central do MVP - toda regra de negócio fica aqui"""

    @staticmethod
    @transaction.atomic
    def processar_movimentacao(data: dict, usuario=None) -> Movimentacao:
        """
        Processa uma única movimentação.
        Recebe dict validado pelo DRF serializer.
        """
        produto_id = data['produto_id']
        tipo = data['tipo']
        quantidade = data['quantidade']
        observacao = data.get('observacao')

        # Lock de concorrência (evita race condition)
        produto = ProdutoSelector.get_produto_para_movimentacao(produto_id)

        # Validações de negócio
        if tipo == 'saida' and produto.quantidade < quantidade:
            raise ValidationError(
                f"Estoque insuficiente. Disponível: {produto.quantidade}, solicitado: {quantidade}."
            )

        if tipo == 'ajuste' and quantidade < 0:
            raise ValidationError("Quantidade de ajuste não pode ser negativa.")

        # Atualiza estoque conforme tipo
        if tipo == 'entrada':
            produto.quantidade += quantidade
        elif tipo == 'saida':
            produto.quantidade -= quantidade
        elif tipo == 'ajuste':
            # Ajuste absoluto: define o valor exato do estoque
            produto.quantidade = quantidade
        # 'transferencia' não altera estoque diretamente neste endpoint

        produto.save()

        movimentacao = Movimentacao.objects.create(
            produto=produto,
            tipo=tipo,
            quantidade=quantidade,
            usuario=usuario,
            observacao=observacao,
        )

        return movimentacao

    @staticmethod
    @transaction.atomic
    def processar_ajuste_em_lote(data: dict, usuario=None) -> list[Produto]:
        """
        Processa múltiplas movimentações de uma vez.
        Recebe dict com chave 'movimentacoes' (lista de dicts validados pelo DRF).
        Retorna lista de produtos atualizados.
        """
        movimentacoes_data = data['movimentacoes']

        if not movimentacoes_data:
            raise ValidationError("A lista de movimentações não pode estar vazia.")

        produtos_atualizados = []

        for mov_data in movimentacoes_data:
            movimentacao = MovimentacaoService.processar_movimentacao(mov_data, usuario=usuario)
            produtos_atualizados.append(movimentacao.produto)

        return produtos_atualizados
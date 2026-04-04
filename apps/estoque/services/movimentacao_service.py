# apps/estoque/services/movimentacao_service.py
from django.db import transaction
from django.core.exceptions import ValidationError

from apps.estoque.models import Produto, Movimentacao, SaldoMDF
from apps.estoque.selectors.produto_selector import ProdutoSelector
from apps.estoque.domain.tipos import FamiliaProduto
from apps.estoque.services.schemas import MovimentacaoSchema


class MovimentacaoService:
    """Service central do MVP - toda regra de negócio fica aqui"""

    @staticmethod
    @transaction.atomic
    def processar_movimentacao(data: dict, usuario=None) -> Movimentacao:
        # Valida os dados de entrada com o schema Pydantic
        schema = MovimentacaoSchema(**data)
        produto_id = schema.produto_id
        tipo = schema.tipo
        quantidade = schema.quantidade
        espessura = schema.espessura
        observacao = schema.observacao
        """
        Processa uma única movimentação.
        Recebe dict validado pelo DRF serializer.
        """


        # Lock de concorrência (evita race condition)
        produto = ProdutoSelector.get_produto_para_movimentacao(produto_id)
        familia = produto.categoria.familia

        # Lógica específica para MDF (por espessura)
        if familia == FamiliaProduto.MDF:
            if not espessura:
                raise ValidationError("Espessura é obrigatória para produtos da família MDF.")
            
            saldo_mdf, _ = SaldoMDF.objects.get_or_create(
                produto=produto, 
                espessura=espessura
            )

            if tipo == 'saida' and saldo_mdf.quantidade < quantidade:
                raise ValidationError(
                    f"Estoque insuficiente para {espessura}mm. Disponível: {saldo_mdf.quantidade}, solicitado: {quantidade}."
                )

            if tipo == 'ajuste' and quantidade < 0:
                raise ValidationError("Quantidade de ajuste não pode ser negativa.")

            if tipo == 'entrada':
                saldo_mdf.quantidade += quantidade
            elif tipo == 'saida':
                saldo_mdf.quantidade -= quantidade
            elif tipo == 'ajuste':
                saldo_mdf.quantidade = quantidade
            elif tipo == 'transferencia':
                # TODO: Implementar lógica de transferência entre localizações ou produtos
                raise ValidationError("Tipo de movimentação 'transferencia' ainda não implementado.")
            
            saldo_mdf.save()
            
            # Opcional: Manter produto.quantidade como a soma de todas as espessuras
            # produto.quantidade = SaldoMDF.objects.filter(produto=produto).aggregate(total=models.Sum('quantidade'))['total'] or 0
            # produto.save()

        else:
            # Lógica para demais itens (Ferragens, Fitas, etc.)
            if tipo == 'saida' and produto.quantidade < quantidade:
                raise ValidationError(
                    f"Estoque insuficiente. Disponível: {produto.quantidade}, solicitado: {quantidade}."
                )

            if tipo == 'ajuste' and quantidade < 0:
                raise ValidationError("Quantidade de ajuste não pode ser negativa.")

            if tipo == 'entrada':
                produto.quantidade += quantidade
            elif tipo == 'saida':
                produto.quantidade -= quantidade
            elif tipo == 'ajuste':
                produto.quantidade = quantidade
            elif tipo == 'transferencia':
                # TODO: Implementar lógica de transferência entre localizações ou produtos
                raise ValidationError("Tipo de movimentação 'transferencia' ainda não implementado.")
            
            produto.save()

        movimentacao = Movimentacao.objects.create(
            produto=produto,
            tipo=tipo,
            espessura=espessura,
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
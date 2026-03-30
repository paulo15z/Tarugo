from django.db import transaction
from django.contrib.auth import get_user_model

from apps.estoque.models import Produto, Movimentacao
from apps.estoque.services.schemas import MovimentacaoSchema, AjusteLoteSchema

User = get_user_model()


@transaction.atomic
def processar_movimentacao(data: dict, usuario_id: int | None = None) -> Produto:
    """
    Processa uma única movimentação de estoque.

    - Valida dados via Pydantic (MovimentacaoSchema)
    - Trava o produto com select_for_update para evitar race condition
    - Aplica a regra de negócio conforme o tipo
    - Registra a movimentação com usuário e observação
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
        # Ajuste define o valor absoluto do estoque
        produto.quantidade = schema.quantidade

    elif schema.tipo == 'transferencia':
        # Transferência funciona como saída — origem perde estoque
        # A entrada no destino deve ser registrada separadamente
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


@transaction.atomic
def processar_ajuste_em_lote(data: dict, usuario_id: int | None = None) -> list[Produto]:
    """
    Processa múltiplas movimentações em uma única transação atômica.
    Se qualquer uma falhar, todas são revertidas.
    """
    schema = AjusteLoteSchema(**data)

    produtos_atualizados = []
    for mov in schema.movimentacoes:
        produto = processar_movimentacao(mov.model_dump(), usuario_id=usuario_id)
        produtos_atualizados.append(produto)

    return produtos_atualizados

from django.db import transaction
from django.db.models import Sum

from apps.estoque.models import Produto, Reserva


def get_quantidade_reservada(produto_id: int) -> int:
    """Retorna o total reservado (ativo) de um produto."""
    resultado = Reserva.objects.filter(
        produto_id=produto_id,
        status='ativa',
    ).aggregate(total=Sum('quantidade'))
    return resultado['total'] or 0


def get_saldo_disponivel(produto: Produto) -> int:
    """Saldo real menos o que já está reservado para projetos."""
    return produto.quantidade - get_quantidade_reservada(produto.id)


@transaction.atomic
def criar_reserva(produto_id: int, projeto: str, quantidade: int, usuario_id=None, observacao=None) -> Reserva:
    produto = Produto.objects.select_for_update().get(id=produto_id)

    disponivel = get_saldo_disponivel(produto)
    if quantidade > disponivel:
        raise ValueError(
            f'Quantidade indisponível. Saldo livre: {disponivel} '
            f'(total: {produto.quantidade}, já reservado: {produto.quantidade - disponivel}).'
        )

    from django.contrib.auth import get_user_model
    User = get_user_model()
    usuario = User.objects.get(id=usuario_id) if usuario_id else None

    return Reserva.objects.create(
        produto=produto,
        projeto=projeto,
        quantidade=quantidade,
        usuario=usuario,
        observacao=observacao,
        status='ativa',
    )


@transaction.atomic
def cancelar_reserva(reserva_id: int) -> Reserva:
    reserva = Reserva.objects.select_for_update().get(id=reserva_id)
    if reserva.status != 'ativa':
        raise ValueError(f'Reserva já está com status "{reserva.status}" e não pode ser cancelada.')
    reserva.status = 'cancelada'
    reserva.save()
    return reserva


@transaction.atomic
def consumir_reserva(reserva_id: int) -> Reserva:
    """Marca reserva como consumida e registra saída no estoque."""
    from apps.estoque.services.movimentacao_services import processar_movimentacao

    reserva = Reserva.objects.select_for_update().select_related('produto', 'usuario').get(id=reserva_id)
    if reserva.status != 'ativa':
        raise ValueError(f'Reserva já está com status "{reserva.status}".')

    processar_movimentacao(
        data={
            'produto_id': reserva.produto_id,
            'quantidade': reserva.quantidade,
            'tipo': 'saida',
            'observacao': f'Consumo da reserva #{reserva.id} — Projeto: {reserva.projeto}',
        },
        usuario_id=reserva.usuario_id,
    )

    reserva.status = 'consumida'
    reserva.save()
    return reserva

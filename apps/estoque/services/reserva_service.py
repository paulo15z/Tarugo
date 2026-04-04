# apps/estoque/services/reserva_service.py
from django.db import transaction
from django.core.exceptions import ValidationError
from apps.estoque.models import Produto, Reserva
from apps.estoque.selectors.produto_selector import ProdutoSelector
from apps.bipagem.models.pedido import Pedido

class ReservaService:
    """
    Service para gerenciar reservas de estoque por projeto.
    Garante que o material de um projeto aprovado não seja consumido por outro.
    """

    @staticmethod
    @transaction.atomic
    def criar_reserva(pedido_id: int, produto_id: int, quantidade: int, usuario=None) -> Reserva:
        """
        Cria uma reserva de material para um pedido específico.
        """
        if quantidade <= 0:
            raise ValidationError("A quantidade da reserva deve ser maior que zero.")

        produto = ProdutoSelector.get_produto_para_movimentacao(produto_id)
        pedido = Pedido.objects.get(id=pedido_id)

        # Verifica se há estoque disponível (estoque real - reservas ativas)
        reservas_ativas = Reserva.objects.filter(produto=produto, status='ativa').aggregate(
            total=models.Sum('quantidade'))['total'] or 0
        
        disponivel = produto.quantidade - reservas_ativas

        if disponivel < quantidade:
            raise ValidationError(
                f"Estoque insuficiente para reserva. Disponível: {disponivel}, Solicitado: {quantidade}."
            )

        reserva = Reserva.objects.create(
            produto=produto,
            pedido=pedido,
            quantidade=quantidade,
            usuario=usuario,
            status='ativa'
        )

        return reserva

    @staticmethod
    @transaction.atomic
    def consumir_reserva(reserva_id: int, usuario=None):
        """
        Marca uma reserva como consumida (quando o material é bipado na produção).
        """
        reserva = Reserva.objects.select_for_update().get(id=reserva_id)
        if reserva.status != 'ativa':
            raise ValidationError(f"Reserva não pode ser consumida. Status atual: {reserva.status}")

        reserva.status = 'consumida'
        reserva.save(update_fields=['status', 'atualizado_em'])
        return reserva

    @staticmethod
    @transaction.atomic
    def cancelar_reserva(reserva_id: int, usuario=None):
        """
        Libera o material reservado de volta para o estoque geral.
        """
        reserva = Reserva.objects.select_for_update().get(id=reserva_id)
        reserva.status = 'cancelada'
        reserva.save(update_fields=['status', 'atualizado_em'])
        return reserva

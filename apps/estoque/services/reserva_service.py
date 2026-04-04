# apps/estoque/services/reserva_service.py
from django.db import models, transaction
from pydantic import ValidationError
from apps.estoque.services.schemas import ReservaCreateSchema
from apps.estoque.models import Produto, Reserva, SaldoMDF
from apps.estoque.selectors.produto_selector import ProdutoSelector
from apps.estoque.domain.tipos import FamiliaProduto
from apps.bipagem.models.pedido import Pedido

class ReservaService:
    """
    Service para gerenciar reservas de estoque por projeto.
    Garante que o material de um projeto aprovado não seja consumido por outro.
    """

    @staticmethod
    @transaction.atomic
    def criar_reserva(data: dict, usuario=None) -> Reserva:
        schema = ReservaCreateSchema(**data)
        produto_id = schema.produto_id
        pedido_id = schema.pedido_id
        quantidade = schema.quantidade
        espessura = schema.espessura
        observacao = schema.observacao
        """
        Cria uma reserva de material para um pedido específico.
        Valida contra o estoque físico disponível.
        """

        produto = ProdutoSelector.get_produto_para_movimentacao(produto_id)
        pedido = Pedido.objects.get(id=pedido_id)
        familia = produto.categoria.familia

        if familia == FamiliaProduto.MDF:
            if not espessura:
                raise ValidationError("Espessura é obrigatória para reservar produtos da família MDF.")
            
            saldo_mdf, _ = SaldoMDF.objects.get_or_create(
                produto=produto,
                espessura=espessura,
                defaults={\'quantidade\': 0}
            )
            if saldo_mdf.quantidade < quantidade:
                raise ValidationError(
                    f"Estoque insuficiente para {espessura}mm. Disponível: {saldo_mdf.quantidade}, solicitado: {quantidade}."
                )
        else:
            if produto.quantidade < quantidade:
                raise ValidationError(
                    f"Estoque insuficiente. Disponível: {produto.quantidade}, solicitado: {quantidade}."
                )
        reserva = Reserva.objects.create(
            produto=produto,
            pedido=pedido,
            espessura=espessura,
            quantidade=quantidade,
            usuario=usuario,
            observacao=observacao,
            status=\'ativa\'
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

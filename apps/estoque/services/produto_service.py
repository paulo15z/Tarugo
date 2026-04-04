# apps/estoque/services/produto_service.py
from typing import Optional
from decimal import Decimal

from django.db import transaction
from pydantic import ValidationError

from apps.estoque.models.produto import Produto
from apps.estoque.models.categoria import CategoriaProduto
from apps.estoque.models.saldo_mdf import SaldoMDF
from apps.estoque.domain.tipos import FamiliaProduto
from apps.estoque.schemas.produto_schema import (
    ProdutoCreateSchema,
    ProdutoUpdateSchema,
)


class ProdutoService:
    """Service central para regras de negócio de produtos (padrão Tarugo)"""

    @staticmethod
    @transaction.atomic
    def criar_produto(data: dict) -> Produto:
        """Cria um novo produto com validação Pydantic"""
        try:
            schema = ProdutoCreateSchema(**data)
        except ValidationError as e:
            raise ValueError(f"Erro de validação dos dados: {e.errors()}")

        try:
            categoria = CategoriaProduto.objects.get(id=schema.categoria_id)
        except CategoriaProduto.DoesNotExist:
            raise ValueError(f"Categoria ID {schema.categoria_id} não encontrada.")

        # Se a família não foi informada, inferimos da categoria
        familia = schema.familia or categoria.familia

        produto = Produto.objects.create(
            nome=schema.nome,
            sku=schema.sku,
            categoria=categoria,
            unidade_medida=schema.unidade_medida,
            estoque_minimo=schema.estoque_minimo,
            preco_custo=schema.preco_custo,
            lote=schema.lote,
            localizacao=schema.localizacao,
            atributos_especificos=schema.atributos_especificos or {},
        )

        # Inicializa espessuras padrão se for MDF
        if familia == FamiliaProduto.MDF:
            espessuras_padrao = [6, 15, 18, 25]
            for esp in espessuras_padrao:
                SaldoMDF.objects.get_or_create(
                    produto=produto,
                    espessura=esp,
                    defaults={'quantidade': 0}
                )

        return produto

    @staticmethod
    @transaction.atomic
    def atualizar_produto(produto_id: int, data: dict) -> Produto:
        """Atualiza um produto existente"""
        try:
            produto = Produto.objects.select_for_update().get(id=produto_id)
        except Produto.DoesNotExist:
            raise ValueError(f"Produto ID {produto_id} não encontrado.")

        schema = ProdutoUpdateSchema(**data)

        for field, value in schema.model_dump(exclude_unset=True).items():
            if field == "atributos_especificos" and value is not None:
                current = getattr(produto, field) or {}
                current.update(value)
                setattr(produto, field, current)
            else:
                setattr(produto, field, value)

        produto.save()
        return produto
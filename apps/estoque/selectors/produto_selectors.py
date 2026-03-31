# apps/estoque/selectors/produto_selectors.py
from django.db.models import F, QuerySet

from apps.estoque.models import Produto


def get_saldo_atual(produto_id: int) -> Produto:
    """Retorna o produto com o saldo atual de estoque."""
    return Produto.objects.get(id=produto_id)


def get_produtos_baixo_estoque() -> QuerySet:
    """Retorna produtos cujo estoque está no nível mínimo ou abaixo."""
    return Produto.objects.filter(quantidade__lte=F('estoque_minimo')).order_by('quantidade')


def get_produtos_com_saldo_baixo(quantidade_minima: int = 10) -> QuerySet:
    """
    Versão mais flexível para o dashboard (pode usar estoque_minimo ou valor fixo).
    Prioriza o campo estoque_minimo do model quando disponível.
    """
    return Produto.objects.filter(
        quantidade__lte=F('estoque_minimo') if hasattr(Produto, 'estoque_minimo') else quantidade_minima,
        ativo=True
    ).order_by('quantidade')


def get_total_produtos_ativos() -> int:
    """Retorna o total de produtos ativos."""
    return Produto.objects.filter(ativo=True).count()
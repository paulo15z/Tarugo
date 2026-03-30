from django.db.models import F, QuerySet

from apps.estoque.models import Produto, Movimentacao


def get_saldo_atual(produto_id: int) -> Produto:
    """Retorna o produto com o saldo atual de estoque."""
    return Produto.objects.get(id=produto_id)


def get_produtos_baixo_estoque() -> QuerySet:
    """Retorna produtos cujo estoque está no nível mínimo ou abaixo."""
    return Produto.objects.filter(quantidade__lte=F('estoque_minimo')).order_by('quantidade')


def get_movimentacoes_recentes(produto_id: int | None = None, limite: int = 20) -> QuerySet:
    """Retorna as movimentações mais recentes, opcionalmente filtradas por produto."""
    qs = Movimentacao.objects.select_related('produto', 'usuario')

    if produto_id:
        qs = qs.filter(produto_id=produto_id)

    return qs.order_by('-criado_em')[:limite]


def listar_movimentacoes(
    produto_id: int | None = None,
    tipo: str | None = None,
    usuario_id: int | None = None,
    data_inicio=None,
    data_fim=None,
) -> QuerySet:
    """
    Selector principal de movimentações com todos os filtros disponíveis.
    Retorna queryset — paginação fica na view.
    """
    qs = Movimentacao.objects.select_related('produto', 'usuario')

    if produto_id:
        qs = qs.filter(produto_id=produto_id)

    if tipo:
        qs = qs.filter(tipo=tipo)

    if usuario_id:
        qs = qs.filter(usuario_id=usuario_id)

    if data_inicio:
        qs = qs.filter(criado_em__gte=data_inicio)

    if data_fim:
        qs = qs.filter(criado_em__lte=data_fim)

    return qs.order_by('-criado_em')

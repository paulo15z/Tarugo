from apps.estoque.models import Movimentacao


#função reutilizavel para listar movimentaççoes 
def listar_movimentacoes(
        produto_id: int | None = None,
        data_inicio=None,
        data_fim=None,
):
    qs =Movimentacao.objects.all()

    if produto_id:
        qs = qs.filter(produto_id=produto_id)

    if data_inicio:
        qs = qs.filter(criado_em__gte=data_inicio)

    if data_fim:
        qs = qs.filter(criado_em__lte=data_fim)

    return qs.order_by('-criado_em')

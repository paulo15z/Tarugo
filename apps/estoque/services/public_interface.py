from apps.estoque.domain.tipos import FamiliaProduto
from apps.estoque.models import Produto
from apps.estoque.selectors.disponibilidade_selector import get_disponibilidade_por_produto


class EstoquePublicService:
    """
    Interface publica do Estoque para consumo por outros apps (ex.: PCP).
    Evita acesso direto aos models fora do dominio de estoque.
    """

    @staticmethod
    def consultar_disponibilidade(
        produto_id: int | None = None,
        sku: str | None = None,
        familia: str | None = None,
        espessura: int | None = None,
    ) -> list[dict]:
        produtos = Produto.objects.select_related("categoria").filter(ativo=True)
        if produto_id:
            produtos = produtos.filter(id=produto_id)
        if sku:
            produtos = produtos.filter(sku=sku)
        if familia:
            produtos = produtos.filter(categoria__familia=familia)

        resultado = []
        for produto in produtos:
            if produto.categoria.familia == FamiliaProduto.MDF and espessura is None:
                for esp in produto.saldos_mdf.values_list("espessura", flat=True):
                    resultado.append(get_disponibilidade_por_produto(produto, espessura=esp))
            else:
                resultado.append(get_disponibilidade_por_produto(produto, espessura=espessura))
        return resultado

    @staticmethod
    def get_alertas_baixo_estoque() -> list[dict]:
        alertas = []
        produtos = Produto.objects.select_related("categoria").filter(ativo=True)
        for produto in produtos:
            if produto.categoria.familia == FamiliaProduto.MDF:
                for esp in produto.saldos_mdf.values_list("espessura", flat=True):
                    disponibilidade = get_disponibilidade_por_produto(produto, espessura=esp)
                    if disponibilidade["saldo_disponivel"] <= produto.estoque_minimo:
                        alertas.append(disponibilidade)
            else:
                disponibilidade = get_disponibilidade_por_produto(produto)
                if disponibilidade["saldo_disponivel"] <= produto.estoque_minimo:
                    alertas.append(disponibilidade)
        return alertas

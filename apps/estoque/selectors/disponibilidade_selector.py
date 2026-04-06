from django.db.models import Sum

from apps.estoque.domain.tipos import FamiliaProduto
from apps.estoque.models import Produto, Reserva, SaldoMDF


def get_saldo_fisico(produto: Produto, espessura: int | None = None) -> int:
    familia = produto.categoria.familia
    if familia == FamiliaProduto.MDF:
        if espessura is None:
            return (
                SaldoMDF.objects.filter(produto=produto).aggregate(total=Sum("quantidade")).get("total")
                or 0
            )
        saldo = SaldoMDF.objects.filter(produto=produto, espessura=espessura).first()
        return saldo.quantidade if saldo else 0
    return int(produto.quantidade or 0)


def get_saldo_reservado(produto: Produto, espessura: int | None = None) -> int:
    reservas = Reserva.objects.filter(produto=produto, status="ativa")
    if espessura is not None:
        reservas = reservas.filter(espessura=espessura)
    return reservas.aggregate(total=Sum("quantidade")).get("total") or 0


def get_saldo_disponivel(produto: Produto, espessura: int | None = None) -> int:
    saldo_fisico = get_saldo_fisico(produto, espessura=espessura)
    saldo_reservado = get_saldo_reservado(produto, espessura=espessura)
    return max(0, saldo_fisico - saldo_reservado)


def get_disponibilidade_por_produto(produto: Produto, espessura: int | None = None) -> dict:
    saldo_fisico = get_saldo_fisico(produto, espessura=espessura)
    saldo_reservado = get_saldo_reservado(produto, espessura=espessura)
    return {
        "produto_id": produto.id,
        "produto_nome": produto.nome,
        "sku": produto.sku,
        "familia": produto.categoria.familia,
        "espessura": espessura,
        "saldo_fisico": saldo_fisico,
        "saldo_reservado": saldo_reservado,
        "saldo_disponivel": max(0, saldo_fisico - saldo_reservado),
    }


def get_disponibilidade_resumida(produto: Produto) -> dict:
    if produto.categoria.familia == FamiliaProduto.MDF:
        por_espessura = []
        for esp in produto.saldos_mdf.values_list("espessura", flat=True):
            por_espessura.append(get_disponibilidade_por_produto(produto, espessura=esp))
        return {
            "produto_id": produto.id,
            "familia": produto.categoria.familia,
            "saldo_fisico": sum(item["saldo_fisico"] for item in por_espessura),
            "saldo_reservado": sum(item["saldo_reservado"] for item in por_espessura),
            "saldo_disponivel": sum(item["saldo_disponivel"] for item in por_espessura),
            "por_espessura": por_espessura,
        }

    base = get_disponibilidade_por_produto(produto)
    return {
        "produto_id": produto.id,
        "familia": produto.categoria.familia,
        "saldo_fisico": base["saldo_fisico"],
        "saldo_reservado": base["saldo_reservado"],
        "saldo_disponivel": base["saldo_disponivel"],
        "por_espessura": [],
    }

from apps.bipagem.schemas.bipagem_schema import PecaOutput


def map_peca_to_output(peca) -> PecaOutput:
    return PecaOutput(
        id=peca.id_peca,
        descricao=peca.descricao,
        status=peca.status,
        destino=peca.destino if peca.destino else None,
        pedido_id=getattr(
            peca.modulo.ordem_producao.pedido,
            "id",
            None
        )
    )

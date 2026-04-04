from django.db import transaction
from django.utils import timezone
from typing import Dict, Any

from apps.bipagem.models import Peca, EventoBipagem, LoteProducao
from apps.bipagem.schemas.bipagem_schema import (
    BipagemInput,
    BipagemOutput
)
from apps.bipagem.mappers.peca_mapper import map_peca_to_output
from apps.bipagem.domain.tipos import StatusPeca

@transaction.atomic
def registrar_bipagem(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Registra a bipagem de uma peça, validando o estado e persistindo o evento.
    Agora suporta validação por LoteProducao.
    """
    try:
        payload = BipagemInput(**data)
    except Exception as e:
        return BipagemOutput(
            sucesso=False,
            mensagem="Dados de entrada inválidos",
            erro=str(e)
        ).model_dump()

    # 1. Buscar peça com lock para evitar concorrência
    # Se lote_producao_id for fornecido, filtramos por ele para garantir que a peça pertence ao lote
    query = Peca.objects.select_for_update().select_related("modulo__ordem_producao__pedido", "lote_producao")
    
    if payload.lote_producao_id:
        query = query.filter(id_peca=payload.codigo_peca, lote_producao_id=payload.lote_producao_id)
    else:
        query = query.filter(id_peca=payload.codigo_peca)
    
    peca = query.order_by("-id").first()

    if not peca:
        msg = "Peça não encontrada"
        if payload.lote_producao_id:
            msg += f" no lote informado ({payload.lote_producao_id})"
        return BipagemOutput(
            sucesso=False,
            mensagem=msg,
            erro=f"Código {payload.codigo_peca} não existe no sistema ou não pertence ao lote."
        ).model_dump()

    # 2. Validar estados impeditivos (Pedido e Lote)
    pedido = peca.modulo.ordem_producao.pedido
    if pedido.bloqueado:
        return BipagemOutput(
            sucesso=False,
            mensagem="Bipagem bloqueada pelo PCP",
            erro=f"O pedido {pedido.numero_pedido} está bloqueado para novas bipagens."
        ).model_dump()

    if peca.lote_producao and not peca.lote_producao.liberado_para_bipagem:
        return BipagemOutput(
            sucesso=False,
            mensagem="Lote não liberado",
            erro=f"O lote {peca.lote_producao.numero_lote} ainda não foi liberado para produção."
        ).model_dump()

    if peca.status in [StatusPeca.CONCLUIDA, StatusPeca.CANCELADA]:
        return BipagemOutput(
            sucesso=False,
            mensagem=f"Peça já está {peca.status.lower()}",
            peca=map_peca_to_output(peca)
        ).model_dump()

    agora = timezone.now()

    # 3. Idempotência: se já estiver bipada, apenas retorna sucesso
    if peca.status == StatusPeca.BIPADA:
        return BipagemOutput(
            sucesso=True,
            mensagem="Peça já foi bipada anteriormente",
            repetido=True,
            peca=map_peca_to_output(peca)
        ).model_dump()

    # 4. Registrar evento de bipagem
    evento = EventoBipagem.objects.create(
        peca=peca,
        usuario=payload.usuario,
        localizacao=payload.localizacao,
        momento=agora
    )

    # 5. Determinar destino com base no plano de corte (Lógica MVP)
    if peca.plano_corte and "Corte" in peca.plano_corte:
        peca.destino = "Corte"
    elif peca.plano_corte and "Bordo" in peca.plano_corte:
        peca.destino = "Bordo"
    else:
        peca.destino = "Desconhecido"

    # 6. Atualizar status da peça
    peca.status = StatusPeca.BIPADA
    peca.data_bipagem = agora
    peca.save(update_fields=["status", "data_bipagem", "destino"])

    # 7. Gêmeo Digital: REMOVIDO TEMPORARIAMENTE PARA SPRINT 1
    # No Sprint 2, isso será substituído pela orquestração com Reservas.
    # try:
    #     GemeoDigitalService.processar_consumo_peca(peca.id, usuario=payload.usuario)
    # except Exception as e:
    #     evento.erro_sincronia = str(e)
    #     evento.save(update_fields=["erro_sincronia"])

    return BipagemOutput(
        sucesso=True,
        mensagem="Bipagem realizada com sucesso",
        peca=map_peca_to_output(peca)
    ).model_dump()


@transaction.atomic
def toggle_bloqueio_pedido(pedido_id: int) -> bool:
    """Alterna o estado de bloqueio de um pedido (Bipagem)"""
    from apps.bipagem.models.pedido import Pedido
    pedido = Pedido.objects.select_for_update().get(id=pedido_id)
    pedido.bloqueado = not pedido.bloqueado
    pedido.save(update_fields=['bloqueado'])
    return pedido.bloqueado

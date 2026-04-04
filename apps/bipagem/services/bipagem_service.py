from django.db import transaction
from django.utils import timezone
from typing import Dict, Any

from apps.bipagem.models import Peca, EventoBipagem
from apps.bipagem.schemas.bipagem_schema import (
    BipagemInput,
    BipagemOutput
)
from apps.bipagem.mappers.peca_mapper import map_peca_to_output
from apps.bipagem.domain.tipos import StatusPeca
from apps.integracoes.services.gemeo_digital_service import GemeoDigitalService

@transaction.atomic
def registrar_bipagem(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Registra a bipagem de uma peça, validando o estado e persistindo o evento.
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
    peca = (
        Peca.objects
        .select_for_update()
        .select_related("modulo__ordem_producao__pedido")
        .filter(id_peca=payload.codigo_peca)
        .order_by("-id") # Pega a mais recente se houver duplicidade de ID em lotes diferentes
        .first()
    )

    if not peca:
        return BipagemOutput(
            sucesso=False,
            mensagem="Peça não encontrada",
            erro=f"Código {payload.codigo_peca} não existe no sistema"
        ).model_dump()

    # 2. Validar estados impeditivos
    pedido = peca.modulo.ordem_producao.pedido
    if pedido.bloqueado:
        return BipagemOutput(
            sucesso=False,
            mensagem="Bipagem bloqueada pelo PCP",
            erro=f"O pedido {pedido.numero_pedido} está bloqueado para novas bipagens."
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

    # 7. Gêmeo Digital: Sincronizar consumo com o estoque físico
    try:
        GemeoDigitalService.processar_consumo_peca(peca.id, usuario=payload.usuario)
    except Exception as e:
        # Registra o erro no evento para o Dashboard de Discrepâncias
        evento.erro_sincronia = str(e)
        evento.save(update_fields=["erro_sincronia"])

    return BipagemOutput(
        sucesso=True,
        mensagem="Bipagem realizada com sucesso",
        peca=map_peca_to_output(peca)
    ).model_dump()


@transaction.atomic
def toggle_bloqueio_pedido(pedido_id: int) -> bool:
    """Alterna o estado de bloqueio de um pedido"""
    from apps.bipagem.models import Pedido
    pedido = Pedido.objects.select_for_update().get(id=pedido_id)
    pedido.bloqueado = not pedido.bloqueado
    pedido.save(update_fields=['bloqueado'])
    return pedido.bloqueado

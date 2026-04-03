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
    if peca.status in [StatusPeca.CONCLUIDA, StatusPeca.CANCELADA]:
        return BipagemOutput(
            sucesso=False,
            mensagem=f"Peça já está {peca.status.lower()}",
            peca=map_peca_to_output(peca)
        ).model_dump()

    agora = timezone.now()

    # 3. Idempotência: se já estiver bipada, apenas retorna sucesso
    if peca.status == StatusPeca.BIPADA:
        # Ainda assim registramos o evento para histórico de tentativas/re-bipagem se necessário,
        # mas aqui vamos apenas retornar que já foi feito.
        return BipagemOutput(
            sucesso=True,
            mensagem="Peça já foi bipada anteriormente",
            repetido=True,
            peca=map_peca_to_output(peca)
        ).model_dump()

    # 4. Registrar evento de bipagem
    EventoBipagem.objects.create(
        peca=peca,
        usuario=payload.usuario,
        localizacao=payload.localizacao,
        momento=agora
    )

    # 5. Atualizar status da peça
    peca.status = StatusPeca.BIPADA
    peca.data_bipagem = agora
    peca.save(update_fields=["status", "data_bipagem"])

    return BipagemOutput(
        sucesso=True,
        mensagem="Bipagem realizada com sucesso",
        peca=map_peca_to_output(peca)
    ).model_dump()

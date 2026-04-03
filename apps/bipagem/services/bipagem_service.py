from django.db import transaction
from django.utils import timezone

from apps.bipagem.models import Peca, EventoBipagem
from apps.bipagem.schemas.bipagem_schema import (
    BipagemInput,
    BipagemOutput,
    PecaOutput
)
from apps.bipagem.mappers.peca_mapper import map_peca_to_output




def registrar_bipagem(data: dict) -> dict:

    # 1. Validação de entrada (Pydantic)
    try:
        payload = BipagemInput(**data)
    except Exception:
        return BipagemOutput(
            sucesso=False,
            erro="Dados inválidos"
        ).dict()

    try:
        with transaction.atomic():

            # lock + performance
            peca = (
                Peca.objects
                .select_for_update()
                .select_related("modulo__ordem_producao__pedido")
                .filter(id_peca=payload.codigo_peca)
                .order_by("-id")
                .first()
            )

            if not peca:
                return BipagemOutput(
                    sucesso=False,
                    erro="Peça não encontrada"
                ).dict()

            # estados inválidos
            if peca.status in ["CONCLUIDA", "CANCELADA"]:
                return BipagemOutput(
                    sucesso=False,
                    erro=f"Peça já está {peca.status.lower()}"
                ).dict()

            agora = timezone.now()

            # idempotência
            if peca.status == "BIPADA":
                return BipagemOutput(
                    sucesso=True,
                    mensagem="Peça já bipada",
                    repetido=True,
                    peca= map_peca_to_output(peca)
                ).dict()

            # registrar evento
            EventoBipagem.objects.create(
                peca=peca,
                usuario=payload.usuario or "DESCONHECIDO",
                localizacao=payload.localizacao,
                data_hora=agora
            )

            # atualizar peça
            peca.status = "BIPADA"
            peca.data_bipagem = agora
            peca.save(update_fields=["status", "data_bipagem"])

            return BipagemOutput(
                sucesso=True,
                mensagem="Bipagem registrada",
                peca= map_peca_to_output(peca)
            ).dict()

    except Exception:
        return BipagemOutput(
            sucesso=False,
            erro="Erro interno ao registrar bipagem"
        ).dict()

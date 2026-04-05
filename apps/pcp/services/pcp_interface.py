"""
Interface pública do módulo PCP.

Regra: outros apps (bipagem, estoque, etc.) só podem importar do PCP através
deste módulo. Nunca importar ProcessamentoPCP, models ou services internos
diretamente de fora do app pcp.

Exporta apenas o necessário para consumo externo. Uma hora ou outra vai dar problema de bidirecionalidade
"""
from __future__ import annotations

from typing import TypedDict


# ---------------------------------------------------------------------------
# Tipos públicos (evita que o caller precise conhecer os models do PCP)
# ---------------------------------------------------------------------------

class LoteInfo(TypedDict):
    id: str                    # PID do processamento
    lote: int | None           # Número do lote (ex: 500)
    nome_arquivo: str
    criado_em: str             # ISO 8601
    liberado_para_bipagem: bool
    liberado_para_viagem: bool
    data_liberacao: str | None
    total_pecas: int


# ---------------------------------------------------------------------------
# Queries públicas
# ---------------------------------------------------------------------------

def get_lotes_liberados_para_bipagem() -> list[LoteInfo]:
    """
    Retorna todos os lotes que o PCP liberou para bipagem.
    Usado pelo app bipagem para montar o dashboard operacional.
    """
    from apps.pcp.models.processamento import ProcessamentoPCP

    qs = ProcessamentoPCP.objects.filter(
        liberado_para_bipagem=True
    ).order_by('-criado_em')

    return [_to_lote_info(p) for p in qs]


def get_numeros_lotes_liberados() -> list[str]:
    """
    Retorna apenas os números de lote liberados para bipagem.
    Forma mais leve para queries de filtragem no bipagem.
    """
    from apps.pcp.models.processamento import ProcessamentoPCP

    return list(
        ProcessamentoPCP.objects
        .filter(liberado_para_bipagem=True)
        .values_list('lote', flat=True)
    )


def get_lote_info(pid: str) -> LoteInfo | None:
    """Retorna informações de um processamento específico."""
    from apps.pcp.models.processamento import ProcessamentoPCP

    try:
        p = ProcessamentoPCP.objects.get(id=pid)
        return _to_lote_info(p)
    except ProcessamentoPCP.DoesNotExist:
        return None


# ---------------------------------------------------------------------------
# Comandos públicos (ações que o PCP executa, disparadas por outros apps)
# ---------------------------------------------------------------------------

def liberar_lote_para_bipagem(pid: str, usuario=None) -> dict:
    """
    Libera um lote processado para bipagem.
    Chama o service interno do PCP e retorna resultado padronizado.
    """
    from apps.pcp.services.processamento_service import ProcessamentoPCPService

    return ProcessamentoPCPService.liberar_lote(pid, usuario=usuario)


def bloquear_lote_bipagem(pid: str, motivo: str = "") -> dict:
    """
    Bloqueia um lote que estava liberado para bipagem.
    Mantém o histórico de importação intacto — apenas suspende novas bipagens.
    """
    from apps.pcp.models.processamento import ProcessamentoPCP
    from apps.bipagem.models import LoteProducao

    try:
        proc = ProcessamentoPCP.objects.get(id=pid)
        proc.liberado_para_bipagem = False
        proc.data_liberacao = None
        proc.save(update_fields=['liberado_para_bipagem', 'data_liberacao'])

        # Propaga o bloqueio para os LoteProducao vinculados
        LoteProducao.objects.filter(processamento_pcp=proc).update(
            liberado_para_bipagem=False,
            bloqueado_motivo=motivo or "Bloqueado pelo PCP"
        )

        return {'sucesso': True, 'mensagem': f'Lote {proc.lote} bloqueado para bipagem.'}
    except ProcessamentoPCP.DoesNotExist:
        return {'sucesso': False, 'mensagem': 'Processamento não encontrado.'}


def reabrir_lote_bipagem(pid: str) -> dict:
    """
    Reabre um lote previamente bloqueado, sem reimportar as peças.
    Apenas sinaliza como liberado novamente.
    """
    from django.utils import timezone
    from apps.pcp.models.processamento import ProcessamentoPCP
    from apps.bipagem.models import LoteProducao

    try:
        proc = ProcessamentoPCP.objects.get(id=pid)

        if not proc.liberado_para_bipagem:
            proc.liberado_para_bipagem = True
            proc.data_liberacao = timezone.now()
            proc.save(update_fields=['liberado_para_bipagem', 'data_liberacao'])

        # Propaga reabertura para os LoteProducao vinculados
        LoteProducao.objects.filter(processamento_pcp=proc).update(
            liberado_para_bipagem=True,
            bloqueado_motivo=None
        )

        return {'sucesso': True, 'mensagem': f'Lote {proc.lote} reaberto para bipagem.'}
    except ProcessamentoPCP.DoesNotExist:
        return {'sucesso': False, 'mensagem': 'Processamento não encontrado.'}


# ---------------------------------------------------------------------------
# Helpers privados
# ---------------------------------------------------------------------------

def _to_lote_info(p) -> LoteInfo:
    return LoteInfo(
        id=p.id,
        lote=p.lote,
        nome_arquivo=p.nome_arquivo,
        criado_em=p.criado_em.isoformat(),
        liberado_para_bipagem=p.liberado_para_bipagem,
        liberado_para_viagem=p.liberado_para_viagem,
        data_liberacao=p.data_liberacao.isoformat() if p.data_liberacao else None,
        total_pecas=p.total_pecas,
    )
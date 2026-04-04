from typing import List, Optional
from apps.pcp.models.lote import LotePCP, PecaPCP


def get_lote_by_pid(pid: str) -> Optional[LotePCP]:
    """Busca lote completo por PID (com prefetch para performance)"""
    return (
        LotePCP.objects.prefetch_related('ambientes__modulos__pecas')
        .filter(pid=pid)
        .first()
    )


def list_lotes_pendentes() -> List[LotePCP]:
    """Lotes ainda não finalizados"""
    return LotePCP.objects.filter(status__in=['pendente', 'em_producao']).order_by(
        '-data_processamento'
    )


def get_pecas_do_lote(lote_id: int) -> List[PecaPCP]:
    """Todas as peças de um lote (para tela de bipagem)"""
    return PecaPCP.objects.select_related('modulo__ambiente__lote').filter(
        modulo__ambiente__lote_id=lote_id
    )


def get_peca_by_id(peca_id: int) -> Optional[PecaPCP]:
    """Busca única peça com contexto completo"""
    return PecaPCP.objects.select_related('modulo__ambiente__lote').filter(id=peca_id).first()
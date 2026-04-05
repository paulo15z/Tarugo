"""
Consultas de lotes para o app de bipagem.

Regra de dependência:
  - Usa pcp.services.pcp_interface (interface pública) para dados do PCP
  - Nunca importa ProcessamentoPCP diretamente
"""
from __future__ import annotations

from django.db.models import Count, Q

from apps.bipagem.models import LoteProducao, Peca
from apps.bipagem.domain.tipos import StatusPeca


# ---------------------------------------------------------------------------
# Lotes de Produção (entidade do bipagem, criada pelo importador PCP)
# ---------------------------------------------------------------------------

def get_lotes_por_pedido(numero_pedido: str):
    """Retorna QuerySet de LoteProducao que contêm peças de um pedido."""
    return (
        LoteProducao.objects
        .filter(pecas__modulo__ordem_producao__pedido__numero_pedido=numero_pedido)
        .distinct()
        .order_by('-data_criacao')
    )


def get_pecas_por_lote_producao(lote_id: int) -> list:
    """Retorna todas as peças de um LoteProducao específico."""
    return list(
        Peca.objects
        .filter(lote_producao_id=lote_id)
        .select_related('modulo__ordem_producao__pedido', 'lote_producao')
        .order_by('modulo__ordem_producao__pedido__numero_pedido', 'id_peca')
    )


def get_todos_lotes_ativos() -> list[dict]:
    """
    Retorna todos os LoteProducao com resumo de progresso.
    Usado pela API interna do bipagem.
    """
    lotes = LoteProducao.objects.annotate(
        total_pecas=Count('pecas'),
        pecas_bipadas=Count('pecas', filter=Q(pecas__status=StatusPeca.BIPADA))
    ).order_by('-data_criacao')

    resultado = []
    for lote in lotes:
        total = lote.total_pecas or 0
        bipadas = lote.pecas_bipadas or 0
        percentual = (bipadas / total * 100) if total > 0 else 0

        resultado.append({
            'id': lote.id,
            'numero_lote': lote.numero_lote,
            'processamento_id': lote.processamento_pcp_id,
            'liberado': lote.liberado_para_bipagem,
            'total_pecas': total,
            'pecas_bipadas': bipadas,
            'percentual': round(percentual, 1),
            'data_criacao': lote.data_criacao,
        })
    return resultado


# ---------------------------------------------------------------------------
# Dashboard operacional — agrupamento por Lote Base
# ---------------------------------------------------------------------------

def get_lotes_dashboard() -> list[dict]:
    """
    Monta o dashboard operacional de bipagem agrupado por lote base.

    Lote base = parte numérica antes do '-' em numero_lote_pcp.
    Exemplo: "500-01", "500-02" → lote base "500".

    Retorna apenas peças cujo LoteProducao está liberado para bipagem,
    sem importar nada do app pcp diretamente.
    """
    from apps.pcp.services.pcp_interface import get_numeros_lotes_liberados

    lotes_liberados = get_numeros_lotes_liberados()

    if not lotes_liberados:
        return []

    # Monta filtro para numero_lote_pcp exato ou sub-lotes (ex: "500" ou "500-01")
    q_filter = Q()
    for lote in lotes_liberados:
        lote_str = str(lote)
        q_filter |= Q(numero_lote_pcp=lote_str) | Q(numero_lote_pcp__startswith=f"{lote_str}-")

    pecas_qs = (
        Peca.objects
        .filter(q_filter)
        .select_related('modulo__ordem_producao__pedido')
        .values(
            'numero_lote_pcp',
            'modulo__ordem_producao__pedido__numero_pedido',
            'modulo__ordem_producao__pedido__cliente_nome',
            'modulo__ordem_producao__pedido__bloqueado',
            'status',
        )
    )

    lotes_map: dict[str, dict] = {}

    for p in pecas_qs:
        lote_composto = p['numero_lote_pcp'] or ''
        lote_base = lote_composto.split('-')[0].strip() if lote_composto else 'SEM LOTE'

        if lote_base not in lotes_map:
            lotes_map[lote_base] = {
                'lote': lote_base,
                'numero_pedido': p['modulo__ordem_producao__pedido__numero_pedido'] or '---',
                'cliente_nome': p['modulo__ordem_producao__pedido__cliente_nome'] or 'Cliente Desconhecido',
                'bloqueado': p['modulo__ordem_producao__pedido__bloqueado'],
                'total': 0,
                'bipadas': 0,
                'sub_lotes': set(),
            }

        lotes_map[lote_base]['total'] += 1
        if p['status'] == StatusPeca.BIPADA:
            lotes_map[lote_base]['bipadas'] += 1
        if lote_composto:
            lotes_map[lote_base]['sub_lotes'].add(lote_composto)

    resultado = []
    for lb in lotes_map.values():
        total = lb['total']
        bipadas = lb['bipadas']
        sub_lotes_unicos = sorted(lb['sub_lotes'])
        sub_lotes_display = ' / '.join(sub_lotes_unicos[:5])
        if len(sub_lotes_unicos) > 5:
            sub_lotes_display += '...'

        resultado.append({
            'lote': lb['lote'],
            'sub_lotes_display': sub_lotes_display,
            'numero_pedido': lb['numero_pedido'],
            'cliente_nome': lb['cliente_nome'],
            'bloqueado': lb['bloqueado'],
            'total': total,
            'bipadas': bipadas,
            'bipadas_neg': -bipadas,
            'percentual': round((bipadas / total * 100), 1) if total > 0 else 0,
        })

    resultado.sort(key=lambda x: x['lote'], reverse=True)
    return resultado
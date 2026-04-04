from django.db.models import Count, Q
from typing import List, Optional
from apps.bipagem.models import LoteProducao, Peca, Pedido
from apps.bipagem.domain.tipos import StatusPeca

def get_lotes_por_pedido(numero_pedido: str) -> List[LoteProducao]:
    """
    Retorna todos os lotes de produção que contêm peças de um determinado pedido.
    """
    return LoteProducao.objects.filter(
        pecas__modulo__ordem_producao__pedido__numero_pedido=numero_pedido
    ).distinct().order_by('-data_criacao')

def get_pecas_por_lote_producao(lote_id: int) -> List[Peca]:
    """
    Retorna todas as peças associadas a um lote de produção específico.
    """
    return Peca.objects.filter(
        lote_producao_id=lote_id
    ).select_related(
        'modulo__ordem_producao__pedido',
        'lote_producao'
    ).order_by('modulo__ordem_producao__pedido__numero_pedido', 'id_peca')

def get_todos_lotes_ativos() -> List[dict]:
    """
    Retorna todos os lotes com resumo de progresso.
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
            'data_criacao': lote.data_criacao
        })
    return resultado

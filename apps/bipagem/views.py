from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q

from apps.bipagem.models import Pedido, Modulo, Peca
from apps.pcp.models.processamento import ProcessamentoPCP
from apps.bipagem.selectors.progresso import (
    get_resumo_pedido, 
    get_modulos_pedido, 
    get_pecas_modulo
)
from apps.bipagem.domain.tipos import StatusPeca

def _extrair_lote_base(lote_composto: str) -> str:
    """Extrai o lote base de um lote composto (ex: '500-01' -> '500')."""
    if not lote_composto:
        return "SEM LOTE"
    return lote_composto.split('-')[0].strip()

@login_required
def index(request):
    """Página principal do scanner de bipagem (Dashboard Operacional por LOTE BASE)."""
    # 1. Buscar apenas os lotes que foram explicitamente liberados no PCP
    lotes_liberados = ProcessamentoPCP.objects.filter(
        liberado_para_bipagem=True
    ).values_list('lote', flat=True)
    
    # 2. Filtrar as peças que pertencem a esses lotes
    # O numero_lote_pcp pode ser "500" ou "500-01"
    # Precisamos de uma query que pegue ambos
    q_filter = Q()
    for lote in lotes_liberados:
        q_filter |= Q(numero_lote_pcp=str(lote)) | Q(numero_lote_pcp__startswith=f"{lote}-")
    
    if not lotes_liberados:
        return render(request, 'bipagem/index.html', {'lotes': []})

    pecas_qs = Peca.objects.filter(q_filter).select_related('modulo__ordem_producao__pedido').values(
        'numero_lote_pcp',
        'modulo__ordem_producao__pedido__numero_pedido',
        'modulo__ordem_producao__pedido__cliente_nome',
        'status'
    )
    
    # Agrupamento manual por Lote Base para garantir unicidade absoluta
    lotes_base_map = {}
    for p in pecas_qs:
        lote_composto = p['numero_lote_pcp']
        lote_base = _extrair_lote_base(lote_composto)
        
        if lote_base not in lotes_base_map:
            lotes_base_map[lote_base] = {
                'lote_base': lote_base,
                'numero_pedido': p['modulo__ordem_producao__pedido__numero_pedido'] or "---",
                'cliente_nome': p['modulo__ordem_producao__pedido__cliente_nome'] or "Cliente Desconhecido",
                'total': 0,
                'bipadas': 0,
                'sub_lotes': set() # Usando set para evitar repetições
            }
        
        lotes_base_map[lote_base]['total'] += 1
        if p['status'] == StatusPeca.BIPADA:
            lotes_base_map[lote_base]['bipadas'] += 1
        
        if lote_composto:
            lotes_base_map[lote_base]['sub_lotes'].add(lote_composto)

    lotes_finais = []
    for lb in lotes_base_map.values():
        total = lb['total']
        bipadas = lb['bipadas']
        percentual = (bipadas / total * 100) if total > 0 else 0
        
        # Ordenar sub-lotes e pegar apenas os únicos
        sub_lotes_unicos = sorted(list(lb['sub_lotes']))
        sub_lotes_display = " / ".join(sub_lotes_unicos[:5])
        if len(sub_lotes_unicos) > 5:
            sub_lotes_display += "..."

        lotes_finais.append({
            'lote': lb['lote_base'],
            'sub_lotes_display': sub_lotes_display,
            'numero_pedido': lb['numero_pedido'],
            'cliente_nome': lb['cliente_nome'],
            'total': total,
            'bipadas': bipadas,
            'bipadas_neg': -bipadas,
            'percentual': round(percentual, 1)
        })
    
    lotes_finais.sort(key=lambda x: x['lote'], reverse=True)
    return render(request, 'bipagem/index.html', {'lotes': lotes_finais})

@login_required
def pedidos_list(request):
    return index(request)

@login_required
def pedido_detalhe(request, numero_pedido):
    """Detalhes de um LOTE BASE."""
    lote_base = numero_pedido
    
    pecas_qs = Peca.objects.filter(
        Q(numero_lote_pcp=lote_base) | Q(numero_lote_pcp__startswith=f"{lote_base}-")
    ).select_related('modulo__ordem_producao__pedido').order_by('numero_lote_pcp', 'modulo__nome_modulo', 'id_peca')
    
    if not pecas_qs.exists():
        return render(request, 'bipagem/index.html', {'erro': f'Lote {lote_base} não encontrado'})
        
    primeira = pecas_qs.first()
    pedido_obj = primeira.modulo.ordem_producao.pedido
    
    stats = pecas_qs.aggregate(
        total=Count('id'),
        bipadas=Count('id', filter=Q(status=StatusPeca.BIPADA))
    )
    
    resumo = {
        'numero_pedido': pedido_obj.numero_pedido,
        'cliente': pedido_obj.cliente_nome,
        'total_pecas': stats['total'],
        'pecas_bipadas': stats['bipadas'],
        'pecas_bipadas_neg': -stats['bipadas'],
        'percentual': round((stats['bipadas'] / stats['total'] * 100), 1) if stats['total'] > 0 else 0
    }
    
    # GARANTIA DE UNICIDADE: Usar set() para os lotes exibidos no cabeçalho
    lotes_unicos_set = set(pecas_qs.exclude(numero_lote_pcp='').values_list('numero_lote_pcp', flat=True))
    lote_display = " / ".join(sorted(list(lotes_unicos_set)))
    
    return render(request, 'bipagem/pedido_detalhe.html', {
        'pedido': resumo,
        'lote_manual': lote_display,
        'pecas': pecas_qs,
        'status_bipada': StatusPeca.BIPADA
    })

@login_required
def modulo_detalhe(request, referencia_modulo):
    modulo = get_object_or_404(Modulo, referencia_modulo=referencia_modulo)
    pecas = get_pecas_modulo(referencia_modulo)
    
    return render(request, 'bipagem/modulo_detalhe.html', {
        'modulo': {
            'nome': modulo.nome_modulo,
            'referencia': modulo.referencia_modulo
        },
        'pecas': pecas
    })

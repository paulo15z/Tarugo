from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q

from apps.bipagem.models import Pedido, Modulo, Peca
from apps.bipagem.selectors.progresso import (
    get_resumo_pedido, 
    get_modulos_pedido, 
    get_pecas_modulo
)
from apps.bipagem.domain.tipos import StatusPeca

@login_required
def index(request):
    """Página principal do scanner de bipagem (Dashboard Operacional)."""
    # Agrupamos por pedido
    pedidos_qs = Pedido.objects.annotate(
        total=Count('ordens_producao__modulos__pecas'),
        bipadas=Count('ordens_producao__modulos__pecas', filter=Q(ordens_producao__modulos__pecas__status=StatusPeca.BIPADA))
    ).order_by('-data_criacao')
    
    pedidos = []
    for p in pedidos_qs:
        total = p.total or 0
        bipadas = p.bipadas or 0
        percentual = (bipadas / total * 100) if total > 0 else 0
        
        # Buscar os lotes únicos deste pedido (ex: 573-01, 573-04)
        # Filtramos valores vazios e usamos set() para garantir unicidade absoluta
        lotes_raw = Peca.objects.filter(
            modulo__ordem_producao__pedido=p
        ).exclude(numero_lote_pcp='').values_list('numero_lote_pcp', flat=True).distinct()
        
        lotes_list = sorted(list(set(lotes_raw)))
        
        lote_display = ", ".join(lotes_list[:3])
        if len(lotes_list) > 3:
            lote_display += "..."
        elif not lotes_list:
            lote_display = p.numero_pedido # Fallback para o número do pedido se não houver lote

        pedidos.append({
            'numero_pedido': p.numero_pedido,
            'lote': lote_display,
            'cliente_nome': p.cliente_nome,
            'total': total,
            'bipadas': bipadas,
            'bipadas_neg': -bipadas,
            'percentual': round(percentual, 1)
        })
        
    return render(request, 'bipagem/index.html', {'pedidos': pedidos})

@login_required
def pedidos_list(request):
    return index(request)

@login_required
def pedido_detalhe(request, numero_pedido):
    """Detalhes de um pedido e seus módulos para conferência real-time."""
    resumo = get_resumo_pedido(numero_pedido)
    if not resumo:
        return render(request, 'bipagem/index.html', {'erro': 'Pedido não encontrado'})
        
    pecas_qs = Peca.objects.filter(
        modulo__ordem_producao__pedido__numero_pedido=numero_pedido
    ).select_related('modulo').order_by('modulo__nome_modulo', 'id_peca')
    
    # Pegar todos os lotes únicos de forma limpa e sem repetições
    lotes_raw = pecas_qs.exclude(numero_lote_pcp='').values_list('numero_lote_pcp', flat=True).distinct()
    lotes_unicos = sorted(list(set(lotes_raw)))
    
    lote_display = " / ".join(lotes_unicos) if lotes_unicos else numero_pedido
    
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

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Max

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
    # Puxamos o numero_lote_pcp mais comum ou o primeiro encontrado para cada pedido
    pedidos_qs = Pedido.objects.annotate(
        total=Count('ordens_producao__modulos__pecas'),
        bipadas=Count('ordens_producao__modulos__pecas', filter=Q(ordens_producao__modulos__pecas__status=StatusPeca.BIPADA)),
        lote_manual=Max('ordens_producao__modulos__pecas__numero_lote_pcp')
    ).order_by('-data_criacao')
    
    pedidos = []
    for p in pedidos_qs:
        total = p.total or 0
        bipadas = p.bipadas or 0
        percentual = (bipadas / total * 100) if total > 0 else 0
        
        pedidos.append({
            'numero_pedido': p.numero_pedido,
            'lote': p.lote_manual or "---",
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
    
    # Pega o lote manual de uma das peças para exibir no cabeçalho
    lote_manual = pecas_qs.first().numero_lote_pcp if pecas_qs.exists() else "---"
    
    return render(request, 'bipagem/pedido_detalhe.html', {
        'pedido': resumo,
        'lote_manual': lote_manual,
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

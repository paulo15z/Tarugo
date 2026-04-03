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
    pedidos_qs = Pedido.objects.annotate(
        total=Count('ordens_producao__modulos__pecas'),
        bipadas=Count('ordens_producao__modulos__pecas', filter=Q(ordens_producao__modulos__pecas__status=StatusPeca.BIPADA))
    ).order_by('-data_criacao')
    
    pedidos = []
    for p in pedidos_qs:
        total = p.total or 0
        bipadas = p.bipadas or 0
        percentual = (bipadas / total * 100) if total > 0 else 0
        
        pedidos.append({
            'numero_pedido': p.numero_pedido,
            'cliente_nome': p.cliente_nome,
            'total': total,
            'bipadas': bipadas,
            'bipadas_neg': -bipadas, # Para cálculo no template
            'percentual': round(percentual, 1)
        })
        
    return render(request, 'bipagem/index.html', {'pedidos': pedidos})

@login_required
def pedidos_list(request):
    """Redireciona para a index que agora é a listagem operacional."""
    return index(request)

@login_required
def pedido_detalhe(request, numero_pedido):
    """Detalhes de um pedido e seus módulos para conferência real-time."""
    resumo = get_resumo_pedido(numero_pedido)
    if not resumo:
        return render(request, 'bipagem/index.html', {'erro': 'Pedido não encontrado'})
        
    # Buscar todas as peças do pedido de uma vez para a visão completa
    pecas_qs = Peca.objects.filter(
        modulo__ordem_producao__pedido__numero_pedido=numero_pedido
    ).select_related('modulo').order_by('modulo__nome_modulo', 'id_peca')
    
    return render(request, 'bipagem/pedido_detalhe.html', {
        'pedido': resumo,
        'pecas': pecas_qs,
        'status_bipada': StatusPeca.BIPADA
    })

@login_required
def modulo_detalhe(request, referencia_modulo):
    """Listagem de peças de um módulo."""
    modulo = get_object_or_404(Modulo, referencia_modulo=referencia_modulo)
    pecas = get_pecas_modulo(referencia_modulo)
    
    return render(request, 'bipagem/modulo_detalhe.html', {
        'modulo': {
            'nome': modulo.nome_modulo,
            'referencia': modulo.referencia_modulo
        },
        'pecas': pecas
    })

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
    """Página principal do scanner de bipagem."""
    return render(request, 'bipagem/index.html')

@login_required
def pedidos_list(request):
    """Listagem de pedidos com progresso de bipagem."""
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
            'percentual': round(percentual, 2)
        })
        
    return render(request, 'bipagem/pedidos.html', {'pedidos': pedidos})

@login_required
def pedido_detalhe(request, numero_pedido):
    """Detalhes de um pedido e seus módulos."""
    resumo = get_resumo_pedido(numero_pedido)
    if not resumo:
        # Poderia redirecionar com mensagem de erro
        return render(request, 'bipagem/pedidos.html', {'erro': 'Pedido não encontrado'})
        
    modulos = get_modulos_pedido(numero_pedido)
    
    return render(request, 'bipagem/pedido_detalhe.html', {
        'pedido': resumo,
        'modulos': modulos
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

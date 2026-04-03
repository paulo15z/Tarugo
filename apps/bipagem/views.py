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
    """Página principal do scanner de bipagem (Dashboard Operacional por LOTE)."""
    # Agrupamos por LOTE em vez de Pedido para que cada lote seja uma unidade de trabalho
    lotes_qs = Peca.objects.values(
        'numero_lote_pcp', 
        'modulo__ordem_producao__pedido__numero_pedido',
        'modulo__ordem_producao__pedido__cliente_nome'
    ).annotate(
        total=Count('id'),
        bipadas=Count('id', filter=Q(status=StatusPeca.BIPADA))
    ).order_by('-modulo__ordem_producao__pedido__data_criacao', 'numero_lote_pcp')
    
    lotes = []
    for item in lotes_qs:
        total = item['total'] or 0
        bipadas = item['bipadas'] or 0
        percentual = (bipadas / total * 100) if total > 0 else 0
        
        lote_val = item['numero_lote_pcp'] or "SEM LOTE"
        pedido_val = item['modulo__ordem_producao__pedido__numero_pedido'] or "---"

        lotes.append({
            'lote': lote_val,
            'numero_pedido': pedido_val,
            'cliente_nome': item['modulo__ordem_producao__pedido__cliente_nome'] or "Cliente Desconhecido",
            'total': total,
            'bipadas': bipadas,
            'bipadas_neg': -bipadas,
            'percentual': round(percentual, 1)
        })
        
    return render(request, 'bipagem/index.html', {'lotes': lotes})

@login_required
def pedidos_list(request):
    return index(request)

@login_required
def pedido_detalhe(request, numero_pedido):
    """
    Detalhes de um pedido. 
    Se o numero_pedido contiver um hífen, tratamos como um LOTE específico.
    """
    # Verifica se o parâmetro é um LOTE (ex: 573-04) ou um Pedido (ex: 573)
    is_lote = "-" in numero_pedido
    
    if is_lote:
        pecas_qs = Peca.objects.filter(
            numero_lote_pcp=numero_pedido
        ).select_related('modulo__ordem_producao__pedido').order_by('modulo__nome_modulo', 'id_peca')
        
        if not pecas_qs.exists():
            return render(request, 'bipagem/index.html', {'erro': 'Lote não encontrado'})
            
        primeira = pecas_qs.first()
        pedido_obj = primeira.modulo.ordem_producao.pedido
        
        # Criar um resumo fake baseado no lote
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
        lote_display = numero_pedido
    else:
        # Comportamento original por Pedido
        resumo = get_resumo_pedido(numero_pedido)
        if not resumo:
            return render(request, 'bipagem/index.html', {'erro': 'Pedido não encontrado'})
            
        pecas_qs = Peca.objects.filter(
            modulo__ordem_producao__pedido__numero_pedido=numero_pedido
        ).select_related('modulo').order_by('modulo__nome_modulo', 'id_peca')
        
        lotes_unicos = sorted(list(set(pecas_qs.exclude(numero_lote_pcp='').values_list('numero_lote_pcp', flat=True).distinct())))
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

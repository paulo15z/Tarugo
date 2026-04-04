"""
Views Django (server-rendered) do app de bipagem.

Regra de dependência:
  - Usa apenas selectors e services do próprio app bipagem
  - Nunca importa models ou services do app pcp diretamente
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q

from apps.bipagem.models import Modulo, Peca
from apps.bipagem.selectors.lote_selectors import (
    get_lotes_dashboard,
    get_pecas_por_lote_producao,
)
from apps.bipagem.selectors.progresso import get_pecas_modulo
from apps.bipagem.services.bipagem_service import toggle_bloqueio_pedido
from apps.bipagem.domain.tipos import StatusPeca


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@login_required
def index(request):
    """Página principal do scanner — dashboard operacional por lote base."""
    lotes = get_lotes_dashboard()
    return render(request, 'bipagem/index.html', {'lotes': lotes})


# ---------------------------------------------------------------------------
# Detalhe de lote/pedido (scanner de peças)
# ---------------------------------------------------------------------------

@login_required
def pedido_detalhe(request, numero_pedido):
    """
    Tela de conferência de um lote base.
    O parâmetro `numero_pedido` é na verdade o lote base (ex: "500").
    """
    lote_base = numero_pedido

    pecas_qs = (
        Peca.objects
        .filter(
            Q(numero_lote_pcp=lote_base) |
            Q(numero_lote_pcp__startswith=f'{lote_base}-')
        )
        .select_related('modulo__ordem_producao__pedido')
        .order_by('numero_lote_pcp', 'modulo__nome_modulo', 'id_peca')
    )

    if not pecas_qs.exists():
        messages.error(request, f'Lote {lote_base} não encontrado.')
        return redirect('bipagem:index')

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
        'percentual': round(
            (stats['bipadas'] / stats['total'] * 100), 1
        ) if stats['total'] > 0 else 0,
    }

    lotes_unicos = sorted(set(
        pecas_qs
        .exclude(numero_lote_pcp='')
        .values_list('numero_lote_pcp', flat=True)
    ))
    lote_display = ' / '.join(lotes_unicos)

    return render(request, 'bipagem/pedido_detalhe.html', {
        'pedido': resumo,
        'pedido_obj': pedido_obj,
        'lote_manual': lote_display,
        'pecas': pecas_qs,
        'status_bipada': StatusPeca.BIPADA,
    })


# ---------------------------------------------------------------------------
# Detalhe de LoteProducao (lote misto — múltiplos pedidos)
# ---------------------------------------------------------------------------

@login_required
def lote_producao_detail(request, lote_id):
    """
    Detalhe de um LoteProducao específico.
    Mostra todas as peças e os pedidos envolvidos (útil para lotes mistos).
    """
    from apps.bipagem.models import LoteProducao, Pedido

    try:
        lote = LoteProducao.objects.select_related('processamento_pcp').get(id=lote_id)
    except LoteProducao.DoesNotExist:
        messages.error(request, f'Lote de produção {lote_id} não encontrado.')
        return redirect('bipagem:index')

    pecas = (
        Peca.objects
        .filter(lote_producao=lote)
        .select_related('modulo__ordem_producao__pedido')
        .order_by('modulo__ordem_producao__pedido__numero_pedido', 'id_peca')
    )

    stats = pecas.aggregate(
        total=Count('id'),
        bipadas=Count('id', filter=Q(status=StatusPeca.BIPADA))
    )
    total = stats['total'] or 0
    bipadas = stats['bipadas'] or 0

    pedidos = (
        Pedido.objects
        .filter(ordens_producao__modulos__pecas__lote_producao=lote)
        .distinct()
        .order_by('numero_pedido')
    )

    return render(request, 'bipagem/lote_producao_detail.html', {
        'lote': lote,
        'pecas': pecas,
        'pedidos': pedidos,
        'total': total,
        'bipadas': bipadas,
        'percentual': round((bipadas / total * 100), 1) if total > 0 else 0,
    })


# ---------------------------------------------------------------------------
# Módulo
# ---------------------------------------------------------------------------

@login_required
def modulo_detalhe(request, referencia_modulo):
    modulo = get_object_or_404(Modulo, referencia_modulo=referencia_modulo)
    pecas = get_pecas_modulo(referencia_modulo)

    return render(request, 'bipagem/modulo_detalhe.html', {
        'modulo': {
            'nome': modulo.nome_modulo,
            'referencia': modulo.referencia_modulo,
        },
        'pecas': pecas,
    })


# ---------------------------------------------------------------------------
# Ações
# ---------------------------------------------------------------------------

@login_required
def toggle_bloqueio_pedido_view(request, numero_pedido):
    """
    Bloqueia ou libera a bipagem de um pedido/lote.
    Busca o pedido pelo número ou pela associação com o lote base.
    """
    from apps.bipagem.models import Pedido

    pedido = Pedido.objects.filter(numero_pedido=numero_pedido).first()

    if not pedido:
        peca = (
            Peca.objects
            .filter(
                Q(numero_lote_pcp=numero_pedido) |
                Q(numero_lote_pcp__startswith=f'{numero_pedido}-')
            )
            .select_related('modulo__ordem_producao__pedido')
            .first()
        )
        if peca:
            pedido = peca.modulo.ordem_producao.pedido

    if not pedido:
        messages.error(request, f'Pedido ou Lote "{numero_pedido}" não encontrado.')
        return redirect('bipagem:index')

    try:
        bloqueado = toggle_bloqueio_pedido(pedido.id)
        estado = 'BLOQUEADO' if bloqueado else 'LIBERADO'
        messages.success(request, f'Pedido {pedido.numero_pedido} {estado} com sucesso.')
    except Exception as e:
        messages.error(request, f'Erro ao alterar status: {e}')

    return redirect('bipagem:index')
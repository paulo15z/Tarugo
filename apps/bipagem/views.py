from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from apps.bipagem.selectors.lote_selectors import (
    get_lote_preview,
    get_lotes_dashboard,
    get_pecas_do_lote,
)
from apps.bipagem.selectors.operacional_selector import (
    get_envio_expedicao,
    list_auditoria_pecas,
    list_envios_expedicao,
    list_modulos_preenchimento,
    list_viagens_por_lote,
)
from apps.bipagem.services.bipagem_service import estornar_bipagem


def _user_pode_gerenciar(request) -> bool:
    user = request.user
    if not user.is_authenticated:
        return False
    if user.is_superuser or user.is_staff:
        return True
    return user.groups.filter(name__in=['PCP', 'TI']).exists()


@login_required
def index(request):
    cliente = request.GET.get('cliente', '').strip()
    ambiente = request.GET.get('ambiente', '').strip()
    lotes = get_lotes_dashboard(cliente=cliente, ambiente=ambiente)

    return render(request, 'bipagem/index.html', {
        'lotes': lotes,
        'filtro_cliente': cliente,
        'filtro_ambiente': ambiente,
    })


@login_required
def pedido_detalhe(request, numero_pedido):
    pid = numero_pedido
    termo = request.GET.get('q', '').strip()
    ambiente = request.GET.get('ambiente', '').strip()
    plano = request.GET.get('plano', '').strip()
    status = request.GET.get('status', '').strip()

    preview = get_lote_preview(pid)
    if not preview:
        messages.error(request, 'Lote nao encontrado ou nao liberado para bipagem.')
        return redirect('bipagem:index')

    pecas = get_pecas_do_lote(pid, termo=termo, ambiente=ambiente, plano=plano, status=status)
    ambientes = preview['ambientes']
    planos = preview['planos']

    return render(request, 'bipagem/pedido_detalhe.html', {
        'pid': pid,
        'preview': preview,
        'pecas': pecas,
        'ambientes': ambientes,
        'planos': planos,
        'filtros': {
            'q': termo,
            'ambiente': ambiente,
            'plano': plano,
            'status': status,
        },
        'pode_estornar': _user_pode_gerenciar(request),
    })


@login_required
def operacional_lote(request, numero_pedido):
    pid = numero_pedido
    ambiente = request.GET.get('ambiente', '').strip()
    modulo = request.GET.get('modulo', '').strip()

    preview = get_lote_preview(pid)
    if not preview:
        messages.error(request, 'Lote nao encontrado ou nao liberado para bipagem.')
        return redirect('bipagem:index')

    auditoria_pecas = list_auditoria_pecas(pid, ambiente=ambiente, modulo=modulo)
    modulos = list_modulos_preenchimento(pid, ambiente=ambiente)
    envios_lote = list_viagens_por_lote(pid)

    return render(request, 'bipagem/operacional_lote.html', {
        'pid': pid,
        'preview': preview,
        'auditoria_pecas': auditoria_pecas,
        'modulos': modulos,
        'envios': envios_lote,
        'ambientes': preview['ambientes'],
        'filtros': {
            'ambiente': ambiente,
            'modulo': modulo,
        },
        'pode_gerenciar': _user_pode_gerenciar(request),
    })


@login_required
def viagens_index(request):
    status = request.GET.get("status", "").strip()
    viagens = list_envios_expedicao(status=status)
    return render(request, "bipagem/viagens.html", {
        "viagens": viagens,
        "status_filtro": status,
    })


@login_required
def viagem_detalhe(request, codigo):
    viagem = get_envio_expedicao(codigo)
    if not viagem:
        messages.error(request, "Viagem nao encontrada.")
        return redirect("bipagem:viagens")
    return render(request, "bipagem/viagem_detalhe.html", {
        "viagem": viagem,
    })


@login_required
@require_POST
def estornar_peca_view(request, numero_pedido):
    if not _user_pode_gerenciar(request):
        return HttpResponseForbidden('Somente PCP, TI ou admin podem estornar bipagens.')

    pid = numero_pedido
    codigo_peca = request.POST.get('codigo_peca', '').strip()
    motivo = request.POST.get('motivo', '').strip()

    resultado = estornar_bipagem({
        'pid': pid,
        'codigo_peca': codigo_peca,
        'usuario': request.user.username or 'SISTEMA',
        'motivo': motivo,
    })

    if resultado.get('sucesso'):
        messages.success(request, resultado['mensagem'])
    else:
        messages.error(request, resultado.get('mensagem') or resultado.get('erro') or 'Falha ao estornar.')
    return redirect('bipagem:pedido_detalhe', numero_pedido=pid)

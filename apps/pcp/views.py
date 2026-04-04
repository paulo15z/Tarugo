"""
Views do app PCP.

O PCP gerencia o ciclo de vida completo dos lotes:
liberar → bloquear → reabrir → liberar viagem

Não há acoplamento com views do bipagem aqui.
"""
from django.http import JsonResponse, FileResponse, Http404
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST

from apps.pcp.models.processamento import ProcessamentoPCP
from apps.pcp.services.processamento_service import ProcessamentoPCPService
from apps.pcp.services.pcp_interface import (
    bloquear_lote_bipagem,
    reabrir_lote_bipagem,
)


# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------

def pcp_index(request):
    """Serve o frontend principal do PCP."""
    return render(request, 'pcp/index.html')


# ---------------------------------------------------------------------------
# Processamento
# ---------------------------------------------------------------------------

@require_POST
def pcp_processar(request):
    """Recebe arquivo via AJAX, processa e retorna JSON com prévia."""
    arquivo = request.FILES.get('arquivo')

    if not arquivo:
        return JsonResponse({'erro': 'Nenhum arquivo enviado.'}, status=400)

    lote_str = request.POST.get('lote', '').strip()
    if not lote_str or not lote_str.isdigit() or int(lote_str) <= 0:
        return JsonResponse({'erro': 'Informe um número de lote válido.'}, status=400)

    try:
        resultado = ProcessamentoPCPService.processar_arquivo(arquivo, int(lote_str))
    except Exception as e:
        return JsonResponse({'erro': str(e)}, status=500)

    return JsonResponse({
        'pid': resultado['pid'],
        'lote': resultado['lote'],
        'total': resultado['total_pecas'],
        'previa': resultado['previa'],
        'resumo': resultado['resumo'],
        'nome_saida': resultado['nome_saida'],
    })


# ---------------------------------------------------------------------------
# Ciclo de vida do lote (bipagem)
# ---------------------------------------------------------------------------

@require_POST
def pcp_liberar(request, pid):
    """Libera um lote processado para bipagem (importa peças + sinaliza liberado)."""
    try:
        resultado = ProcessamentoPCPService.liberar_lote(pid, usuario=request.user)
        if not resultado.get('sucesso'):
            return JsonResponse({'erro': resultado.get('mensagem')}, status=400)
        return JsonResponse(resultado)
    except Exception as e:
        return JsonResponse({'erro': str(e)}, status=500)


@require_POST
def pcp_bloquear(request, pid):
    """
    Bloqueia um lote liberado para bipagem.
    Não remove as peças importadas — apenas suspende novas bipagens.
    """
    motivo = request.POST.get('motivo', '') or request.GET.get('motivo', '')
    resultado = bloquear_lote_bipagem(pid, motivo=motivo)
    status_code = 200 if resultado['sucesso'] else 404
    return JsonResponse(resultado, status=status_code)


@require_POST
def pcp_reabrir(request, pid):
    """
    Reabre um lote previamente bloqueado, sem reimportar peças.
    Útil para corrigir bloqueios acidentais.
    """
    resultado = reabrir_lote_bipagem(pid)
    status_code = 200 if resultado['sucesso'] else 404
    return JsonResponse(resultado, status=status_code)


# ---------------------------------------------------------------------------
# Ciclo de vida do lote (viagem/expedição)
# ---------------------------------------------------------------------------

@require_POST
def pcp_liberar_viagem(request, pid):
    """Libera um lote para expedição/viagem."""
    try:
        from django.utils import timezone

        lote = ProcessamentoPCP.objects.get(id=pid)
        lote.liberado_para_viagem = True
        lote.data_liberacao_viagem = timezone.now()
        lote.save(update_fields=['liberado_para_viagem', 'data_liberacao_viagem'])

        return JsonResponse({
            'sucesso': True,
            'mensagem': 'Lote liberado para viagem.',
            'data_liberacao_viagem': lote.data_liberacao_viagem.isoformat(),
        })
    except ProcessamentoPCP.DoesNotExist:
        return JsonResponse({'erro': 'Lote não encontrado.'}, status=404)
    except Exception as e:
        return JsonResponse({'erro': str(e)}, status=500)


# ---------------------------------------------------------------------------
# Histórico e download
# ---------------------------------------------------------------------------

@require_GET
def pcp_historico(request):
    """Retorna os últimos 50 processamentos como JSON."""
    registros = ProcessamentoPCP.objects.order_by('-criado_em')[:50]

    data = [
        {
            'id': r.id,
            'nome_arquivo': r.nome_arquivo,
            'lote': r.lote,
            'total_pecas': r.total_pecas,
            'data': r.criado_em.isoformat(),
            'liberado': r.liberado_para_bipagem,
            'data_liberacao': r.data_liberacao.isoformat() if r.data_liberacao else None,
            'liberado_viagem': r.liberado_para_viagem,
            'data_liberacao_viagem': (
                r.data_liberacao_viagem.isoformat() if r.data_liberacao_viagem else None
            ),
        }
        for r in registros
    ]

    return JsonResponse(data, safe=False)


@require_GET
def pcp_download(request, pid):
    """Serve o arquivo XLS gerado para download."""
    try:
        processamento = ProcessamentoPCP.objects.get(id=pid)
    except ProcessamentoPCP.DoesNotExist:
        raise Http404('Processamento não encontrado.')

    if not processamento.arquivo_saida:
        raise Http404('Arquivo não disponível.')

    try:
        arquivo = processamento.arquivo_saida.open('rb')
    except FileNotFoundError:
        raise Http404('Arquivo não encontrado no servidor.')

    nome = processamento.arquivo_saida.name.split('/')[-1]
    return FileResponse(arquivo, as_attachment=True, filename=nome)
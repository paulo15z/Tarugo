# apps/pcp/views.py
from django.http import JsonResponse, FileResponse, Http404
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST

from apps.pcp.models.processamento import ProcessamentoPCP
from apps.pcp.services.processamento_service import ProcessamentoPCPService


def pcp_index(request):
    """Serve o frontend principal do PCP."""
    return render(request, 'pcp/index.html')


@require_POST
def pcp_processar(request):
    """
    Recebe o arquivo via AJAX (sem campo lote — gerado automaticamente).
    Retorna JSON com resultado para o frontend.
    """
    arquivo = request.FILES.get('arquivo')

    if not arquivo:
        return JsonResponse({'erro': 'Nenhum arquivo enviado.'}, status=400)

    lote_str = request.POST.get('lote', '').strip()
    if not lote_str or not lote_str.isdigit() or int(lote_str) <= 0:
        return JsonResponse({'erro': 'Informe um número de lote válido.'}, status=400)
    lote = int(lote_str)

    try:
        resultado = ProcessamentoPCPService.processar_arquivo(arquivo, lote)
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


@require_POST
def pcp_liberar(request, pid):
    """
    Libera um lote processado para a bipagem.
    """
    try:
        resultado = ProcessamentoPCPService.liberar_lote(pid, usuario=request.user)
        if not resultado.get('sucesso'):
            return JsonResponse({'erro': resultado.get('mensagem')}, status=400)
        return JsonResponse(resultado)
    except Exception as e:
        return JsonResponse({'erro': str(e)}, status=500)


@require_POST
def pcp_liberar_viagem(request, pid):
    """
    Libera um lote processado para a expedição/viagem.
    """
    try:
        from django.utils import timezone
        lote = ProcessamentoPCP.objects.get(id=pid)
        lote.liberado_para_viagem = True
        lote.data_liberacao_viagem = timezone.now()
        lote.save(update_fields=['liberado_para_viagem', 'data_liberacao_viagem'])
        
        return JsonResponse({
            'sucesso': True, 
            'mensagem': 'Lote liberado para viagem!',
            'data_liberacao_viagem': lote.data_liberacao_viagem.isoformat()
        })
    except ProcessamentoPCP.DoesNotExist:
        return JsonResponse({'erro': 'Lote não encontrado.'}, status=404)
    except Exception as e:
        return JsonResponse({'erro': str(e)}, status=500)


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
            'data_liberacao_viagem': r.data_liberacao_viagem.isoformat() if r.data_liberacao_viagem else None,
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
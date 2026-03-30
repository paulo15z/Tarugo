# apps/pcp/views.py
from django.shortcuts import render
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from apps.pcp.services.processamento_service import ProcessamentoPCPService


@login_required
def pcp_upload(request):
    """Upload + processamento do PCP com campo de lote"""
    contexto = {'secao': 'pcp'}

    if request.method == 'POST':
        arquivo = request.FILES.get('arquivo')
        lote_str = request.POST.get('lote')

        if not arquivo:
            messages.error(request, "❌ Selecione um arquivo!")
            return render(request, 'pcp/upload.html', contexto)

        if not lote_str or not lote_str.isdigit():
            messages.error(request, "❌ Informe um número de lote válido!")
            return render(request, 'pcp/upload.html', contexto)

        lote = int(lote_str)

        try:
            resultado = ProcessamentoPCPService.processar_arquivo(arquivo, lote)

            messages.success(request, f"✅ Roteiro do Lote {lote} processado com sucesso! ({resultado['total_pecas']} peças)")

            contexto.update({
                'resultado': resultado,
                'pid': resultado['pid'],
                'nome_saida': resultado['nome_saida'],
            })

        except Exception as e:
            messages.error(request, f"❌ Erro ao processar arquivo: {str(e)}")

    return render(request, 'pcp/upload.html', contexto)
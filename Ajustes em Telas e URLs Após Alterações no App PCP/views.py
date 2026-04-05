"""
Views do app PCP.

O PCP gerencia o ciclo de vida completo dos lotes:
liberar → bloquear → reabrir → liberar viagem

Não há acoplamento com views do bipagem aqui.
"""
import unicodedata
import re
import pandas as pd
from django.http import JsonResponse, FileResponse, Http404
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST
from django.core.files.base import ContentFile

from apps.pcp.models.processamento import ProcessamentoPCP
from apps.pcp.models.lote import LotePCP
from apps.pcp.services.pcp_service import processar_arquivo_dinabox
from apps.pcp.services.pcp_interface import (
    liberar_lote_para_bipagem,
    bloquear_lote_bipagem,
    reabrir_lote_bipagem,
)


def _normalizar_chave(chave: str) -> str:
    """Converte 'DESCRIÇÃO DA PEÇA' → 'DESCRICAO_DA_PECA' (válido no template Django)."""
    chave = unicodedata.normalize('NFD', chave)
    chave = ''.join(c for c in chave if unicodedata.category(c) != 'Mn')
    return re.sub(r'\W+', '_', chave).strip('_').upper()


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
        # 1. Processa o arquivo usando o novo serviço
        df, xls_bytes, nome_saida, pid = processar_arquivo_dinabox(arquivo)
        
        # 2. Cria o registro legado ProcessamentoPCP para compatibilidade com o histórico atual
        # e para armazenar o arquivo_saida (XLS)
        processamento = ProcessamentoPCP.objects.create(
            id=pid,
            nome_arquivo=arquivo.name,
            lote=int(lote_str),
            total_pecas=len(df),
            usuario=request.user if request.user.is_authenticated else None
        )
        
        arquivo_content = ContentFile(xls_bytes, name=nome_saida)
        processamento.arquivo_saida.save(nome_saida, arquivo_content, save=True)

        # 3. Prepara a resposta JSON esperada pelo index.html
        cols_previa = ['DESCRIÇÃO DA PEÇA', 'LOCAL', 'PLANO', 'ROTEIRO']
        if 'LOTE' in df.columns:
            cols_previa.insert(0, 'LOTE')
        if 'OBSERVAÇÃO' in df.columns:
            cols_previa.insert(3, 'OBSERVAÇÃO')

        previa_raw = df[cols_previa].head(50).fillna('').to_dict(orient='records')
        previa = [{_normalizar_chave(k): v for k, v in row.items()} for row in previa_raw]

        resumo_df = df['ROTEIRO'].fillna('SEM ROTEIRO').astype(str).value_counts().reset_index()
        resumo_df.columns = ['roteiro', 'qtd']
        resumo = resumo_df.to_dict(orient='records')

        return JsonResponse({
            'pid': pid,
            'lote': int(lote_str),
            'total': len(df),
            'previa': previa,
            'resumo': resumo,
            'nome_saida': nome_saida,
        })
    except Exception as e:
        return JsonResponse({'erro': str(e)}, status=500)


# ---------------------------------------------------------------------------
# Ciclo de vida do lote (bipagem)
# ---------------------------------------------------------------------------

@require_POST
def pcp_liberar(request, pid):
    """Libera um lote processado para bipagem."""
    try:
        resultado = liberar_lote_para_bipagem(pid, usuario=request.user)
        if not resultado.get('sucesso'):
            return JsonResponse({'erro': resultado.get('mensagem')}, status=400)
        return JsonResponse(resultado)
    except Exception as e:
        return JsonResponse({'erro': str(e)}, status=500)


@require_POST
def pcp_bloquear(request, pid):
    """Bloqueia um lote liberado para bipagem."""
    motivo = request.POST.get('motivo', '') or request.GET.get('motivo', '')
    resultado = bloquear_lote_bipagem(pid, motivo=motivo)
    status_code = 200 if resultado['sucesso'] else 404
    return JsonResponse(resultado, status=status_code)


@require_POST
def pcp_reabrir(request, pid):
    """Reabre um lote previamente bloqueado."""
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

# apps/estoque/views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from apps.estoque.services.movimentacao_service import MovimentacaoService
from apps.estoque.selectors import (
    get_produtos_com_saldo_baixo,
    get_movimentacoes_recentes,
    get_total_produtos_ativos,
)


@login_required
def dashboard(request):
    """Dashboard principal do módulo Estoque - Tarugo"""
    context = {
        'titulo': 'Dashboard - Estoque | Tarugo',
        'produtos_baixo_estoque': get_produtos_com_saldo_baixo(quantidade_minima=10),
        'ultimas_movimentacoes': get_movimentacoes_recentes(limit=15),
        'total_produtos': get_total_produtos_ativos(),
        'secao': 'estoque',
    }
    return render(request, 'estoque/dashboard.html', context)


@login_required
def movimentacao_create(request):
    """Formulário simples de movimentação usando o Service"""
    if request.method == 'POST':
        try:
            data = {
                'produto_id': int(request.POST.get('produto_id')),
                'tipo': request.POST.get('tipo'),
                'quantidade': float(request.POST.get('quantidade')),
                'observacao': request.POST.get('observacao', ''),
            }
            MovimentacaoService.processar_movimentacao(data, usuario_id=request.user.id)
            messages.success(request, '✅ Movimentação registrada com sucesso!')
            return redirect('estoque:estoque-dashboard')
        except Exception as e:
            messages.error(request, f'❌ Erro: {str(e)}')

    context = {'titulo': 'Nova Movimentação de Estoque'}
    return render(request, 'estoque/movimentacao_form.html', context)
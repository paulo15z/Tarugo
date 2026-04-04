# apps/estoque/views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from apps.estoque.models.categoria import CategoriaProduto
from apps.estoque.permissions import grupo_requerido
from apps.estoque.services.movimentacao_service import MovimentacaoService
from apps.estoque.schemas.movimentacao import MovimentacaoCreateSchema
from apps.estoque.selectors.produto_selector import ProdutoSelector, get_produtos_com_saldo_baixo
from apps.estoque.models import Produto, SaldoMDF
from apps.estoque.services.produto_service import ProdutoService
from apps.estoque.domain.tipos import FamiliaProduto


@login_required
def lista_produtos(request):
    produtos = ProdutoSelector.get_all_produtos().select_related('categoria').prefetch_related('saldos_mdf')
    produtos_baixo_estoque = get_produtos_com_saldo_baixo()

    grupos = set(request.user.groups.values_list('name', flat=True))
    pode_movimentar = request.user.is_superuser or bool(grupos & {'estoque.02', 'estoque.03'})
    pode_cadastrar  = request.user.is_superuser or 'estoque.03' in grupos

    return render(request, 'estoque/lista_produtos.html', {
        'produtos': produtos,
        'produtos_baixo_estoque': produtos_baixo_estoque,
        'pode_movimentar': pode_movimentar,
        'pode_cadastrar': pode_cadastrar,
        'FAMILIA_MDF': FamiliaProduto.MDF,
    })


@grupo_requerido('estoque.02', 'estoque.03')
def movimentacao_create(request):
    if request.method == 'POST':
        try:
            data = {
                'produto_id': int(request.POST['produto_id']),
                'tipo': request.POST['tipo'],
                'quantidade': int(request.POST['quantidade']),
                'espessura': request.POST.get('espessura') or None,
                'observacao': request.POST.get('observacao') or None,
            }
            
            if data['espessura']:
                data['espessura'] = int(data['espessura'])

            MovimentacaoService.processar_movimentacao(data, request.user)
            messages.success(request, 'Movimentação registrada com sucesso!')
            return redirect('estoque:lista_produtos')
        except Exception as e:
            messages.error(request, str(e))

    produtos = ProdutoSelector.get_all_produtos().select_related('categoria')
    return render(request, 'estoque/movimentacao_form.html', {
        'produtos': produtos,
        'FAMILIA_MDF': FamiliaProduto.MDF,
    })


@grupo_requerido('estoque.03')
def produto_create(request):
    """View para cadastro de produto com suporte a categorias e atributos dinâmicos"""
    
    if request.method == 'POST':
        try:
            # Prepara os dados para o Service (padrão Tarugo)
            import json
            atributos_raw = request.POST.get('atributos_especificos', '{}')
            try:
                atributos = json.loads(atributos_raw)
            except:
                atributos = {}

            data = {
                'nome': request.POST.get('nome', '').strip(),
                'sku': request.POST.get('sku', '').strip().upper(),
                'categoria_id': int(request.POST.get('categoria_id')),
                'unidade_medida': request.POST.get('unidade_medida'),
                'estoque_minimo': int(request.POST.get('estoque_minimo', 0)),
                'preco_custo': float(request.POST.get('preco_custo')) if request.POST.get('preco_custo') else None,
                'lote': request.POST.get('lote', '').strip() or None,
                'localizacao': request.POST.get('localizacao', '').strip() or None,
                'atributos_especificos': atributos,
            }

            # Chama o Service (regra de negócio central)
            produto = ProdutoService.criar_produto(data)

            messages.success(request, f'Produto "{produto.nome}" ({produto.sku}) cadastrado com sucesso!')
            return redirect('estoque:lista_produtos')

        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f'Erro inesperado ao cadastrar produto: {str(e)}')

    # GET → carrega o formulário com as categorias
    categorias = CategoriaProduto.objects.all().order_by('ordem', 'nome')

    return render(request, 'estoque/produto_form.html', {
        'categorias': categorias,
    })
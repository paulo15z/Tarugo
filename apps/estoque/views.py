# apps/estoque/views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from apps.estoque.models.categoria import CategoriaProduto
from apps.estoque.permissions import grupo_requerido
from apps.estoque.services.movimentacao_service import MovimentacaoService
from apps.estoque.schemas.movimentacao import MovimentacaoCreateSchema
from apps.estoque.selectors.produto_selector import ProdutoSelector, get_produtos_com_saldo_baixo
from apps.estoque.models import Produto
from apps.estoque.services.produto_service import ProdutoService


@login_required
def lista_produtos(request):
    produtos = ProdutoSelector.get_all_produtos()
    produtos_baixo_estoque = get_produtos_com_saldo_baixo()

    grupos = set(request.user.groups.values_list('name', flat=True))
    pode_movimentar = request.user.is_superuser or bool(grupos & {'estoque.02', 'estoque.03'})
    pode_cadastrar  = request.user.is_superuser or 'estoque.03' in grupos

    return render(request, 'estoque/lista_produtos.html', {
        'produtos': produtos,
        'produtos_baixo_estoque': produtos_baixo_estoque,
        'pode_movimentar': pode_movimentar,
        'pode_cadastrar': pode_cadastrar,
    })


@grupo_requerido('estoque.02', 'estoque.03')
def movimentacao_create(request):
    if request.method == 'POST':
        try:
            schema = MovimentacaoCreateSchema(
                produto_id=int(request.POST['produto_id']),
                tipo=request.POST['tipo'],
                quantidade=int(request.POST['quantidade']),
                observacao=request.POST.get('observacao') or None,
            )
            MovimentacaoService.processar_movimentacao(schema.model_dump(), request.user)
            messages.success(request, 'Movimentação registrada com sucesso!')
            return redirect('estoque:lista_produtos')
        except Exception as e:
            messages.error(request, str(e))

    produtos = ProdutoSelector.get_all_produtos()
    return render(request, 'estoque/movimentacao_form.html', {'produtos': produtos})


@grupo_requerido('estoque.03')
def produto_create(request):
    """View para cadastro de produto com suporte a categorias e atributos dinâmicos"""
    
    if request.method == 'POST':
        try:
            # Prepara os dados para o Service (padrão Tarugo)
            data = {
                'nome': request.POST.get('nome', '').strip(),
                'sku': request.POST.get('sku', '').strip().upper(),
                'categoria_id': int(request.POST.get('categoria_id')),
                'unidade_medida': request.POST.get('unidade_medida'),
                'estoque_minimo': int(request.POST.get('estoque_minimo', 0)),
                'preco_custo': float(request.POST.get('preco_custo')) if request.POST.get('preco_custo') else None,
                'lote': request.POST.get('lote', '').strip() or None,
                'localizacao': request.POST.get('localizacao', '').strip() or None,
                'atributos_especificos': {},   # Vamos melhorar na próxima etapa
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
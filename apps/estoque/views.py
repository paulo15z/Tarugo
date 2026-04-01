# apps/estoque/views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from apps.estoque.services.movimentacao_service import MovimentacaoService
from apps.estoque.schemas.movimentacao import MovimentacaoCreateSchema
from apps.estoque.selectors.produto_selector import ProdutoSelector
from apps.estoque.selectors.produto_selector import get_produtos_com_saldo_baixo


@login_required
def lista_produtos(request):
    produtos = ProdutoSelector.get_all_produtos()
    produtos_baixo_estoque = get_produtos_com_saldo_baixo()
    return render(request, "estoque/lista_produtos.html", {
        "produtos": produtos,
        "produtos_baixo_estoque": produtos_baixo_estoque,
    })


@login_required
def movimentacao_create(request):
    if request.method == "POST":
        try:
            schema = MovimentacaoCreateSchema(
                produto_id=int(request.POST["produto_id"]),
                tipo=request.POST["tipo"],
                quantidade=int(request.POST["quantidade"]),
                observacao=request.POST.get("observacao") or None,
            )

            # Converte para dict pois o service agora trabalha com dict
            MovimentacaoService.processar_movimentacao(schema.model_dump(), request.user)
            messages.success(request, "Movimentação registrada com sucesso!")
            return redirect("estoque:lista_produtos")

        except Exception as e:
            messages.error(request, str(e))

    produtos = ProdutoSelector.get_all_produtos()
    return render(request, "estoque/movimentacao_form.html", {"produtos": produtos})
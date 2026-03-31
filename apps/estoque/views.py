from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from apps.estoque.services.movimentacao_service import MovimentacaoService
from apps.estoque.schemas.movimentacao import MovimentacaoCreateSchema
from apps.estoque.selectors.produto_selector import ProdutoSelector
from apps.estoque.models import Produto


@login_required
def lista_produtos(request):
    produtos = ProdutoSelector.get_all_produtos()
    return render(request, "estoque/lista_produtos.html", {"produtos": produtos})


@login_required
def movimentacao_create(request):
    if request.method == "POST":
        try:
            schema = MovimentacaoCreateSchema(
                produto_id=int(request.POST["produto_id"]),
                tipo=request.POST["tipo"],
                quantidade=int(request.POST["quantidade"]),
                observacao=request.POST.get("observacao"),
            )

            MovimentacaoService.processar_movimentacao(schema, request.user)
            messages.success(request, "Movimentação realizada com sucesso!")
            return redirect("estoque:lista_produtos")

        except Exception as e:
            messages.error(request, str(e))

    produtos = ProdutoSelector.get_all_produtos()
    return render(request, "estoque/movimentacao_form.html", {"produtos": produtos})
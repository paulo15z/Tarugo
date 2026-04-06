import json
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import redirect, render

from apps.estoque.domain.tipos import FamiliaProduto
from apps.estoque.models import Produto, Reserva
from apps.estoque.models.categoria import CategoriaProduto
from apps.estoque.permissions import grupo_requerido
from apps.estoque.selectors.disponibilidade_selector import get_disponibilidade_resumida
from apps.estoque.selectors.produto_selector import ProdutoSelector
from apps.estoque.services.movimentacao_service import MovimentacaoService
from apps.estoque.services.produto_service import ProdutoService
from apps.estoque.services.reserva_service import ReservaService


@login_required
def lista_produtos(request):
    produtos = ProdutoSelector.get_all_produtos().select_related("categoria").prefetch_related("saldos_mdf")
    produto_rows = []
    for produto in produtos:
        disponibilidade = get_disponibilidade_resumida(produto)
        if produto.categoria.familia == FamiliaProduto.MDF:
            critico = any(
                item["saldo_reservado"] > 0 and item["saldo_disponivel"] <= produto.estoque_minimo
                for item in disponibilidade["por_espessura"]
            )
        else:
            critico = disponibilidade["saldo_disponivel"] <= produto.estoque_minimo
        produto_rows.append(
            {
                "produto": produto,
                "disponibilidade": disponibilidade,
                "critico": critico,
            }
        )
    produtos_criticos_count = sum(1 for row in produto_rows if row["critico"])

    grupos = set(request.user.groups.values_list("name", flat=True))
    pode_movimentar = request.user.is_superuser or bool(grupos & {"estoque.02", "estoque.03"})
    pode_cadastrar = request.user.is_superuser or "estoque.03" in grupos

    return render(
        request,
        "estoque/lista_produtos.html",
        {
            "produtos": produtos,
            "produto_rows": produto_rows,
            "produtos_criticos_count": produtos_criticos_count,
            "pode_movimentar": pode_movimentar,
            "pode_cadastrar": pode_cadastrar,
            "FAMILIA_MDF": FamiliaProduto.MDF,
        },
    )


@grupo_requerido("estoque.02", "estoque.03")
def movimentacao_create(request):
    if request.method == "POST":
        try:
            data = {
                "produto_id": int(request.POST["produto_id"]),
                "tipo": request.POST["tipo"],
                "quantidade": int(request.POST["quantidade"]),
                "espessura": request.POST.get("espessura") or None,
                "observacao": request.POST.get("observacao") or None,
            }

            if data["espessura"]:
                data["espessura"] = int(data["espessura"])

            MovimentacaoService.processar_movimentacao(data, usuario=request.user)
            messages.success(request, "Movimentacao registrada com sucesso!")
            return redirect("estoque:lista_produtos")
        except Exception as exc:
            messages.error(request, str(exc))

    produtos = ProdutoSelector.get_all_produtos().select_related("categoria")
    return render(
        request,
        "estoque/movimentacao_form.html",
        {
            "produtos": produtos,
            "FAMILIA_MDF": FamiliaProduto.MDF,
        },
    )


@grupo_requerido("estoque.03")
def produto_create(request):
    if request.method == "POST":
        try:
            atributos_raw = request.POST.get("atributos_especificos", "{}")
            try:
                atributos = json.loads(atributos_raw)
            except Exception:
                atributos = {}

            data = {
                "nome": request.POST.get("nome", "").strip(),
                "sku": request.POST.get("sku", "").strip().upper(),
                "categoria_id": int(request.POST.get("categoria_id")),
                "unidade_medida": request.POST.get("unidade_medida"),
                "estoque_minimo": int(request.POST.get("estoque_minimo", 0)),
                "preco_custo": float(request.POST.get("preco_custo")) if request.POST.get("preco_custo") else None,
                "lote": request.POST.get("lote", "").strip() or None,
                "localizacao": request.POST.get("localizacao", "").strip() or None,
                "atributos_especificos": atributos,
            }

            produto = ProdutoService.criar_produto(data)
            messages.success(request, f'Produto "{produto.nome}" ({produto.sku}) cadastrado com sucesso!')
            return redirect("estoque:lista_produtos")

        except ValueError as exc:
            messages.error(request, str(exc))
        except Exception as exc:
            messages.error(request, f"Erro inesperado ao cadastrar produto: {exc}")

    categorias = CategoriaProduto.objects.all().order_by("ordem", "nome")
    return render(request, "estoque/produto_form.html", {"categorias": categorias})


@login_required
def lista_reservas(request):
    reservas = Reserva.objects.select_related("produto", "produto__categoria").all()
    return render(
        request,
        "estoque/lista_reservas.html",
        {
            "reservas": reservas,
            "FAMILIA_MDF": FamiliaProduto.MDF,
        },
    )


@grupo_requerido("estoque.02", "estoque.03")
def reserva_create(request):
    if request.method == "POST":
        try:
            data = {
                "produto_id": int(request.POST.get("produto_id")),
                "quantidade": int(request.POST.get("quantidade")),
                "espessura": int(request.POST.get("espessura")) if request.POST.get("espessura") else None,
                "referencia_externa": request.POST.get("referencia_externa") or None,
                "origem_externa": request.POST.get("origem_externa") or "pcp",
                "observacao": request.POST.get("observacao"),
            }
            ReservaService.criar_reserva(data, usuario=request.user)
            messages.success(request, "Reserva criada com sucesso!")
            return redirect("estoque:lista_reservas")
        except ValidationError as exc:
            messages.error(request, f"Erro de validacao: {exc}")
        except Exception as exc:
            messages.error(request, f"Erro inesperado ao criar reserva: {exc}")

    produtos = Produto.objects.select_related("categoria").prefetch_related("saldos_mdf").all()
    return render(
        request,
        "estoque/reserva_form.html",
        {
            "produtos": produtos,
            "FAMILIA_MDF": FamiliaProduto.MDF,
        },
    )


@grupo_requerido("estoque.02", "estoque.03")
def reserva_consumir(request, reserva_id):
    if request.method == "POST":
        try:
            ReservaService.consumir_reserva(reserva_id, usuario=request.user)
            messages.success(request, "Reserva consumida com sucesso.")
        except Exception as exc:
            messages.error(request, f"Erro ao consumir reserva: {exc}")
    return redirect("estoque:lista_reservas")


@grupo_requerido("estoque.02", "estoque.03")
def reserva_cancelar(request, reserva_id):
    if request.method == "POST":
        try:
            ReservaService.cancelar_reserva(reserva_id, usuario=request.user)
            messages.success(request, "Reserva cancelada com sucesso.")
        except Exception as exc:
            messages.error(request, f"Erro ao cancelar reserva: {exc}")
    return redirect("estoque:lista_reservas")


@grupo_requerido("estoque.03")
def produto_config_update(request, produto_id):
    if request.method == "POST":
        try:
            espessura = int(request.POST.get("espessura"))
            estoque_minimo = int(request.POST.get("estoque_minimo"))
            preco_custo = Decimal(request.POST.get("preco_custo")) if request.POST.get("preco_custo") else None

            ProdutoService.atualizar_configuracoes_mdf(
                produto_id=produto_id,
                espessura=espessura,
                estoque_minimo=estoque_minimo,
                preco_custo=preco_custo,
            )
            messages.success(request, "Configuracoes atualizadas com sucesso!")
        except Exception as exc:
            messages.error(request, f"Erro ao atualizar: {exc}")

    return redirect("estoque:lista_produtos")

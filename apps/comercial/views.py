from __future__ import annotations

from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from pydantic import ValidationError

from apps.integracoes.dinabox.client import DinaboxRequestError

from .models import AmbienteOrcamento, ClienteComercial, StatusClienteComercial
from .permissions import (
    comercial_editar_requerido,
    comercial_excluir_requerido,
    comercial_login_e_ver,
    pode_editar_comercial,
    pode_excluir_cliente_comercial,
)
from .schemas.cliente import (
    AmbienteOrcamentoInputSchema,
    ClienteComercialAtualizarDinaboxSchema,
    ClienteComercialCriarDinaboxSchema,
)
from .selectors import ComercialSelector
from .services import ClienteComercialService


def _parse_decimal_br(raw: str) -> Decimal | None:
    s = (raw or "").strip().replace(".", "").replace(",", ".")
    if not s:
        return None
    try:
        return Decimal(s)
    except InvalidOperation:
        raise ValueError("Valor monetário inválido.")


@comercial_login_e_ver
def lista(request):
    q = (request.GET.get("q") or "").strip()
    view_mode = (request.GET.get("v") or "board").strip().lower()
    if view_mode not in ("board", "lista"):
        view_mode = "board"

    clientes = ComercialSelector.list_clientes()
    rows = []
    for c in clientes:
        idx = ComercialSelector.dinabox_index_por_customer_id(c.customer_id)
        if q:
            blob = f"{c.customer_id} {(idx.customer_name if idx else '')}".lower()
            if q.lower() not in blob:
                continue
        rows.append({"cliente": c, "dinabox": idx})

    board_columns = [
        {"status": val, "label": label, "items": []} for val, label in StatusClienteComercial.choices
    ]
    by_status = {col["status"]: col["items"] for col in board_columns}
    for row in rows:
        bucket = by_status.get(row["cliente"].status)
        if bucket is not None:
            bucket.append(row)

    return render(
        request,
        "comercial/lista.html",
        {
            "rows": rows,
            "board_columns": board_columns,
            "view_mode": view_mode,
            "q": q,
            "pode_editar": pode_editar_comercial(request.user),
            "pode_excluir": pode_excluir_cliente_comercial(request.user),
            "status_choices": StatusClienteComercial.choices,
        },
    )


@comercial_login_e_ver
def detalhe(request, pk: int):
    cliente = ComercialSelector.get_cliente(pk)
    if cliente is None:
        raise Http404()

    idx = ComercialSelector.dinabox_index_por_customer_id(cliente.customer_id)
    return render(
        request,
        "comercial/detalhe.html",
        {
            "cliente": cliente,
            "dinabox": idx,
            "status_choices": StatusClienteComercial.choices,
            "pode_editar": pode_editar_comercial(request.user),
            "pode_excluir": pode_excluir_cliente_comercial(request.user),
        },
    )


@comercial_editar_requerido
def novo(request):
    if request.method == "POST":
        try:
            schema = ClienteComercialCriarDinaboxSchema(
                customer_name=request.POST.get("customer_name", ""),
                customer_type=request.POST.get("customer_type") or "pf",
                customer_status=request.POST.get("customer_status") or "on",
                customer_emails=request.POST.get("customer_emails"),
                customer_phones=request.POST.get("customer_phones"),
                customer_note=request.POST.get("customer_note"),
                customer_cpf=request.POST.get("customer_cpf"),
                customer_cnpj=request.POST.get("customer_cnpj"),
            )
            cliente = ClienteComercialService.criar_na_dinabox_e_local(schema, request.user)
            messages.success(request, "Cliente criado na Dinabox e ficha comercial aberta.")
            return redirect("comercial:detalhe", pk=cliente.pk)
        except ValidationError as exc:
            for err in exc.errors():
                messages.error(request, f"{err.get('loc', ())}: {err.get('msg', '')}")
        except ValueError as exc:
            messages.error(request, str(exc))
        except DinaboxRequestError as exc:
            messages.error(request, f"Erro na API Dinabox: {exc}")

    return render(request, "comercial/novo.html", {})


@comercial_editar_requerido
def vincular(request):
    search = (request.GET.get("q") or request.POST.get("q") or "").strip()
    if request.method == "POST":
        cid = (request.POST.get("customer_id") or "").strip()
        try:
            cliente = ClienteComercialService.vincular_cliente_existente(cid, request.user)
            messages.success(request, "Cliente vinculado à ficha comercial.")
            return redirect("comercial:detalhe", pk=cliente.pk)
        except ValueError as exc:
            messages.error(request, str(exc))
        except DinaboxRequestError as exc:
            messages.error(request, f"Erro na API Dinabox: {exc}")

    candidatos = ComercialSelector.candidatos_vinculacao(search=search)
    return render(
        request,
        "comercial/vincular.html",
        {"candidatos": candidatos, "q": search},
    )


@comercial_editar_requerido
def editar_dinabox(request, pk: int):
    cliente = get_object_or_404(ClienteComercial, pk=pk)
    idx = ComercialSelector.dinabox_index_por_customer_id(cliente.customer_id)

    if request.method == "POST":
        try:
            schema = ClienteComercialAtualizarDinaboxSchema(
                customer_id=cliente.customer_id,
                customer_name=request.POST.get("customer_name", ""),
                customer_type=request.POST.get("customer_type") or "pf",
                customer_status=request.POST.get("customer_status") or "on",
                customer_emails=request.POST.get("customer_emails"),
                customer_phones=request.POST.get("customer_phones"),
                customer_note=request.POST.get("customer_note"),
                customer_cpf=request.POST.get("customer_cpf"),
                customer_cnpj=request.POST.get("customer_cnpj"),
            )
            ClienteComercialService.atualizar_cadastro_dinabox(cliente, schema)
            messages.success(request, "Cadastro essencial atualizado na Dinabox.")
            return redirect("comercial:detalhe", pk=cliente.pk)
        except ValidationError as exc:
            for err in exc.errors():
                messages.error(request, f"{err.get('loc', ())}: {err.get('msg', '')}")
        except ValueError as exc:
            messages.error(request, str(exc))
        except DinaboxRequestError as exc:
            messages.error(request, f"Erro na API Dinabox: {exc}")

    initial = {
        "customer_name": idx.customer_name if idx else "",
        "customer_type": (idx.customer_type if idx else "pf") or "pf",
        "customer_status": (idx.customer_status if idx else "on") or "on",
        "customer_emails": idx.customer_emails_text if idx else "",
        "customer_phones": idx.customer_phones_text if idx else "",
    }
    return render(
        request,
        "comercial/editar_dinabox.html",
        {"cliente": cliente, "dinabox": idx, "initial": initial},
    )


@comercial_editar_requerido
def status_post(request, pk: int):
    if request.method != "POST":
        return redirect("comercial:detalhe", pk=pk)
    cliente = get_object_or_404(ClienteComercial, pk=pk)
    novo_status = (request.POST.get("status") or "").strip()
    try:
        ClienteComercialService.atualizar_status(cliente, novo_status)
        messages.success(request, "Status atualizado.")
    except ValueError as exc:
        messages.error(request, str(exc))
    nxt = (request.POST.get("return") or "").strip()
    if nxt == "board":
        return redirect(f"{reverse('comercial:lista')}?v=board")
    if nxt == "lista":
        return redirect(f"{reverse('comercial:lista')}?v=lista")
    return redirect("comercial:detalhe", pk=pk)


@comercial_editar_requerido
def observacao_post(request, pk: int):
    if request.method != "POST":
        return redirect("comercial:detalhe", pk=pk)
    cliente = get_object_or_404(ClienteComercial, pk=pk)
    try:
        ClienteComercialService.adicionar_observacao(
            cliente,
            request.POST.get("texto", ""),
            request.user,
        )
        messages.success(request, "Observação registrada.")
    except ValueError as exc:
        messages.error(request, str(exc))
    return redirect("comercial:detalhe", pk=pk)


@comercial_editar_requerido
def ambiente_novo_post(request, pk: int):
    if request.method != "POST":
        return redirect("comercial:detalhe", pk=pk)
    cliente = get_object_or_404(ClienteComercial, pk=pk)
    try:
        valor = _parse_decimal_br(request.POST.get("valor_orcado", ""))
        schema = AmbienteOrcamentoInputSchema(
            nome_ambiente=request.POST.get("nome_ambiente", ""),
            valor_orcado=valor,
        )
        ClienteComercialService.adicionar_ambiente(cliente, schema)
        messages.success(request, "Ambiente adicionado.")
    except (ValidationError, ValueError) as exc:
        messages.error(request, str(exc))
    return redirect("comercial:detalhe", pk=pk)


@comercial_editar_requerido
def ambiente_editar_post(request, pk: int, ambiente_id: int):
    if request.method != "POST":
        return redirect("comercial:detalhe", pk=pk)
    cliente = get_object_or_404(ClienteComercial, pk=pk)
    ambiente = get_object_or_404(AmbienteOrcamento, pk=ambiente_id, cliente=cliente)
    try:
        valor = _parse_decimal_br(request.POST.get("valor_orcado", ""))
        schema = AmbienteOrcamentoInputSchema(
            nome_ambiente=request.POST.get("nome_ambiente", ""),
            valor_orcado=valor,
        )
        ClienteComercialService.atualizar_ambiente(ambiente, schema)
        messages.success(request, "Ambiente atualizado.")
    except (ValidationError, ValueError) as exc:
        messages.error(request, str(exc))
    return redirect("comercial:detalhe", pk=pk)


@comercial_editar_requerido
def ambiente_excluir_post(request, pk: int, ambiente_id: int):
    if request.method != "POST":
        return redirect("comercial:detalhe", pk=pk)
    cliente = get_object_or_404(ClienteComercial, pk=pk)
    ambiente = get_object_or_404(AmbienteOrcamento, pk=ambiente_id, cliente=cliente)
    ClienteComercialService.remover_ambiente(ambiente)
    messages.success(request, "Ambiente removido.")
    return redirect("comercial:detalhe", pk=pk)


@comercial_editar_requerido
def ambiente_detalhes(request, pk: int, ambiente_id: int):
    """Página de edição de detalhes de um ambiente (acabamentos, eletrodomésticos, observações)."""
    cliente = get_object_or_404(ClienteComercial, pk=pk)
    ambiente = get_object_or_404(AmbienteOrcamento, pk=ambiente_id, cliente=cliente)
    idx = ComercialSelector.dinabox_index_por_customer_id(cliente.customer_id)
    
    return render(
        request,
        "comercial/ambiente_detalhes.html",
        {
            "cliente": cliente,
            "ambiente": ambiente,
            "dinabox": idx,
            "pode_editar": True,
        },
    )


@comercial_editar_requerido
def ambiente_adicionar_acabamento_post(request, pk: int, ambiente_id: int):
    if request.method != "POST":
        return redirect("comercial:ambiente_detalhes", pk=pk, ambiente_id=ambiente_id)
    cliente = get_object_or_404(ClienteComercial, pk=pk)
    ambiente = get_object_or_404(AmbienteOrcamento, pk=ambiente_id, cliente=cliente)
    try:
        from .schemas.cliente import AmbienteDetalhesInputSchema
        acabamento = request.POST.get("acabamento", "").strip()
        if acabamento:
            ClienteComercialService.adicionar_acabamento(ambiente, acabamento)
            messages.success(request, f"Acabamento '{acabamento}' adicionado.")
        else:
            messages.warning(request, "Acabamento não pode estar vazio.")
    except (ValidationError, ValueError) as exc:
        messages.error(request, str(exc))
    return redirect("comercial:ambiente_detalhes", pk=pk, ambiente_id=ambiente_id)


@comercial_editar_requerido
def ambiente_remover_acabamento_post(request, pk: int, ambiente_id: int):
    if request.method != "POST":
        return redirect("comercial:ambiente_detalhes", pk=pk, ambiente_id=ambiente_id)
    cliente = get_object_or_404(ClienteComercial, pk=pk)
    ambiente = get_object_or_404(AmbienteOrcamento, pk=ambiente_id, cliente=cliente)
    try:
        acabamento = request.POST.get("acabamento", "").strip()
        ClienteComercialService.remover_acabamento(ambiente, acabamento)
        messages.success(request, "Acabamento removido.")
    except (ValidationError, ValueError) as exc:
        messages.error(request, str(exc))
    return redirect("comercial:ambiente_detalhes", pk=pk, ambiente_id=ambiente_id)


@comercial_editar_requerido
def ambiente_adicionar_eletrodomestico_post(request, pk: int, ambiente_id: int):
    if request.method != "POST":
        return redirect("comercial:ambiente_detalhes", pk=pk, ambiente_id=ambiente_id)
    cliente = get_object_or_404(ClienteComercial, pk=pk)
    ambiente = get_object_or_404(AmbienteOrcamento, pk=ambiente_id, cliente=cliente)
    try:
        eletro = request.POST.get("eletrodomestico", "").strip()
        if eletro:
            ClienteComercialService.adicionar_eletrodomestico(ambiente, eletro)
            messages.success(request, f"Eletrodoméstico '{eletro}' adicionado.")
        else:
            messages.warning(request, "Eletrodoméstico não pode estar vazio.")
    except (ValidationError, ValueError) as exc:
        messages.error(request, str(exc))
    return redirect("comercial:ambiente_detalhes", pk=pk, ambiente_id=ambiente_id)


@comercial_editar_requerido
def ambiente_remover_eletrodomestico_post(request, pk: int, ambiente_id: int):
    if request.method != "POST":
        return redirect("comercial:ambiente_detalhes", pk=pk, ambiente_id=ambiente_id)
    cliente = get_object_or_404(ClienteComercial, pk=pk)
    ambiente = get_object_or_404(AmbienteOrcamento, pk=ambiente_id, cliente=cliente)
    try:
        eletro = request.POST.get("eletrodomestico", "").strip()
        ClienteComercialService.remover_eletrodomestico(ambiente, eletro)
        messages.success(request, "Eletrodoméstico removido.")
    except (ValidationError, ValueError) as exc:
        messages.error(request, str(exc))
    return redirect("comercial:ambiente_detalhes", pk=pk, ambiente_id=ambiente_id)


@comercial_editar_requerido
def ambiente_atualizar_observacoes_post(request, pk: int, ambiente_id: int):
    if request.method != "POST":
        return redirect("comercial:ambiente_detalhes", pk=pk, ambiente_id=ambiente_id)
    cliente = get_object_or_404(ClienteComercial, pk=pk)
    ambiente = get_object_or_404(AmbienteOrcamento, pk=ambiente_id, cliente=cliente)
    try:
        observacoes = request.POST.get("observacoes_especiais", "").strip()
        from .schemas.cliente import AmbienteDetalhesInputSchema
        schema = AmbienteDetalhesInputSchema(observacoes_especiais=observacoes)
        ClienteComercialService.atualizar_observacoes_especiais(ambiente, schema)
        messages.success(request, "Observações especiais atualizadas.")
    except (ValidationError, ValueError) as exc:
        messages.error(request, str(exc))
    return redirect("comercial:ambiente_detalhes", pk=pk, ambiente_id=ambiente_id)


@comercial_excluir_requerido
def excluir_post(request, pk: int):
    if request.method != "POST":
        return redirect("comercial:detalhe", pk=pk)
    cliente = get_object_or_404(ClienteComercial, pk=pk)
    try:
        ClienteComercialService.excluir_cliente_completo(cliente)
        messages.success(request, "Cliente removido na Dinabox e ficha comercial apagada.")
    except ValueError as exc:
        messages.error(request, str(exc))
    return redirect("comercial:lista")

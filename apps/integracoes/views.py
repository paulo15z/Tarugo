from __future__ import annotations

from types import SimpleNamespace

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from apps.integracoes.dinabox.api_service import DinaboxApiService
from apps.integracoes.dinabox.client import DinaboxAPIClient, DinaboxAuthError, DinaboxRequestError


def _user_pode_testar_integracoes(user) -> bool:
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser or user.is_staff:
        return True
    return user.groups.filter(name__in=["PCP", "TI", "Gestao", "GESTAO"]).exists()


def _obter_servico_dinabox() -> DinaboxApiService:
    return DinaboxApiService()


def _coerce_page(raw_value) -> int:
    try:
        value = int(raw_value)
    except (TypeError, ValueError):
        return 1
    return value if value > 0 else 1


@login_required
def dinabox_conectar(request: HttpRequest):
    if not _user_pode_testar_integracoes(request.user):
        messages.error(request, "Somente PCP, TI, Gestao ou admin podem acessar a integracao Dinabox.")
        return redirect("estoque:lista_produtos")

    force_refresh = request.method == "POST"
    service = _obter_servico_dinabox()

    profile = {}
    auth = {}
    conectado = False
    erro = ""

    try:
        service.client.obter_token(force_refresh=force_refresh)
        profile, auth = service.get_service_account_profile()
        conectado = True
        if force_refresh:
            messages.success(request, "Token da conta tecnica Dinabox renovado com sucesso.")
    except DinaboxAuthError as exc:
        erro = str(exc)
        messages.error(request, f"Falha de autenticacao da conta tecnica Dinabox: {exc}")
    except DinaboxRequestError as exc:
        erro = str(exc)
        messages.error(request, f"Falha ao consultar perfil da conta tecnica Dinabox: {exc}")

    return render(
        request,
        "integracoes/dinabox/conectar.html",
        {
            "dinabox_conectado": conectado,
            "dinabox_profile": profile,
            "dinabox_auth": auth,
            "dinabox_error": erro,
        },
    )


@login_required
@require_POST
def dinabox_desconectar(request: HttpRequest):
    DinaboxAPIClient.invalidar_cache_global()
    messages.success(request, "Cache de token Dinabox limpo. A proxima chamada ira reautenticar.")
    return redirect("integracoes:dinabox-conectar")


@login_required
@require_POST
def dinabox_test_auth(request):
    if not _user_pode_testar_integracoes(request.user):
        return JsonResponse({"erro": "Somente PCP, TI, Gestao ou admin podem testar integracoes."}, status=403)

    force_refresh = str(request.POST.get("force_refresh", "")).strip().lower() in {"1", "true", "on", "sim"}

    try:
        service = _obter_servico_dinabox()
        token_result = service.client.obter_token(force_refresh=force_refresh)
        profile = service.client.get_user_info()
        token_preview = (token_result.token[:6] + "..." + token_result.token[-4:]) if len(token_result.token) >= 12 else "***"

        return JsonResponse(
            {
                "sucesso": True,
                "mensagem": "Autenticacao Dinabox (conta tecnica) realizada com sucesso.",
                "token_preview": token_preview,
                "expires_in": token_result.expires_in,
                "token_type": token_result.token_type,
                "user_login": token_result.user_login or profile.get("user_login"),
                "user_display_name": token_result.user_display_name or profile.get("user_display_name"),
                "user_email": token_result.user_email or profile.get("user_email"),
            }
        )
    except DinaboxAuthError as exc:
        return JsonResponse({"sucesso": False, "erro": str(exc)}, status=400)
    except DinaboxRequestError as exc:
        return JsonResponse({"sucesso": False, "erro": str(exc)}, status=502)


@login_required
def dinabox_capacidades(request: HttpRequest):
    if not _user_pode_testar_integracoes(request.user):
        messages.error(request, "Somente PCP, TI, Gestao ou admin podem acessar a integracao Dinabox.")
        return redirect("estoque:lista_produtos")

    service = _obter_servico_dinabox()
    capabilities: list[dict] = []

    try:
        capabilities = service.discover_capabilities()
    except DinaboxAuthError as exc:
        messages.error(request, f"Falha de autenticacao da conta tecnica Dinabox: {exc}")
    except DinaboxRequestError as exc:
        messages.error(request, f"Falha ao extrair capacidades da API Dinabox: {exc}")

    return render(
        request,
        "integracoes/dinabox/capacidades.html",
        {
            "capabilities": capabilities,
        },
    )


@login_required
def dinabox_projetos_list(request: HttpRequest):
    if not _user_pode_testar_integracoes(request.user):
        messages.error(request, "Somente PCP, TI, Gestao ou admin podem acessar a integracao Dinabox.")
        return redirect("estoque:lista_produtos")

    service = _obter_servico_dinabox()

    page = _coerce_page(request.GET.get("p", "1"))
    search = str(request.GET.get("s", "")).strip() or None
    status = str(request.GET.get("status", "")).strip() or None

    try:
        response = service.list_projects(page=page, search=search, status=status)
    except DinaboxAuthError as exc:
        messages.error(request, f"Falha de autenticacao da conta tecnica Dinabox: {exc}")
        return redirect("integracoes:dinabox-conectar")
    except DinaboxRequestError as exc:
        messages.error(request, f"Falha ao consultar projetos na Dinabox: {exc}")
        response = SimpleNamespace(projects=[], total=0, quantity=10, page=page)

    return render(
        request,
        "integracoes/dinabox/projetos_list.html",
        {
            "response": response,
            "search": search or "",
            "status": status or "",
        },
    )


@login_required
def dinabox_projeto_detail(request: HttpRequest, project_id: str):
    if not _user_pode_testar_integracoes(request.user):
        messages.error(request, "Somente PCP, TI, Gestao ou admin podem acessar a integracao Dinabox.")
        return redirect("estoque:lista_produtos")

    service = _obter_servico_dinabox()

    try:
        projeto = service.get_project_detail(project_id)
    except DinaboxAuthError as exc:
        messages.error(request, f"Falha de autenticacao da conta tecnica Dinabox: {exc}")
        return redirect("integracoes:dinabox-conectar")
    except DinaboxRequestError as exc:
        messages.error(request, f"Falha ao consultar projeto na Dinabox: {exc}")
        return redirect("integracoes:dinabox-projetos-list")

    return render(request, "integracoes/dinabox/projeto_detail.html", {"projeto": projeto})


@login_required
def dinabox_lotes_list(request: HttpRequest):
    if not _user_pode_testar_integracoes(request.user):
        messages.error(request, "Somente PCP, TI, Gestao ou admin podem acessar a integracao Dinabox.")
        return redirect("estoque:lista_produtos")

    service = _obter_servico_dinabox()

    page = _coerce_page(request.GET.get("p", "1"))
    search = str(request.GET.get("s", "")).strip() or None

    try:
        response = service.list_groups(page=page, search=search)
    except DinaboxAuthError as exc:
        messages.error(request, f"Falha de autenticacao da conta tecnica Dinabox: {exc}")
        return redirect("integracoes:dinabox-conectar")
    except DinaboxRequestError as exc:
        messages.error(request, f"Falha ao consultar lotes na Dinabox: {exc}")
        response = SimpleNamespace(project_groups=[], total=0, page=page)

    return render(
        request,
        "integracoes/dinabox/lotes_list.html",
        {
            "response": response,
            "search": search or "",
        },
    )


@login_required
def dinabox_lote_detail(request: HttpRequest, group_id: str):
    if not _user_pode_testar_integracoes(request.user):
        messages.error(request, "Somente PCP, TI, Gestao ou admin podem acessar a integracao Dinabox.")
        return redirect("estoque:lista_produtos")

    service = _obter_servico_dinabox()

    try:
        lote = service.get_group_detail(group_id)
    except DinaboxAuthError as exc:
        messages.error(request, f"Falha de autenticacao da conta tecnica Dinabox: {exc}")
        return redirect("integracoes:dinabox-conectar")
    except DinaboxRequestError as exc:
        messages.error(request, f"Falha ao consultar lote na Dinabox: {exc}")
        return redirect("integracoes:dinabox-lotes-list")

    return render(request, "integracoes/dinabox/lote_detail.html", {"lote": lote})

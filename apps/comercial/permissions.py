from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect


def _nomes_grupos(user) -> set[str]:
    if not user or not user.is_authenticated:
        return set()
    return {n.lower() for n in user.groups.values_list("name", flat=True)}


def pode_ver_comercial(user) -> bool:
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return bool(
        _nomes_grupos(user)
        & {
            "comercial_orcamentista",
            "comercial_consultor",
            "comercial_leitura",
            "gestao",
            "ti",
        }
    )


def pode_editar_comercial(user) -> bool:
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return bool(
        _nomes_grupos(user)
        & {
            "comercial_orcamentista",
            "comercial_consultor",
            "ti",
        }
    )


def pode_excluir_cliente_comercial(user) -> bool:
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return bool(_nomes_grupos(user) & {"comercial_orcamentista", "ti"})


def comercial_login_e_ver(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("login")
        if not pode_ver_comercial(request.user):
            messages.error(request, "Sem permissão para acessar o módulo Comercial.")
            return redirect("entrada")
        return view_func(request, *args, **kwargs)

    return wrapper


def comercial_editar_requerido(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("login")
        if not pode_editar_comercial(request.user):
            messages.error(request, "Sem permissão para alterar dados comerciais.")
            return redirect("comercial:lista")
        return view_func(request, *args, **kwargs)

    return wrapper


def comercial_excluir_requerido(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("login")
        if not pode_excluir_cliente_comercial(request.user):
            messages.error(request, "Apenas orçamentista (ou TI) pode excluir cliente na Dinabox.")
            return redirect("comercial:lista")
        return view_func(request, *args, **kwargs)

    return wrapper

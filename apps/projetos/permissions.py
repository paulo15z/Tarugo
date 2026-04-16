from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect


def _nomes_grupos(user) -> set[str]:
    if not user or not user.is_authenticated:
        return set()
    return {n.lower() for n in user.groups.values_list("name", flat=True)}


def pode_ver_projetos(user) -> bool:
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser or user.is_staff:
        return True
    return bool(
        _nomes_grupos(user)
        & {
            "projetos_distribuidor",
            "projetos_projetista",
            "projetos_liberadortecnico",
            "gestao",
            "ti",
            "comercial_orcamentista",
            "comercial_consultor",
        }
    )


def pode_editar_projetos(user) -> bool:
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser or user.is_staff:
        return True
    return bool(
        _nomes_grupos(user)
        & {
            "projetos_distribuidor",
            "projetos_projetista",
            "projetos_liberadortecnico",
            "ti",
        }
    )


def projetos_login_e_ver(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("login")
        if not pode_ver_projetos(request.user):
            messages.error(request, "Sem permissao para acessar o modulo Projetos.")
            return redirect("entrada")
        return view_func(request, *args, **kwargs)

    return wrapper


def projetos_editar_requerido(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("login")
        if not pode_editar_projetos(request.user):
            messages.error(request, "Sem permissao para alterar projetos.")
            return redirect("projetos:index")
        return view_func(request, *args, **kwargs)

    return wrapper

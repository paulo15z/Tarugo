# apps/estoque/permissions.py
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def grupo_requerido(*grupos):
    """
    Decorator que verifica se o usuário pertence a pelo menos um dos grupos.
    Uso: @grupo_requerido('estoque.02', 'estoque.03')
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')

            # Superusuário passa sempre
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            grupos_do_usuario = request.user.groups.values_list('name', flat=True)
            if any(g in grupos_do_usuario for g in grupos):
                return view_func(request, *args, **kwargs)

            messages.error(request, 'Você não tem permissão para acessar esta página.')
            return redirect('estoque:lista_produtos')

        return wrapper
    return decorator
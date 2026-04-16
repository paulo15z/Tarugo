from django.shortcuts import get_object_or_404, redirect, render

from apps.projetos.domain.status import ProjetoStatus
from apps.projetos.models import Projeto
from apps.projetos.permissions import projetos_editar_requerido, projetos_login_e_ver
from apps.projetos.services import ProjetoService


@projetos_login_e_ver
def index(request):
    status = (request.GET.get("status") or "").strip().upper()
    numero_pedido = (request.GET.get("pedido") or "").strip()

    queryset = Projeto.objects.select_related("pedido", "ambiente_pedido", "projetista", "liberador_tecnico")
    if status in ProjetoStatus.values:
        queryset = queryset.filter(status=status)
    else:
        status = ""
    if numero_pedido:
        queryset = queryset.filter(pedido__numero_pedido__icontains=numero_pedido)

    return render(
        request,
        "projetos/index.html",
        {
            "rows": queryset.order_by("-criado_em"),
            "status": status,
            "pedido": numero_pedido,
            "status_choices": ProjetoStatus.choices,
        },
    )


@projetos_login_e_ver
def pedido_projetos(request, numero_pedido: str):
    rows = Projeto.objects.filter(pedido__numero_pedido=numero_pedido).select_related(
        "pedido", "ambiente_pedido", "projetista", "liberador_tecnico"
    ).order_by("ambiente_pedido__nome_ambiente")
    pedido = rows.first().pedido if rows else None
    return render(
        request,
        "projetos/pedido_projetos.html",
        {
            "pedido_obj": pedido,
            "rows": rows,
            "numero_pedido": numero_pedido,
        },
    )


@projetos_login_e_ver
def projeto_detail(request, pk: int):
    projeto = get_object_or_404(
        Projeto.objects.select_related("pedido", "ambiente_pedido", "projetista", "liberador_tecnico", "distribuidor"),
        pk=pk,
    )
    return render(
        request,
        "projetos/projeto_detail.html",
        {"projeto": projeto, "status_choices": ProjetoStatus.choices},
    )


@projetos_editar_requerido
def projeto_status_post(request, pk: int):
    if request.method != "POST":
        return redirect("projetos:projeto-detail", pk=pk)
    projeto = get_object_or_404(Projeto, pk=pk)
    novo_status = (request.POST.get("status") or "").strip()
    try:
        ProjetoService.atualizar_status(projeto, novo_status, usuario=request.user)
    except ValueError as exc:
        from django.contrib import messages

        messages.error(request, str(exc))
    else:
        from django.contrib import messages

        messages.success(request, "Status do projeto atualizado.")
    return redirect("projetos:projeto-detail", pk=pk)

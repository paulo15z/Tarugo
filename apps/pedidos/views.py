"""
Views web (HTML) para o app pedidos.

Responsabilidade: Renderização de templates.
"""

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator

from apps.pedidos.selectors import PedidoSelector, AmbienteSelector
from apps.pedidos.mappers import PedidoMapper


@login_required
def index(request):
    """
    Dashboard de pedidos.
    """
    pedidos = PedidoSelector.list_pedidos_ativos()
    
    # Paginação
    paginator = Paginator(pedidos, 20)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        "page_obj": page_obj,
        "total_pedidos": paginator.count,
    }
    return render(request, "pedidos/index.html", context)


@login_required
def pedido_detail(request, numero_pedido):
    """
    Detalhes de um pedido com todos seus ambientes.
    """
    pedido = PedidoSelector.get_pedido_completo(numero_pedido)
    if not pedido:
        return render(request, "pedidos/pedido_not_found.html", {"numero_pedido": numero_pedido}, status=404)
    
    context = {
        "pedido": pedido,
        "schema": PedidoMapper.model_to_detalhe_schema(pedido),
    }
    return render(request, "pedidos/pedido_detail.html", context)


@login_required
def ambiente_detail(request, pk):
    """
    Detalhes de um ambiente específico.
    """
    ambiente = AmbienteSelector.get_ambiente_completo(pk)
    if not ambiente:
        return render(request, "pedidos/ambiente_not_found.html", {"ambiente_id": pk}, status=404)
    
    context = {
        "ambiente": ambiente,
    }
    return render(request, "pedidos/ambiente_detail.html", context)


@login_required
def buscar_pedidos(request):
    """
    Página de busca de pedidos.
    """
    query = request.GET.get("q", "")
    status_filtro = request.GET.get("status", "")
    
    if query:
        pedidos = PedidoSelector.search_pedidos(query)
    elif status_filtro:
        pedidos = PedidoSelector.list_pedidos_por_status(status_filtro)
    else:
        pedidos = PedidoSelector.list_pedidos_ativos()
    
    # Paginação
    paginator = Paginator(pedidos, 20)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        "page_obj": page_obj,
        "query": query,
        "status_filtro": status_filtro,
    }
    return render(request, "pedidos/buscar_pedidos.html", context)

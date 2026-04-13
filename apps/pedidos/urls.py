"""
URL Config para o app pedidos.
"""

from django.urls import path

from apps.pedidos.api import (
    pedido_list,
    pedido_detail,
    pedido_atualizar_status,
    pedido_historico_status,
    ambiente_list,
    ambiente_detail,
    ambiente_processar_engenharia,
)

app_name = "pedidos"

urlpatterns = [
    # Pedidos
    path("api/pedidos/", pedido_list, name="api-pedido-list"),
    path("api/pedidos/<str:numero_pedido>/", pedido_detail, name="api-pedido-detail"),
    path(
        "api/pedidos/<str:numero_pedido>/atualizar-status/",
        pedido_atualizar_status,
        name="api-pedido-atualizar-status",
    ),
    path(
        "api/pedidos/<str:numero_pedido>/historico-status/",
        pedido_historico_status,
        name="api-pedido-historico-status",
    ),
    # Ambientes
    path("api/ambientes/", ambiente_list, name="api-ambiente-list"),
    path("api/ambientes/<int:pk>/", ambiente_detail, name="api-ambiente-detail"),
    path(
        "api/ambientes/<int:pk>/processar-engenharia/",
        ambiente_processar_engenharia,
        name="api-ambiente-processar-engenharia",
    ),
]

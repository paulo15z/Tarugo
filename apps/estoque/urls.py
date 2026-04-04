from django.urls import path
from . import views

app_name = "estoque"

urlpatterns = [
    path("", views.lista_produtos, name="lista_produtos"),
    path("movimentacao/", views.movimentacao_create, name="movimentacao_create"),
    path("produtos/novo/", views.produto_create, name="produto_create"),
    path("reservas/", views.lista_reservas, name="lista_reservas"),
    path("reservas/nova/", views.reserva_create, name="reserva_create"),
    path("produtos/<int:produto_id>/config/", views.produto_config_update, name="produto_config_update"),
    path("pedidos/<int:pedido_id>/toggle-bloqueio/", views.pedido_toggle_bloqueio, name="pedido_toggle_bloqueio"),
]
from django.urls import path

from apps.estoque.api.views import (
    ProdutoCreateView,
    DisponibilidadeView,
    MovimentacaoView,
    MovimentacaoListView,
    AjusteLoteView,
    BaixoEstoqueView,
    ReservaView,
    ReservaCancelarView,
    ReservaConsumirView,
)

urlpatterns = [
    path('produtos/', ProdutoCreateView.as_view(), name='produto-create'),
    path('disponibilidade/', DisponibilidadeView.as_view(), name='disponibilidade'),
    path('movimentar/', MovimentacaoView.as_view(), name='movimentacao-create'),
    path('movimentacoes/', MovimentacaoListView.as_view(), name='movimentacao-list'),
    path('movimentar/lote/', AjusteLoteView.as_view(), name='movimentacao-lote'),
    path('reservas/', ReservaView.as_view(), name='reserva-create'),
    path('reservas/<int:reserva_id>/cancelar/', ReservaCancelarView.as_view(), name='reserva-cancelar'),
    path('reservas/<int:reserva_id>/consumir/', ReservaConsumirView.as_view(), name='reserva-consumir'),
    path('produtos/baixo-estoque/', BaixoEstoqueView.as_view(), name='produto-baixo-estoque'),
]

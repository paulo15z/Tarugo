from django.urls import path

from apps.estoque.api.views import (
    ProdutoCreateView,
    MovimentacaoView,
    MovimentacaoListView,
    AjusteLoteView,
    BaixoEstoqueView,
)

urlpatterns = [
    path('produtos/', ProdutoCreateView.as_view(), name='produto-create'),
    path('movimentar/', MovimentacaoView.as_view(), name='movimentacao-create'),
    path('movimentacoes/', MovimentacaoListView.as_view(), name='movimentacao-list'),
    path('movimentar/lote/', AjusteLoteView.as_view(), name='movimentacao-lote'),
    path('produtos/baixo-estoque/', BaixoEstoqueView.as_view(), name='produto-baixo-estoque'),
]

from django.urls import path
from .views import (
    BipagemView,
    PecaDetailView,
    BuscaPecaView,
    PedidoDetailView,
    ModuloDetailView,
    LoteProducaoListView,
    PedidoLotesView,
    LotePecasView,
)
from .views_lots import (
    LotesListView, LoteDetailView, PecasPorLoteView
)
from .views_import import ImportarCSVView

app_name = 'bipagem-api'

urlpatterns = [
    # Lotes (para interface de scanning)
    path('lotes/', LotesListView.as_view(), name='lotes-list'),
    path('lotes/<int:lote_id>/', LoteDetailView.as_view(), name='lote-detail'),
    path('lotes/<int:lote_id>/pecas/', PecasPorLoteView.as_view(), name='pecas-por-lote'),
    
    # Bipagem principal (scanner)
    path('bipagem/', BipagemView.as_view(), name='bipagem'),

    # Detalhes
    path('peca/<str:id_peca>/', PecaDetailView.as_view(), name='peca-detail'),
    path('modulo/<str:referencia>/', ModuloDetailView.as_view(), name='modulo-detail'),
    path('pedido/<str:numero_pedido>/', PedidoDetailView.as_view(), name='pedido-detail'),

    # Busca rápida
    path('buscar/', BuscaPecaView.as_view(), name='buscar'),

    # Novos endpoints de LoteProducao (Sprint 1)
    path('lotes-producao/', LoteProducaoListView.as_view(), name='lotes-producao-list'),
    path('pedidos/<str:numero>/lotes-producao/', PedidoLotesView.as_view(), name='pedido-lotes-producao'),
    path('lotes-producao/<int:id>/pecas/', LotePecasView.as_view(), name='lote-producao-pecas'),

    path("importar-csv/", ImportarCSVView.as_view()),
]

from django.urls import path
from .views import (
    BipagemView, PecaDetailView, BuscaPecaView,
    PedidoDetailView, ModuloDetailView
)

app_name = 'bipagem-api'

urlpatterns = [
    # Bipagem principal (scanner)
    path('bipagem/', BipagemView.as_view(), name='bipagem'),
    
    # Detalhes
    path('peca/<str:id_peca>/', PecaDetailView.as_view(), name='peca-detail'),
    path('modulo/<str:referencia>/', ModuloDetailView.as_view(), name='modulo-detail'),
    path('pedido/<str:numero_pedido>/', PedidoDetailView.as_view(), name='pedido-detail'),
    
    # Busca rápida
    path('buscar/', BuscaPecaView.as_view(), name='buscar'),
]
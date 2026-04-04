"""
apps/bipagem/urls.py

Rotas do app de bipagem (server-rendered).
Tudo que for API REST fica em apps/bipagem/api/urls.py
"""
from django.urls import path
from . import views
from .views_scanner import BipagemScannerView

app_name = 'bipagem'

urlpatterns = [
    # Dashboard operacional
    path('', views.index, name='index'),

    # Conferência de lote (scanner de peças)
    path('lote/<str:numero_pedido>/', views.pedido_detalhe, name='pedido_detalhe'),

    # Detalhe de módulo
    path('modulo/<str:referencia_modulo>/', views.modulo_detalhe, name='modulo_detalhe'),

    # Ações do operador
    path('lote/<str:numero_pedido>/toggle-bloqueio/', views.toggle_bloqueio_pedido_view, name='toggle_bloqueio'),

    # Detalhe de LoteProducao por ID (lotes mistos / múltiplos pedidos)
    path('lote-producao/<int:lote_id>/', views.lote_producao_detail, name='lote_producao_detail'),

    # Interface standalone de scanner (MVP)
    path('scanner/', BipagemScannerView.as_view(), name='scanner'),
]
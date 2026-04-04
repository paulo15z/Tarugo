from django.urls import path
from . import views
from .views_scanner import BipagemScannerView

app_name = 'bipagem'

urlpatterns = [
    path('', views.index, name='index'),
    path('pedidos/', views.pedidos_list, name='pedidos'),
    path('pedido/<str:numero_pedido>/', views.pedido_detalhe, name='pedido_detalhe'),
    path('modulo/<str:referencia_modulo>/', views.modulo_detalhe, name='modulo_detalhe'),
    
    # Scanner interface (MVP)
    path('scanner/', BipagemScannerView.as_view(), name='scanner'),
]

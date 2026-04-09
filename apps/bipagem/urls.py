from django.urls import path

from . import views

app_name = 'bipagem'

urlpatterns = [
    path('', views.index, name='index'),
    path('viagens/', views.viagens_index, name='viagens'),
    path('viagens/<str:codigo>/', views.viagem_detalhe, name='viagem_detalhe'),
    path('lote/<str:numero_pedido>/', views.pedido_detalhe, name='pedido_detalhe'),
    path('operacional/lote/<str:numero_pedido>/', views.operacional_lote, name='operacional_lote'),
    path('lote/<str:numero_pedido>/estornar/', views.estornar_peca_view, name='estornar_peca'),
]

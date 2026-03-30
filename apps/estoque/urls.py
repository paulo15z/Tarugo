from django.urls import path
import apps.estoque.api.views as views

urlpatterns = [
    path('', views.dashboard, name='estoque-dashboard'),
    path('produtos/', views.lista_produtos, name='estoque-produtos'),
    path('produtos/novo/', views.novo_produto, name='estoque-produto-novo'),
    path('movimentar/', views.movimentar, name='estoque-movimentar'),
    path('historico/', views.historico, name='estoque-historico'),
    path('reservas/', views.reservas, name='estoque-reservas'),
]
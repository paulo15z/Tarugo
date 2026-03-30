# apps/estoque/urls.py
from django.urls import path

from . import views   # ← views.py da raiz (template views)

app_name = 'estoque'

urlpatterns = [
    path('', views.dashboard, name='estoque-dashboard'),
    path('movimentacao/nova/', views.movimentacao_create, name='movimentacao-create'),
]
from django.urls import path
from . import views

app_name = "estoque"

urlpatterns = [
    path("", views.lista_produtos, name="lista_produtos"),
    path("movimentacao/", views.movimentacao_create, name="movimentacao_create"),
]
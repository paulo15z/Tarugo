from django.urls import path
from . import views

app_name = "dinabox_api"

urlpatterns = [
    path('importar/', views.importar_projeto_api, name='importar-projeto'),
    path('projetos/<str:projeto_id>/modulos-pecas/', views.projeto_modulos_pecas, name='projeto-modulos-pecas'),
]
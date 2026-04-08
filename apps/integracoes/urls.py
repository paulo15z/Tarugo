from django.urls import path

from . import views

app_name = "integracoes"

urlpatterns = [
    path("dinabox/conectar/", views.dinabox_conectar, name="dinabox-conectar"),
    path("dinabox/capacidades/", views.dinabox_capacidades, name="dinabox-capacidades"),
    path("dinabox/desconectar/", views.dinabox_desconectar, name="dinabox-desconectar"),
    path("dinabox/test-auth/", views.dinabox_test_auth, name="dinabox-test-auth"),
    path("dinabox/projetos/", views.dinabox_projetos_list, name="dinabox-projetos-list"),
    path("dinabox/projetos/<str:project_id>/", views.dinabox_projeto_detail, name="dinabox-projeto-detail"),
    path("dinabox/lotes/", views.dinabox_lotes_list, name="dinabox-lotes-list"),
    path("dinabox/lotes/<str:group_id>/", views.dinabox_lote_detail, name="dinabox-lote-detail"),
]

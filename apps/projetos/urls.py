from django.urls import path

from apps.projetos import views

app_name = "projetos"

urlpatterns = [
    path("", views.index, name="index"),
    path("pedido/<str:numero_pedido>/", views.pedido_projetos, name="pedido-projetos"),
    path("<int:pk>/", views.projeto_detail, name="projeto-detail"),
    path("<int:pk>/status/", views.projeto_status_post, name="projeto-status-post"),
]

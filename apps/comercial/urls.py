from django.urls import path

from . import views

app_name = "comercial"

urlpatterns = [
    path("", views.lista, name="lista"),
    path("novo/", views.novo, name="novo"),
    path("vincular/", views.vincular, name="vincular"),
    path("<int:pk>/", views.detalhe, name="detalhe"),
    path("<int:pk>/editar-dinabox/", views.editar_dinabox, name="editar_dinabox"),
    path("<int:pk>/status/", views.status_post, name="status_post"),
    path("<int:pk>/numero-pedido/", views.numero_pedido_post, name="numero_pedido_post"),
    path("<int:pk>/enviar-para-projetos/", views.enviar_para_projetos_post, name="enviar_para_projetos_post"),
    path("<int:pk>/observacao/", views.observacao_post, name="observacao_post"),
    path("<int:pk>/ambiente/", views.ambiente_novo_post, name="ambiente_novo_post"),
    path("<int:pk>/ambiente/<int:ambiente_id>/", views.ambiente_editar_post, name="ambiente_editar_post"),
    path(
        "<int:pk>/ambiente/<int:ambiente_id>/detalhes/",
        views.ambiente_detalhes,
        name="ambiente_detalhes",
    ),
    path(
        "<int:pk>/ambiente/<int:ambiente_id>/acabamento/",
        views.ambiente_adicionar_acabamento_post,
        name="ambiente_adicionar_acabamento_post",
    ),
    path(
        "<int:pk>/ambiente/<int:ambiente_id>/acabamento/remover/",
        views.ambiente_remover_acabamento_post,
        name="ambiente_remover_acabamento_post",
    ),
    path(
        "<int:pk>/ambiente/<int:ambiente_id>/eletrodomestico/",
        views.ambiente_adicionar_eletrodomestico_post,
        name="ambiente_adicionar_eletrodomestico_post",
    ),
    path(
        "<int:pk>/ambiente/<int:ambiente_id>/eletrodomestico/remover/",
        views.ambiente_remover_eletrodomestico_post,
        name="ambiente_remover_eletrodomestico_post",
    ),
    path(
        "<int:pk>/ambiente/<int:ambiente_id>/observacoes/",
        views.ambiente_atualizar_observacoes_post,
        name="ambiente_atualizar_observacoes_post",
    ),
    path(
        "<int:pk>/ambiente/<int:ambiente_id>/excluir/",
        views.ambiente_excluir_post,
        name="ambiente_excluir_post",
    ),
    path("<int:pk>/excluir/", views.excluir_post, name="excluir_post"),
]

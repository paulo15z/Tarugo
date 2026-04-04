from django.urls import path
from . import views

app_name = 'pcp'

urlpatterns = [
    path('',            views.pcp_index,     name='index'),
    path('processar/',  views.pcp_processar, name='processar'),
    path('historico/',  views.pcp_historico, name='historico'),
    path('liberar/<str:pid>/', views.pcp_liberar, name='liberar'),
    path('liberar-viagem/<str:pid>/', views.pcp_liberar_viagem, name='liberar-viagem'),
    path('download/<str:pid>/', views.pcp_download, name='download'),
]
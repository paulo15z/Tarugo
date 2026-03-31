from django.urls import path
from . import views

urlpatterns = [
    path('',            views.pcp_index,     name='pcp-index'),
    path('processar/',  views.pcp_processar, name='pcp-processar'),
    path('historico/',  views.pcp_historico, name='pcp-historico'),
    path('download/<str:pid>/', views.pcp_download, name='pcp-download'),
]
from django.urls import path
from apps.pcp.api.views import PCPProcessView, PCPDownloadView, PCPHistoricoView
from django.views.generic import TemplateView

urlpatterns = [
    path('processar/', PCPProcessView.as_view(), name='pcp-processar'),
    path('download/<str:pid>/', PCPDownloadView.as_view(), name='pcp-download'),
    path('historico/', PCPHistoricoView.as_view(), name='pcp-historico'),
    path('', TemplateView.as_view(template_name='pcp/index.html'), name='pcp-index'),
]
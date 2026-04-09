from django.urls import path

from .views import BipagemView, LotePecasView, LotePreviewView
from .views_operacional import (
    EnvioExpedicaoDetailView,
    EnvioExpedicaoEntradaView,
    EnvioExpedicaoItemView,
    EnvioExpedicaoListCreateView,
    EnvioExpedicaoModuloView,
    EnvioExpedicaoSaidaView,
    OperacionalAuditoriaPecasView,
    OperacionalEventoPecaView,
    OperacionalResumoLoteView,
    SeparacaoDestinoView,
)

app_name = 'bipagem-api'

urlpatterns = [
    path('bipagem/', BipagemView.as_view(), name='bipagem'),
    path('lotes/<str:pid>/preview/', LotePreviewView.as_view(), name='lote-preview'),
    path('lotes/<str:pid>/pecas/', LotePecasView.as_view(), name='lote-pecas'),
    path('operacional/lotes/<str:pid>/resumo/', OperacionalResumoLoteView.as_view(), name='operacional-lote-resumo'),
    path('operacional/lotes/<str:pid>/pecas/', OperacionalAuditoriaPecasView.as_view(), name='operacional-lote-pecas'),
    path('operacional/eventos/peca/', OperacionalEventoPecaView.as_view(), name='operacional-evento-peca'),
    path('operacional/separacao-destinos/', SeparacaoDestinoView.as_view(), name='operacional-separacao-destinos'),
    path('operacional/envios/', EnvioExpedicaoListCreateView.as_view(), name='operacional-envios'),
    path('operacional/viagens/', EnvioExpedicaoListCreateView.as_view(), name='operacional-viagens'),
    path('operacional/envios/<str:codigo>/', EnvioExpedicaoDetailView.as_view(), name='operacional-envio-detalhe'),
    path('operacional/viagens/<str:codigo>/', EnvioExpedicaoDetailView.as_view(), name='operacional-viagem-detalhe'),
    path('operacional/envios/<str:codigo>/itens/', EnvioExpedicaoItemView.as_view(), name='operacional-envio-itens'),
    path('operacional/envios/<str:codigo>/modulos/', EnvioExpedicaoModuloView.as_view(), name='operacional-envio-modulos'),
    path('operacional/viagens/<str:codigo>/itens/', EnvioExpedicaoItemView.as_view(), name='operacional-viagem-itens'),
    path('operacional/viagens/<str:codigo>/modulos/', EnvioExpedicaoModuloView.as_view(), name='operacional-viagem-modulos'),
    path('operacional/envios/<str:codigo>/entrada/', EnvioExpedicaoEntradaView.as_view(), name='operacional-envio-entrada'),
    path('operacional/envios/<str:codigo>/saida/', EnvioExpedicaoSaidaView.as_view(), name='operacional-envio-saida'),
    path('operacional/viagens/<str:codigo>/entrada/', EnvioExpedicaoEntradaView.as_view(), name='operacional-viagem-entrada'),
    path('operacional/viagens/<str:codigo>/saida/', EnvioExpedicaoSaidaView.as_view(), name='operacional-viagem-saida'),
]

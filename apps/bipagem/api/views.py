from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q

from apps.bipagem.models import Peca, Modulo, Pedido, LoteProducao
from apps.bipagem.services.bipagem_service import registrar_bipagem
from apps.bipagem.selectors.progresso import (
    get_resumo_pedido, 
    get_modulos_pedido, 
    get_pecas_modulo
)
from apps.bipagem.mappers.peca_mapper import map_peca_to_output
from .serializers import (
    PecaDetailSerializer,
    PecaListSerializer,
    PedidoSerializer,
    OrdemProducaoSerializer,
    ModuloSerializer,
    LoteProducaoSerializer
)
from apps.bipagem.selectors.lote_selectors import (
    get_todos_lotes_ativos,
    get_lotes_por_pedido,
    get_pecas_por_lote_producao
)

class BipagemView(APIView):
    """
    POST /api/bipagem/bipagem/
    Body:
    {
        "codigo": "10167150",
        "usuario": "João",
        "localizacao": "Máquina 3 - Corte"
    }
    """
    def post(self, request):
        codigo = request.data.get('codigo', '').strip()
        usuario = request.data.get('usuario', 'DESCONHECIDO')
        localizacao = request.data.get('localizacao', '')

        if not codigo:
            return Response(
                {'erro': 'Código da peça não informado'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Chama o service passando um dicionário compatível com BipagemInput
        resultado = registrar_bipagem({
            'codigo_peca': codigo,
            'usuario': usuario,
            'localizacao': localizacao
        })

        if resultado['sucesso']:
            # O service retorna um dicionário com a peça mapeada para PecaOutput
            return Response({
                'ok': True,
                'mensagem': resultado['mensagem'],
                'repetido': resultado.get('repetido', False),
                'peca': resultado['peca'],
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'erro': resultado['mensagem'],
                'detalhe': resultado.get('erro')
            }, status=status.HTTP_404_NOT_FOUND if 'não encontrada' in resultado['mensagem'] else status.HTTP_400_BAD_REQUEST)

class PecaDetailView(APIView):
    """GET /api/bipagem/peca/<str:id_peca>/"""
    def get(self, request, id_peca):
        try:
            peca = Peca.objects.select_related('modulo__ordem_producao__pedido').get(id_peca=id_peca)
            return Response(map_peca_to_output(peca).model_dump())
        except Peca.DoesNotExist:
            return Response(
                {'erro': f'Peça {id_peca} não encontrada'},
                status=status.HTTP_404_NOT_FOUND
            )

class BuscaPecaView(APIView):
    """GET /api/bipagem/buscar/?q=termo"""
    def get(self, request):
        termo = request.query_params.get('q', '').strip()
        
        if len(termo) < 2:
            return Response({'erro': 'Termo deve ter no mínimo 2 caracteres'}, status=400)
        
        pecas = Peca.objects.filter(
            Q(id_peca__icontains=termo) |
            Q(descricao__icontains=termo) |
            Q(local__icontains=termo)
        ).select_related('modulo__ordem_producao__pedido')[:50]
        
        return Response({
            'total': pecas.count(),
            'pecas': [map_peca_to_output(p).model_dump() for p in pecas]
        })

class PedidoDetailView(APIView):
    """GET /api/bipagem/pedido/<str:numero_pedido>/"""
    def get(self, request, numero_pedido):
        resumo = get_resumo_pedido(numero_pedido)
        if not resumo:
            return Response({'erro': f'Pedido {numero_pedido} não encontrado'}, status=404)
        
        modulos = get_modulos_pedido(numero_pedido)
        
        return Response({
            'resumo': resumo,
            'modulos': modulos
        })

class ModuloDetailView(APIView):
    """GET /api/bipagem/modulo/<str:referencia>/"""
    def get(self, request, referencia):
        try:
            modulo = Modulo.objects.get(referencia_modulo=referencia)
            pecas = get_pecas_modulo(referencia)
            
            return Response({
                'modulo': {
                    'referencia': modulo.referencia_modulo,
                    'nome': modulo.nome_modulo,
                },
                'pecas': [map_peca_to_output(p).model_dump() for p in pecas]
            })
        except Modulo.DoesNotExist:
            return Response({'erro': f'Módulo {referencia} não encontrado'}, status=404)

class LoteProducaoListView(APIView):
    """GET /api/bipagem/lotes-producao/"""
    def get(self, request):
        lotes = get_todos_lotes_ativos()
        return Response(lotes)

class PedidoLotesView(APIView):
    """GET /api/bipagem/pedidos/<str:numero>/lotes-producao/"""
    def get(self, request, numero):
        lotes = get_lotes_por_pedido(numero)
        # Como o selector retorna QuerySet de models, usamos o serializer
        # Mas precisamos anotar os campos de progresso se quisermos no serializer
        from django.db.models import Count, Q
        from apps.bipagem.domain.tipos import StatusPeca
        lotes_anotados = lotes.annotate(
            total_pecas=Count('pecas'),
            pecas_bipadas=Count('pecas', filter=Q(pecas__status=StatusPeca.BIPADA))
        )
        # Adiciona percentual manualmente ou via serializer method
        serializer = LoteProducaoSerializer(lotes_anotados, many=True)
        data = serializer.data
        for item in data:
            total = item['total_pecas']
            bipadas = item['pecas_bipadas']
            item['percentual'] = round((bipadas / total * 100), 1) if total > 0 else 0
            
        return Response(data)

class LotePecasView(APIView):
    """GET /api/bipagem/lotes-producao/<int:id>/pecas/"""
    def get(self, request, id):
        pecas = get_pecas_por_lote_producao(id)
        return Response([map_peca_to_output(p).model_dump() for p in pecas])

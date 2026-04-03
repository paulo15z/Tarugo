# apps/bipagem/api/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q

from apps.bipagem.models import Peca, Modulo, Pedido
from apps.bipagem.services.bipagem_service import registrar_bipagem  # vamos criar esse service agora
from .serializers import (
    PecaDetailSerializer,
    PecaListSerializer,
    PedidoSerializer,
    OrdemProducaoSerializer,
    ModuloSerializer
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

        resultado = registrar_bipagem(
            codigo_peca=codigo,
            usuario=usuario,
            localizacao=localizacao
        )

        if resultado['sucesso']:
            peca = resultado['peca']
            return Response({
                'ok': True,
                'mensagem': f'Peça {codigo} bipada com sucesso',
                'peca': PecaDetailSerializer(peca).data,
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'erro': resultado['erro']
            }, status=status.HTTP_404_NOT_FOUND if 'não encontrada' in resultado['erro'] else status.HTTP_400_BAD_REQUEST)


class PecaDetailView(APIView):
    """GET /api/bipagem/peca/<str:id_peca>/"""
    
    def get(self, request, id_peca):
        try:
            peca = Peca.objects.get(id_peca=id_peca)
            return Response(PecaDetailSerializer(peca).data)
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
        )[:50]
        
        return Response({
            'total': pecas.count(),
            'pecas': PecaListSerializer(pecas, many=True).data
        })


# Views de resumo (úteis para dashboard)
class PedidoDetailView(APIView):
    """GET /api/bipagem/pedido/<str:numero_pedido>/"""
    
    def get(self, request, numero_pedido):
        try:
            pedido = Pedido.objects.get(numero_pedido=numero_pedido)
            ordens = pedido.ordens_producao.all()
            
            return Response({
                'pedido': PedidoSerializer(pedido).data,
                'ordens_producao': OrdemProducaoSerializer(ordens, many=True).data,
            })
        except Pedido.DoesNotExist:
            return Response({'erro': f'Pedido {numero_pedido} não encontrado'}, status=404)


class ModuloDetailView(APIView):
    """GET /api/bipagem/modulo/<str:referencia>/"""
    
    def get(self, request, referencia):
        try:
            modulo = Modulo.objects.get(referencia_modulo=referencia)
            pecas = modulo.pecas.all()
            
            return Response({
                'modulo': ModuloSerializer(modulo).data,
                'pecas': PecaListSerializer(pecas, many=True).data,
                'resumo': {
                    'total': modulo.total_pecas,
                    'bipadas': modulo.pecas_bipadas,
                    'percentual': modulo.percentual_concluido,
                }
            })
        except Modulo.DoesNotExist:
            return Response({'erro': f'Módulo {referencia} não encontrado'}, status=404)
# apps/estoque/api/views.py
from datetime import datetime

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from apps.estoque.api.serializers import (
    ProdutoSerializer,
    MovimentacaoSerializer,
    MovimentacaoListSerializer,
    AjusteLoteSerializer,
)

# Imports corrigidos e alinhados com o padrão Tarugo
from apps.estoque.services.movimentacao_service import MovimentacaoService
from apps.estoque.services.produto_service import criar_produto

from apps.estoque.selectors import (
    listar_movimentacoes,
    get_produtos_baixo_estoque,
    get_saldo_atual,
)


def _parse_date(value: str, field_name: str):
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        raise ValueError(f'{field_name} inválida. Use o formato ISO: YYYY-MM-DD.')


class ProdutoCreateView(APIView):
    def post(self, request):
        serializer = ProdutoSerializer(data=request.data)
        if serializer.is_valid():
            produto = criar_produto(serializer.validated_data)
            return Response(ProdutoSerializer(produto).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MovimentacaoView(APIView):
    def post(self, request):
        serializer = MovimentacaoSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        usuario_id = request.user.id if request.user.is_authenticated else None

        try:
            # Uso da classe Service (padrão Tarugo)
            produto = MovimentacaoService.processar_movimentacao(
                serializer.validated_data, 
                usuario_id=usuario_id
            )
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'message': 'Movimentação realizada com sucesso.',
            'produto_id': produto.id,
            'quantidade_atual': produto.quantidade,
        }, status=status.HTTP_200_OK)


class MovimentacaoListView(APIView):
    def get(self, request):
        params = request.query_params

        try:
            limit = int(params.get('limit', 10))
            offset = int(params.get('offset', 0))
        except (ValueError, TypeError):
            return Response({'error': 'limit e offset devem ser inteiros.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            produto_id = int(params['produto_id']) if params.get('produto_id') else None
            usuario_id = int(params['usuario_id']) if params.get('usuario_id') else None
            data_inicio = _parse_date(params['data_inicio'], 'data_inicio') if params.get('data_inicio') else None
            data_fim = _parse_date(params['data_fim'], 'data_fim') if params.get('data_fim') else None
        except (ValueError, TypeError) as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        tipo = params.get('tipo')

        movimentacoes = listar_movimentacoes(
            produto_id=produto_id,
            tipo=tipo,
            usuario_id=usuario_id,
            data_inicio=data_inicio,
            data_fim=data_fim,
        )

        total = movimentacoes.count()
        paginated = movimentacoes[offset:offset + limit]

        return Response({
            'meta': {
                'total': total,
                'limit': limit,
                'offset': offset,
                'tem_proxima': (offset + limit) < total,
            },
            'data': MovimentacaoListSerializer(paginated, many=True).data,
        })


class AjusteLoteView(APIView):
    def post(self, request):
        serializer = AjusteLoteSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        usuario_id = request.user.id if request.user.is_authenticated else None

        try:
            produtos = MovimentacaoService.processar_ajuste_em_lote(
                serializer.validated_data, 
                usuario_id=usuario_id
            )
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'message': f'{len(produtos)} movimentação(ões) processada(s) com sucesso.',
            'produtos': [{'id': p.id, 'quantidade_atual': p.quantidade} for p in produtos],
        }, status=status.HTTP_200_OK)


class BaixoEstoqueView(APIView):
    def get(self, request):
        produtos = get_produtos_baixo_estoque()
        return Response(ProdutoSerializer(produtos, many=True).data)
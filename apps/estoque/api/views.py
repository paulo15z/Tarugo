from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from apps.estoque.api.serializers import ProdutoSerializer, MovimentacaoSerializer
from apps.estoque.services.produto_service import criar_produto
from apps.estoque.services.movimentacao_services import processar_movimentacao
from apps.estoque.selectors.movimentacao_selectors import listar_movimentacoes
from .serializers import MovimentacaoListSerializer

from datetime import datetime



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
        
        if serializer.is_valid():
            try:
                produto = processar_movimentacao(serializer.validated_data)
                return Response({
                    "message": "Movimentação realizada com Sucesso!",
                    "produto_id": produto.id,
                    "quantidade_atual": produto.quantidade
                })
            except Exception as e:
                return Response(
                    {"error": str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

    

class MovimentacaoListView(APIView):
    def get(self, request):
        # Parâmetros de filtro
        produto_id = request.query_params.get("produto_id")
        data_inicio = request.query_params.get("data_inicio")
        data_fim = request.query_params.get("data_fim")
        
        # Parâmetros de paginação
        limit = request.query_params.get("limit", 10)
        offset = request.query_params.get("offset", 0)
        
        try:
            limit = int(limit)
            offset = int(offset)
        except (ValueError, TypeError):
            return Response(
                {"error": "limit e offset devem ser números inteiros"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if produto_id:
            try:
                produto_id = int(produto_id)
            except (ValueError, TypeError):
                return Response(
                    {"error": "produto_id deve ser um número inteiro"},
                    status=status.HTTP_400_BAD_REQUEST
                )

        if data_inicio:
            try:
                data_inicio = datetime.fromisoformat(data_inicio)
            except ValueError:
                return Response(
                    {"error": "data_inicio inválida (use formato ISO: YYYY-MM-DD)"},
                    status=status.HTTP_400_BAD_REQUEST
                )

        if data_fim:
            try:
                data_fim = datetime.fromisoformat(data_fim)
            except ValueError:
                return Response(
                    {"error": "data_fim inválida (use formato ISO: YYYY-MM-DD)"},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Obter movimentações com filtros
        movimentacoes = listar_movimentacoes(
            produto_id=produto_id,
            data_inicio=data_inicio,
            data_fim=data_fim,
        )

        # Total antes da paginação
        total = movimentacoes.count()
        
        # Aplicar paginação
        movimentacoes_paginadas = movimentacoes[offset:offset + limit]

        # Verificar se há próxima página
        tem_proxima = (offset + limit) < total

        serializer = MovimentacaoListSerializer(movimentacoes_paginadas, many=True)
        
        return Response({
            "meta": {
                "total": total,
                "limit": limit,
                "offset": offset,
                "tem_proxima": tem_proxima,
            },
            "data": serializer.data
        })
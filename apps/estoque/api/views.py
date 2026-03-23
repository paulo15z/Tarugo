from django.shortcuts import render

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
        produto_id = request.query_params.get("produto_id")
        data_inicio = request.query_params.get("data_inicio")
        data_fim = request.query_params.get("data_fim")

        if produto_id:
            produto_id = int(produto_id)

        from datetime import datetime #parece loucura, e é, em breve relogio pro sistema

        if data_inicio:
            data_inicio = datetime.fromisoformat(data_inicio)

        if data_fim:
            data_fim = datetime.fromisoformat(data_fim)

        movimentacoes = listar_movimentacoes(
            produto_id=produto_id,
            data_inicio=data_inicio,
            data_fim=data_fim,
        )

        serializer = MovimentacaoListSerializer(movimentacoes, many=True)
        return Response(serializer.data)
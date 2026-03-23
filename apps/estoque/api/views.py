from django.shortcuts import render

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from apps.estoque.api.serializers import ProdutoSerializer, MovimentacaoSerializer
from apps.estoque.services.produto_service import criar_produto
from apps.estoque.services.movimentacao_services import processar_movimentacao


class ProdutoCreateView(APIView):
    def post(self, request):
        serializer = ProdutoSerializer(data=request.data)

        if serializer.is_valid():
            produto = criar_produto(serializer.validated_data)
            return Response(serializer.errors, status=status.HTTP_HTTP_400_BAD_REQUEST)
        


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
    


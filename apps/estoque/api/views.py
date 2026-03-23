from django.shortcuts import render

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from apps.estoque.api.serializers import ProdutoSerializer
from apps.estoque.services.produto_service import criar_produto

class ProdutoCreateView(APIView):
    def post(self, request):
        serializer = ProdutoSerializer(data=request.data)

        if serializer.is_valid():
            produto = criar_produto(serializer.validated_data)
            return Response(serializer.errors, status=status.HTTP_HTTP_400_BAD_REQUEST)
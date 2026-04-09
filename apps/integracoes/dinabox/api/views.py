from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from ..importer import importar_projeto
from .serializers import ProjetoCompletoSerializer


@api_view(['POST'])
def importar_projeto_api(request):
    """
    API para importar um projeto do Dinabox.
    Espera csv_corte e html_compras no body.
    """
    csv_corte = request.data.get('csv_corte')
    html_compras = request.data.get('html_compras')

    if not csv_corte and not html_compras:
        return Response(
            {"error": "Pelo menos um dos arquivos (csv_corte ou html_compras) deve ser fornecido."},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        projeto_completo = importar_projeto(csv_corte=csv_corte, html_compras=html_compras)
        serializer = ProjetoCompletoSerializer(projeto_completo)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {"error": f"Erro ao importar projeto: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def projeto_modulos_pecas(request, projeto_id):
    """
    API para visualizar módulos e peças de um projeto.
    Por enquanto, simula com dados de exemplo.
    """
    # TODO: implementar busca real do projeto
    # Por enquanto, retorna estrutura vazia
    data = {
        "projeto": {"id": projeto_id, "nome": "Projeto Exemplo"},
        "cliente": {"nome": "Cliente Exemplo"},
        "pecas": [],
        "modulos": [],
        "insumos": [],
        "chapas": [],
        "metadata": {"origem": "dinabox", "data_importacao": "2024-01-01T00:00:00", "versao": 1}
    }
    serializer = ProjetoCompletoSerializer(data=data)
    if serializer.is_valid():
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
# apps/pcp/api/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.http import FileResponse

from apps.pcp.services.roteiro_service import (
    processar_arquivo_roteiro_pcp,
    ProcessarRoteiroInput
)
from apps.pcp.models.processamento import ProcessamentoPCP
from apps.pcp.api.serializers import (
    PCPProcessResponseSerializer,
    ProcessamentoPCPSerializer
)
from apps.pcp.selectors.pcp_selectors import get_historico_pcp

class PCPProcessView(APIView):
    parser_classes = [MultiPartParser]

    def post(self, request):
        if 'arquivo' not in request.FILES:
            return Response({'erro': 'Arquivo não enviado'}, status=400)

        uploaded_file = request.FILES['arquivo']

        try:
            result = processar_arquivo_roteiro_pcp(uploaded_file)

            return Response(result)

        except Exception as e:
            return Response({'erro': str(e)}, status=500)
        
        

class PCPDownloadView(APIView):
    """Download do arquivo XLS gerado"""
    def get(self, request, pid):
        proc = get_object_or_404(ProcessamentoPCP, id=pid)

        if not proc.arquivo_saida:
            return Response(
                {'erro': 'Arquivo não encontrado'}, 
                status=status.HTTP_404_NOT_FOUND
            )

        
        response = FileResponse(
            proc.arquivo_saida.open('rb'),
            as_attachment=True,
            filename=f"ROTEIRO_{proc.nome_arquivo}.xls"
        )
        return response


class PCPHistoricoView(APIView):
    """Lista histórico de processamentos"""
    def get(self, request):
        historico = get_historico_pcp()
        serializer = ProcessamentoPCPSerializer(historico, many=True)
        return Response(serializer.data)
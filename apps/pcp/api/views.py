from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.http import FileResponse
from django.conf import settings   # ← ESSA LINHA ESTAVA FALTANDO
import os

from apps.pcp.services.pcp_service import processar_arquivo_dinabox
from apps.pcp.models.processamento import ProcessamentoPCP


class PCPProcessView(APIView):
    parser_classes = [MultiPartParser]

    def post(self, request):
        if 'arquivo' not in request.FILES:
            return Response({'erro': 'Arquivo não enviado'}, status=status.HTTP_400_BAD_REQUEST)

        file = request.FILES['arquivo']

        try:
            df, _, nome_saida, pid = processar_arquivo_dinabox(file)

            ProcessamentoPCP.objects.create(
                id=pid,
                nome_arquivo=file.name,
                total_pecas=len(df),
                arquivo_saida=nome_saida
            )

            cols_previa = ['DESCRIÇÃO DA PEÇA', 'LOCAL', 'PLANO', 'ROTEIRO']
            if 'OBS' in df.columns:
                cols_previa.insert(2, 'OBS')
            previa = df[cols_previa].head(50).to_dict(orient='records')

            resumo = df['ROTEIRO'].value_counts().reset_index()
            resumo.columns = ['roteiro', 'qtd']

            return Response({
                'pid': pid,
                'total': len(df),
                'previa': previa,
                'resumo': resumo.to_dict(orient='records')
            })

        except Exception as e:
            return Response({'erro': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PCPDownloadView(APIView):
    def get(self, request, pid):
        proc = get_object_or_404(ProcessamentoPCP, id=pid)
        caminho = os.path.join(settings.PCP_OUTPUTS_DIR, proc.arquivo_saida)

        if not os.path.exists(caminho):
            return Response({'erro': 'Arquivo não encontrado no servidor'}, status=404)

        return FileResponse(open(caminho, 'rb'), as_attachment=True, filename=f"ROTEIRO_{proc.nome_arquivo}.xls")


class PCPHistoricoView(APIView):
    def get(self, request):
        historico = ProcessamentoPCP.objects.all().order_by('-data')
        data = list(historico.values('id', 'nome_arquivo', 'data', 'total_pecas', 'arquivo_saida'))
        return Response(data)
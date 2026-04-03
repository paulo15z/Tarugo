import csv

from rest_framework.views import APIView
from rest_framework.response import Response

from .services.importador_service import importar_csv


class ImportarCSVView(APIView):

    def post(self, request):

        file = request.FILES.get("file")

        if not file:
            return Response(
                {"sucesso": False, "erro": "Arquivo não enviado"},
                status=400
            )

        try:
            linhas = self._csv_to_json(file)

            result = importar_csv({"linhas": linhas})

            if result["sucesso"]:
                return Response(result, status=200)

            return Response(result, status=400)

        except Exception:
            return Response(
                {"sucesso": False, "erro": "Erro ao processar CSV"},
                status=400
            )

    def _csv_to_json(self, file):

        decoded = file.read().decode("utf-8").splitlines()
        reader = csv.DictReader(decoded)

        linhas = []

        for row in reader:
            linhas.append({
                "pedido": row.get("PEDIDO"),
                "ordem": row.get("ORDEM"),
                "modulo": row.get("MODULO"),
                "id_peca": row.get("ID_PECA"),
                "descricao": row.get("DESCRICAO"),
            })

        return linhas

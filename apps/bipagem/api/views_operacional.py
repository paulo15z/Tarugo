from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.bipagem.api.serializers import (
    EnvioExpedicaoAddModuloSerializer,
    EnvioExpedicaoAddItemSerializer,
    EnvioExpedicaoCreateSerializer,
    EnvioExpedicaoFiltroSerializer,
    EnvioExpedicaoMovimentoSerializer,
    EventoPecaSerializer,
    SeparacaoDestinoSerializer,
)
from apps.bipagem.selectors.operacional_selector import (
    list_auditoria_pecas,
    get_envio_expedicao,
    get_resumo_operacional,
    list_envios_expedicao,
    list_grupos_expedicao,
    list_modulos_preenchimento,
)
from apps.bipagem.services.operacional_service import (
    adicionar_modulo_envio,
    adicionar_item_envio,
    criar_envio_expedicao,
    registrar_evento_peca,
    registrar_entrada_expedicao,
    registrar_saida_expedicao,
    registrar_separacao_destino,
)


class OperacionalResumoLoteView(APIView):
    def get(self, request, pid):
        return Response({
            "resumo": get_resumo_operacional(pid),
            "grupos": list_grupos_expedicao(pid, ambiente=request.query_params.get("ambiente", "").strip()),
            "modulos_preenchimento": list_modulos_preenchimento(pid, ambiente=request.query_params.get("ambiente", "").strip()),
        })


class OperacionalAuditoriaPecasView(APIView):
    def get(self, request, pid):
        return Response(
            list_auditoria_pecas(
                pid,
                ambiente=request.query_params.get("ambiente", "").strip(),
                modulo=request.query_params.get("modulo", "").strip(),
            )
        )


class OperacionalEventoPecaView(APIView):
    def post(self, request):
        serializer = EventoPecaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        resultado = registrar_evento_peca({
            "pid": serializer.validated_data["pid"],
            "codigo_peca": serializer.validated_data["codigo"],
            "etapa": serializer.validated_data["etapa"],
            "quantidade": serializer.validated_data["quantidade"],
            "usuario": serializer.validated_data["usuario"] or "OPERADOR",
            "localizacao": serializer.validated_data["localizacao"] or serializer.validated_data["etapa"],
            "observacao": serializer.validated_data.get("observacao", ""),
        })
        return Response(
            resultado,
            status=status.HTTP_200_OK if resultado.get("sucesso") else status.HTTP_400_BAD_REQUEST,
        )


class SeparacaoDestinoView(APIView):
    def post(self, request):
        serializer = SeparacaoDestinoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        resultado = registrar_separacao_destino({
            "pid": serializer.validated_data["pid"],
            "codigo_peca": serializer.validated_data["codigo"],
            "quantidade": serializer.validated_data["quantidade"],
            "usuario": serializer.validated_data["usuario"] or "OPERADOR",
            "localizacao": serializer.validated_data["localizacao"] or "SEPARACAO_DESTINOS",
        })
        return Response(
            resultado,
            status=status.HTTP_200_OK if resultado.get("sucesso") else status.HTTP_400_BAD_REQUEST,
        )


class EnvioExpedicaoListCreateView(APIView):
    def get(self, request):
        serializer = EnvioExpedicaoFiltroSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        data = list_envios_expedicao(status=serializer.validated_data.get("status", ""))
        return Response(data)

    def post(self, request):
        serializer = EnvioExpedicaoCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        destinos_secundarios = [
            item.strip()
            for item in serializer.validated_data.get("destinos_secundarios", "").split(",")
            if item.strip()
        ]
        payload = dict(serializer.validated_data)
        payload["destinos_secundarios"] = destinos_secundarios
        resultado = criar_envio_expedicao(payload)
        return Response(
            resultado,
            status=status.HTTP_201_CREATED if resultado.get("sucesso") else status.HTTP_400_BAD_REQUEST,
        )


class EnvioExpedicaoDetailView(APIView):
    def get(self, request, codigo):
        envio = get_envio_expedicao(codigo)
        if not envio:
            return Response({"erro": "Envio nao encontrado."}, status=status.HTTP_404_NOT_FOUND)
        return Response(envio)


class EnvioExpedicaoItemView(APIView):
    def post(self, request, codigo):
        serializer = EnvioExpedicaoAddItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        resultado = adicionar_item_envio({
            "envio_codigo": codigo,
            "pid": serializer.validated_data["pid"],
            "codigo_peca": serializer.validated_data["codigo"],
            "quantidade": serializer.validated_data["quantidade"],
            "usuario": serializer.validated_data["usuario"] or "OPERADOR",
        })
        return Response(
            resultado,
            status=status.HTTP_200_OK if resultado.get("sucesso") else status.HTTP_400_BAD_REQUEST,
        )


class EnvioExpedicaoModuloView(APIView):
    def post(self, request, codigo):
        serializer = EnvioExpedicaoAddModuloSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        resultado = adicionar_modulo_envio({
            "envio_codigo": codigo,
            "pid": serializer.validated_data["pid"],
            "codigo_modulo": serializer.validated_data["codigo_modulo"],
            "ambiente": serializer.validated_data.get("ambiente", ""),
            "usuario": serializer.validated_data["usuario"] or "OPERADOR",
        })
        return Response(
            resultado,
            status=status.HTTP_200_OK if resultado.get("sucesso") else status.HTTP_400_BAD_REQUEST,
        )


class EnvioExpedicaoEntradaView(APIView):
    def post(self, request, codigo):
        serializer = EnvioExpedicaoMovimentoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        resultado = registrar_entrada_expedicao({
            "envio_codigo": codigo,
            "usuario": serializer.validated_data["usuario"] or "OPERADOR",
            "localizacao": serializer.validated_data["localizacao"] or "EXPEDICAO",
            "observacao": serializer.validated_data.get("observacao", ""),
        })
        return Response(
            resultado,
            status=status.HTTP_200_OK if resultado.get("sucesso") else status.HTTP_400_BAD_REQUEST,
        )


class EnvioExpedicaoSaidaView(APIView):
    def post(self, request, codigo):
        serializer = EnvioExpedicaoMovimentoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        resultado = registrar_saida_expedicao({
            "envio_codigo": codigo,
            "usuario": serializer.validated_data["usuario"] or "OPERADOR",
            "localizacao": serializer.validated_data["localizacao"] or "EXPEDICAO",
            "observacao": serializer.validated_data.get("observacao", ""),
        })
        return Response(
            resultado,
            status=status.HTTP_200_OK if resultado.get("sucesso") else status.HTTP_400_BAD_REQUEST,
        )

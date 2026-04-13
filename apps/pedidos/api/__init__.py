"""
API Views para o app pedidos.

Responsabilidade: Camada HTTP apenas (DRF).
Padrão: Validação via Pydantic → Service → Mapper → Response.
"""

from rest_framework import status, viewsets
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from apps.pedidos.models import Pedido, AmbientePedido
from apps.pedidos.services import PedidoService
from apps.pedidos.selectors import PedidoSelector, AmbienteSelector, HistoricoStatusSelector
from apps.pedidos.schemas import (
    PedidoInputSchema,
    AtualizarStatusSchema,
    AmbientePedidoInputSchema,
    DadosEngenhariaSchema,
)
from apps.pedidos.mappers import (
    PedidoMapper,
    AmbienteMapper,
    HistoricoStatusMapper,
)


@api_view(["GET", "POST"])
def pedido_list(request):
    """
    GET: Lista pedidos (com filtros opcionais).
    POST: Cria novo pedido.
    """
    if request.method == "GET":
        # Filtros opcionais
        status_filtro = request.query_params.get("status")
        customer_id = request.query_params.get("customer_id")
        search = request.query_params.get("search")

        if search:
            queryset = PedidoSelector.search_pedidos(search)
        elif customer_id:
            queryset = PedidoSelector.list_pedidos_por_cliente(customer_id)
        elif status_filtro:
            queryset = PedidoSelector.list_pedidos_por_status(status_filtro)
        else:
            queryset = PedidoSelector.list_pedidos_ativos()

        # Paginação básica
        limit = int(request.query_params.get("limit", 20))
        offset = int(request.query_params.get("offset", 0))
        queryset = queryset[offset : offset + limit]

        schemas = PedidoMapper.models_to_output_schemas(queryset)
        return Response(
            {"count": len(schemas), "results": [s.model_dump() for s in schemas]},
            status=status.HTTP_200_OK,
        )

    # POST: Criar novo pedido
    try:
        input_schema = PedidoInputSchema(**request.data)
    except Exception as e:
        return Response(
            {"detail": str(e)},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # TODO: Buscar cliente_comercial pelo customer_id e criar via service
    # Por enquanto, apenas validação de dados

    return Response(
        {
            "detail": "Criação de pedido requer integração com ClienteComercial.",
        },
        status=status.HTTP_501_NOT_IMPLEMENTED,
    )


@api_view(["GET", "PATCH"])
def pedido_detail(request, numero_pedido):
    """
    GET: Retorna detalhes completos de um pedido.
    PATCH: Atualiza informações do pedido.
    """
    pedido = PedidoSelector.get_pedido_completo(numero_pedido)
    if not pedido:
        return Response(
            {"detail": f"Pedido {numero_pedido} não encontrado."},
            status=status.HTTP_404_NOT_FOUND,
        )

    if request.method == "GET":
        schema = PedidoMapper.model_to_detalhe_schema(pedido)
        return Response(schema.model_dump(), status=status.HTTP_200_OK)

    # PATCH: Atualizar informações básicas
    if "data_entrega_prevista" in request.data:
        pedido.data_entrega_prevista = request.data["data_entrega_prevista"]
    if "observacoes" in request.data:
        pedido.observacoes = request.data["observacoes"]

    pedido.save()
    schema = PedidoMapper.model_to_output_schema(pedido)
    return Response(schema.model_dump(), status=status.HTTP_200_OK)


@api_view(["POST"])
def pedido_atualizar_status(request, numero_pedido):
    """
    Atualiza o status de um pedido.
    
    Body: {"novo_status": "EM_PRODUCAO", "motivo": "..."}
    """
    pedido = get_object_or_404(Pedido, numero_pedido=numero_pedido)

    try:
        input_schema = AtualizarStatusSchema(**request.data)
    except Exception as e:
        return Response(
            {"detail": str(e)},
            status=status.HTTP_400_BAD_REQUEST,
        )

    usuario = request.user if request.user.is_authenticated else None

    pedido = PedidoService.atualizar_status_pedido(
        pedido,
        input_schema.novo_status,
        input_schema.motivo or "",
        usuario,
    )

    schema = PedidoMapper.model_to_output_schema(pedido)
    return Response(schema.model_dump(), status=status.HTTP_200_OK)


@api_view(["GET"])
def pedido_historico_status(request, numero_pedido):
    """
    Retorna histórico de transições de status de um pedido.
    """
    pedido = get_object_or_404(Pedido, numero_pedido=numero_pedido)

    historicos = HistoricoStatusSelector.list_historico_pedido(numero_pedido)
    schemas = HistoricoStatusMapper.models_to_output_schemas(historicos)

    return Response(
        {"pedido": numero_pedido, "historico": [s.model_dump() for s in schemas]},
        status=status.HTTP_200_OK,
    )


@api_view(["GET"])
def ambiente_list(request):
    """
    Lista ambientes com filtros opcionais.
    """
    status_filtro = request.query_params.get("status")
    pedido_numero = request.query_params.get("pedido_numero")
    search = request.query_params.get("search")

    if search:
        queryset = AmbienteSelector.search_ambientes(search)
    elif pedido_numero:
        queryset = AmbienteSelector.list_ambientes_por_pedido(pedido_numero)
    elif status_filtro:
        queryset = AmbienteSelector.list_ambientes_por_status(status_filtro)
    else:
        queryset = AmbientePedido.objects.all().select_related("pedido")

    limit = int(request.query_params.get("limit", 20))
    offset = int(request.query_params.get("offset", 0))
    queryset = queryset[offset : offset + limit]

    schemas = AmbienteMapper.models_to_output_schemas(queryset)
    return Response(
        {"count": len(schemas), "results": [s.model_dump() for s in schemas]},
        status=status.HTTP_200_OK,
    )


@api_view(["GET"])
def ambiente_detail(request, pk):
    """
    Retorna detalhes de um ambiente.
    """
    ambiente = AmbienteSelector.get_ambiente_completo(pk)
    if not ambiente:
        return Response(
            {"detail": f"Ambiente {pk} não encontrado."},
            status=status.HTTP_404_NOT_FOUND,
        )

    schema = AmbienteMapper.model_to_output_schema(ambiente)
    return Response(schema.model_dump(), status=status.HTTP_200_OK)


@api_view(["POST"])
def ambiente_processar_engenharia(request, pk):
    """
    Processa dados de engenharia para um ambiente (via Dinabox API).
    
    Body: {"dimensoes": "...", "furacoes": [...], ...}
    """
    ambiente = get_object_or_404(AmbientePedido, pk=pk)

    try:
        dados_eng = DadosEngenhariaSchema(**request.data)
    except Exception as e:
        return Response(
            {"detail": str(e)},
            status=status.HTTP_400_BAD_REQUEST,
        )

    usuario = request.user if request.user.is_authenticated else None

    ambiente = PedidoService.processar_engenharia_ambiente(
        ambiente,
        dados_eng.model_dump(),
        usuario,
    )

    schema = AmbienteMapper.model_to_output_schema(ambiente)
    return Response(schema.model_dump(), status=status.HTTP_200_OK)

"""
Domain - Status do Pedido e Ambiente.

Define os status válidos para o ciclo de vida de pedidos e ambientes.
Enums puros, sem lógica de negócio aqui.
"""

from django.db import models


class PedidoStatus(models.TextChoices):
    """Status do Pedido no ciclo de vida completo."""

    CONTRATO_FECHADO = "CONTRATO_FECHADO", "Contrato Fechado"
    ENVIADO_PARA_PROJETOS = "ENVIADO_PARA_PROJETOS", "Enviado para Projetos"
    EM_ENGENHARIA = "EM_ENGENHARIA", "Em Engenharia"
    EM_PRODUCAO = "EM_PRODUCAO", "Em Produção"
    EXPEDICAO = "EXPEDICAO", "Expedição"
    MONTAGEM = "MONTAGEM", "Montagem"
    CONCLUIDO = "CONCLUIDO", "Concluído"
    CANCELADO = "CANCELADO", "Cancelado"


class AmbienteStatus(models.TextChoices):
    """Status do Ambiente (sub-unidade de produção dentro de um Pedido)."""

    PENDENTE = "PENDENTE", "Pendente"
    PENDENTE_PROJETOS = "PENDENTE_PROJETOS", "Pendente Projetos"
    EM_ENGENHARIA = "EM_ENGENHARIA", "Em Engenharia"
    AGUARDANDO_PCP = "AGUARDANDO_PCP", "Aguardando PCP"
    EM_INDUSTRIA = "EM_INDUSTRIA", "Em Indústria"
    EM_MONTAGEM = "EM_MONTAGEM", "Em Montagem"
    CONCLUIDO = "CONCLUIDO", "Concluído"

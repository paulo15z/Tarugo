"""
Schemas Pydantic para o app pedidos.

Responsabilidade: Validação de dados de entrada/saída.
Padrão: Toda validação de negócio aqui.
"""

from pydantic import BaseModel, Field, field_validator
from datetime import datetime, date
from typing import Optional, List, Any
from enum import Enum


class PedidoStatusEnum(str, Enum):
    """Enum de status de pedido para validation."""

    CONTRATO_FECHADO = "CONTRATO_FECHADO"
    ENVIADO_PARA_PROJETOS = "ENVIADO_PARA_PROJETOS"
    EM_ENGENHARIA = "EM_ENGENHARIA"
    EM_PRODUCAO = "EM_PRODUCAO"
    EXPEDICAO = "EXPEDICAO"
    MONTAGEM = "MONTAGEM"
    CONCLUIDO = "CONCLUIDO"
    CANCELADO = "CANCELADO"


class AmbienteStatusEnum(str, Enum):
    """Enum de status de ambiente para validation."""

    PENDENTE = "PENDENTE"
    PENDENTE_PROJETOS = "PENDENTE_PROJETOS"
    EM_ENGENHARIA = "EM_ENGENHARIA"
    AGUARDANDO_PCP = "AGUARDANDO_PCP"
    EM_INDUSTRIA = "EM_INDUSTRIA"
    EM_MONTAGEM = "EM_MONTAGEM"
    CONCLUIDO = "CONCLUIDO"


class AmbienteOrcamentoBaseSchema(BaseModel):
    """Base com campos comuns de ambiente."""

    nome_ambiente: str = Field(..., min_length=1, max_length=255)
    descricao: Optional[str] = None
    acabamentos: List[str] = Field(default_factory=list)
    eletrodomesticos: List[str] = Field(default_factory=list)
    observacoes_especiais: Optional[str] = None


class AmbientePedidoInputSchema(AmbienteOrcamentoBaseSchema):
    """Input para criar/atualizar um Ambiente de Pedido."""

    pass


class AmbientePedidoOutputSchema(AmbienteOrcamentoBaseSchema):
    """Output serializado de um Ambiente de Pedido."""

    id: int
    status: AmbienteStatusEnum
    dados_engenharia: dict = Field(default_factory=dict)
    metricas_pcp_resumo: dict = Field(default_factory=dict)
    dados_operacionais_resumo: dict = Field(default_factory=dict)
    data_criacao: datetime
    data_atualizacao: datetime

    class Config:
        from_attributes = True


class PedidoInputSchema(BaseModel):
    """Input para criar um Pedido."""

    numero_pedido: str = Field(..., min_length=1, max_length=50)
    cliente_nome: str = Field(..., min_length=1, max_length=255)
    customer_id: str = Field(..., min_length=1, max_length=64)
    data_contrato: Optional[date] = None
    data_entrega_prevista: Optional[date] = None
    observacoes: Optional[str] = None


class PedidoOutputSchema(BaseModel):
    """Output serializado de um Pedido."""

    id: int
    numero_pedido: str
    customer_id: str
    cliente_nome: str
    status: PedidoStatusEnum
    data_criacao: datetime
    data_contrato: Optional[date] = None
    data_entrega_prevista: Optional[date] = None
    data_conclusao: Optional[datetime] = None
    observacoes: str
    percentual_conclusao: float

    class Config:
        from_attributes = True


class PedidoDetalheSchema(PedidoOutputSchema):
    """Output detalhado de um Pedido com ambientes."""

    ambientes: List[AmbientePedidoOutputSchema] = Field(default_factory=list)


class AtualizarStatusSchema(BaseModel):
    """Input para atualizar status de um Pedido."""

    novo_status: PedidoStatusEnum
    motivo: Optional[str] = None

    @field_validator("novo_status", mode="before")
    @classmethod
    def validate_status(cls, v):
        if isinstance(v, str):
            v = v.upper()
        return v


class HistoricoStatusOutputSchema(BaseModel):
    """Output de uma transição de status."""

    pedido_numero: str
    status_anterior: str
    status_novo: str
    motivo: str
    usuario: Optional[str] = None
    data_criacao: datetime

    class Config:
        from_attributes = True


class DadosEngenhariaSchema(BaseModel):
    """Schema para dados de engenharia (Dinabox)."""

    dimensoes: Optional[str] = None
    furacoes: List[dict] = Field(default_factory=list)
    usinagens: List[dict] = Field(default_factory=list)
    observacoes_tecnicas: Optional[str] = None


class MetricasPCPSchema(BaseModel):
    """Schema para métricas resumidas do PCP."""

    total_pecas_pcp: int = Field(default=0, ge=0)
    pecas_corte_estimado: int = Field(default=0, ge=0)
    pecas_montagem_estimado: int = Field(default=0, ge=0)
    tempo_producao_estimado_horas: float = Field(default=0.0, ge=0.0)
    data_inicio_producao: Optional[date] = None


class DadosOperacionaisSchema(BaseModel):
    """Schema para dados operacionais (bipagem, expedição)."""

    pecas_bipadas: int = Field(default=0, ge=0)
    pecas_expedidas: int = Field(default=0, ge=0)
    ult_bipagem_at: Optional[datetime] = None
    observacoes_operacionais: Optional[str] = None


class SearchPedidosSchema(BaseModel):
    """Input para busca de pedidos."""

    query: str = Field(..., min_length=1, max_length=255)
    status_filtro: Optional[List[PedidoStatusEnum]] = None
    limit: int = Field(default=20, ge=1, le=100)

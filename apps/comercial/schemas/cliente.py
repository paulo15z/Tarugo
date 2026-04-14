from __future__ import annotations

from decimal import Decimal
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, field_validator


class ClienteComercialCriarDinaboxSchema(BaseModel):
    """Parâmetros enviados à Dinabox na criação (PUT /api/v1/customer)."""

    customer_name: str = Field(..., min_length=1, max_length=255)
    customer_type: Literal["pf", "pj"] = "pf"
    customer_status: Literal["on", "off"] = "on"
    customer_emails: Optional[str] = None
    customer_phones: Optional[str] = None
    customer_note: Optional[str] = None
    customer_cpf: Optional[str] = None
    customer_cnpj: Optional[str] = None

    @field_validator("customer_emails", "customer_phones", "customer_note", mode="before")
    @classmethod
    def empty_as_none(cls, v):
        if v is None:
            return None
        s = str(v).strip()
        return s or None


class ClienteComercialAtualizarDinaboxSchema(BaseModel):
    customer_id: str = Field(..., min_length=1, max_length=64)
    customer_name: str = Field(..., min_length=1, max_length=255)
    customer_type: Literal["pf", "pj"] = "pf"
    customer_status: Literal["on", "off"] = "on"
    customer_emails: Optional[str] = None
    customer_phones: Optional[str] = None
    customer_note: Optional[str] = None
    customer_cpf: Optional[str] = None
    customer_cnpj: Optional[str] = None

    @field_validator("customer_emails", "customer_phones", "customer_note", mode="before")
    @classmethod
    def empty_as_none(cls, v):
        if v is None:
            return None
        s = str(v).strip()
        return s or None


class ClienteComercialNumeroPedidoSchema(BaseModel):
    numero_pedido: Optional[str] = Field(default=None, max_length=50)

    @field_validator("numero_pedido", mode="before")
    @classmethod
    def strip_numero(cls, v):
        if v is None:
            return None
        s = str(v).strip()
        return s or None


class AmbienteOrcamentoInputSchema(BaseModel):
    nome_ambiente: str = Field(..., min_length=1, max_length=200)
    valor_orcado: Optional[Decimal] = None

    @field_validator("nome_ambiente", mode="before")
    @classmethod
    def strip_nome(cls, v):
        return str(v).strip() if v is not None else v


class AmbienteDetalhesInputSchema(BaseModel):
    """Detalhes simplificados de um ambiente para o comercial registrar."""
    
    acabamentos: list[str] = Field(default_factory=list, description="Lista de acabamentos")
    eletrodomesticos: list[str] = Field(default_factory=list, description="Lista de eletrodomésticos")
    observacoes_especiais: str = Field(default="", description="Observações para Engenharia/Projetos")
    
    @field_validator("acabamentos", "eletrodomesticos", mode="before")
    @classmethod
    def validate_list(cls, v):
        if isinstance(v, str):
            return [item.strip() for item in v.split(",") if item.strip()]
        if isinstance(v, list):
            return [str(item).strip() for item in v if item]
        return []
    
    @field_validator("observacoes_especiais", mode="before")
    @classmethod
    def strip_obs(cls, v):
        return str(v).strip() if v else ""


class AmbienteOrcamentoAtualizarSchema(BaseModel):
    """Atualizar ambiente com todos os detalhes."""
    
    nome_ambiente: Optional[str] = None
    valor_orcado: Optional[Decimal] = None
    acabamentos: Optional[list[str]] = None
    eletrodomesticos: Optional[list[str]] = None
    observacoes_especiais: Optional[str] = None
    
    @field_validator("nome_ambiente", mode="before")
    @classmethod
    def strip_nome(cls, v):
        if v is None:
            return v
        return str(v).strip() or None
    
    @field_validator("acabamentos", "eletrodomesticos", mode="before")
    @classmethod
    def validate_list(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            return [item.strip() for item in v.split(",") if item.strip()]
        if isinstance(v, list):
            return [str(item).strip() for item in v if item]
        return None
    
    @field_validator("observacoes_especiais", mode="before")
    @classmethod
    def strip_obs(cls, v):
        if v is None:
            return None
        s = str(v).strip()
        return s or None


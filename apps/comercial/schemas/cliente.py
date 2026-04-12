from __future__ import annotations

from decimal import Decimal
from typing import Literal, Optional

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


class AmbienteOrcamentoInputSchema(BaseModel):
    nome_ambiente: str = Field(..., min_length=1, max_length=200)
    valor_orcado: Optional[Decimal] = None

    @field_validator("nome_ambiente", mode="before")
    @classmethod
    def strip_nome(cls, v):
        return str(v).strip() if v is not None else v

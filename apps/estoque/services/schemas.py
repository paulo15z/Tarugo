from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, field_validator

TIPOS_VALIDOS = ['entrada', 'saida', 'ajuste', 'transferencia']


class MovimentacaoSchema(BaseModel):
    produto_id: int
    quantidade: Decimal
    tipo: str
    usuario_id: Optional[int] = None
    observacao: Optional[str] = None
    espessura: Optional[int] = None

    @field_validator('tipo')
    def validar_tipo(cls, v):
        if v not in TIPOS_VALIDOS:
            raise ValueError(f'Tipo inválido. Use: {", ".join(TIPOS_VALIDOS)}')
        return v

    @field_validator('quantidade')
    def validar_quantidade(cls, v):
        if v <= 0:
            raise ValueError('Quantidade deve ser positiva.')
        return v


class AjusteLoteSchema(BaseModel):
    """Schema para ajuste de múltiplos produtos de uma vez."""
    movimentacoes: list[MovimentacaoSchema]

    @field_validator('movimentacoes')
    def validar_lista(cls, v):
        if not v:
            raise ValueError('A lista de movimentações não pode estar vazia.')
        return v


class ReservaCreateSchema(BaseModel):
    produto_id: int
    pedido_id: int
    quantidade: Decimal
    espessura: Optional[int] = None
    observacao: Optional[str] = None

    @field_validator('quantidade')
    def validar_quantidade(cls, v):
        if v <= 0:
            raise ValueError('Quantidade da reserva deve ser positiva.')
        return v

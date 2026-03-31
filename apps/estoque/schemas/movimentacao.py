# apps/estoque/schemas/movimentacao.py
from pydantic import BaseModel, field_validator, ConfigDict
from apps.estoque.domain.tipos import TipoMovimentacao


class MovimentacaoCreateSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    produto_id: int
    tipo: TipoMovimentacao
    quantidade: int
    observacao: str | None = None

    @field_validator("quantidade")
    @classmethod
    def quantidade_positiva(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Quantidade deve ser maior que zero")
        return v
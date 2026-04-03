from pydantic import BaseModel, Field
from typing import Optional

# pydantic eh do caralho

class BipagemInput(BaseModel):
    codigo_peca: str = Field(..., min_length=1)
    usuario: Optional[str] = None
    localizacao: str = Field(..., min_length=1)


class PecaOutput(BaseModel):
    id: str
    descricao: str
    status: str
    destino: Optional[str] = None
    pedido_id: Optional[int] = None


class BipagemOutput(BaseModel):
    sucesso: bool
    mensagem: Optional[str] = None
    erro: Optional[str] = None
    repetido: bool = False
    peca: Optional[PecaOutput] = None

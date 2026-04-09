from pydantic import BaseModel
from typing import List, Optional
from .peca import Peca


class Modulo(BaseModel):
    """Módulo do projeto Dinabox"""
    nome: str
    pecas: List[Peca] = []
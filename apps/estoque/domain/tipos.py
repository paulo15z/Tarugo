from enum import Enum


class TipoMovimentacao(str, Enum):
    """Tipos permitidos no MVP (IA_CONTEXT.md)"""
    ENTRADA = "entrada"
    SAIDA = "saida"
    AJUSTE = "ajuste"

    @classmethod
    def choices(cls):
        return [(member.value, member.value.capitalize()) for member in cls]
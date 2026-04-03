from enum import Enum

class StatusPeca(str, Enum):
    PENDENTE = 'PENDENTE'
    BIPADA = 'BIPADA'
    CONCLUIDA = 'CONCLUIDA'
    CANCELADA = 'CANCELADA'

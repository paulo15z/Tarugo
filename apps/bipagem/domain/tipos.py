from enum import Enum

class StatusPeca(str, Enum):
    PENDENTE = 'PENDENTE'
    BIPADA = 'BIPADA'
    CONCLUIDA = 'CONCLUIDA'
    CANCELADA = 'CANCELADA'

MAPA_SETORES = {
    '01': {'nome': 'PINTURA', 'cor': '#9c27b0'},
    '02': {'nome': 'LÂMINAS/FOLHAS', 'cor': '#795548'},
    '04': {'nome': 'MONTAGEM DE CAIXA', 'cor': '#2196f3'},
    '05': {'nome': 'DUPLAGEM', 'cor': '#ff9800'},
    '06': {'nome': 'PORTAS/FRENTES', 'cor': '#e91e63'},
    '10': {'nome': 'PRÉ-MONTAGEM', 'cor': '#00bcd4'},
    '11': {'nome': 'GERAL / OUTROS', 'cor': '#607d8b'},
}

def get_nome_setor(codigo_plano: str) -> str:
    return MAPA_SETORES.get(codigo_plano, {}).get('nome', f'SETOR {codigo_plano}' if codigo_plano else 'NÃO DEFINIDO')

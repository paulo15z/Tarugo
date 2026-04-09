from enum import Enum


class EtapaOperacional(str, Enum):
    RECEBIMENTO_ITEM = "RECEBIMENTO_ITEM"
    SEPARACAO_RESERVA = "SEPARACAO_RESERVA"
    CORTE = "CORTE"
    BORDA = "BORDA"
    USINAGEM = "USINAGEM"
    FURACAO = "FURACAO"
    SEPARACAO_DESTINOS = "SEPARACAO_DESTINOS"
    DUP = "DUP"
    MCX = "MCX"
    MPE = "MPE"
    MAR = "MAR"
    MEL = "MEL"
    XMAR = "XMAR"
    XBOR = "XBOR"
    CQL = "CQL"
    EXPEDICAO = "EXPEDICAO"

    @classmethod
    def choices(cls) -> list[tuple[str, str]]:
        return [(item.value, item.label) for item in cls]

    @property
    def label(self) -> str:
        return {
            self.RECEBIMENTO_ITEM: "Recebimento do Item",
            self.SEPARACAO_RESERVA: "Separacao para Reserva",
            self.CORTE: "Corte",
            self.BORDA: "Bordo",
            self.USINAGEM: "Usinagem",
            self.FURACAO: "Furacao",
            self.SEPARACAO_DESTINOS: "Separacao de Destinos",
            self.DUP: "Duplagem",
            self.MCX: "Montagem de Caixa",
            self.MPE: "Montagem de Perfis",
            self.MAR: "Marcenaria",
            self.MEL: "Montagem Eletrica",
            self.XMAR: "Marcenaria Especial",
            self.XBOR: "Borda Manual",
            self.CQL: "Qualidade",
            self.EXPEDICAO: "Expedicao",
        }[self]


class MovimentoOperacional(str, Enum):
    BIPAGEM = "BIPAGEM"
    ENTRADA = "ENTRADA"
    SAIDA = "SAIDA"
    ESTORNO = "ESTORNO"

    @classmethod
    def choices(cls) -> list[tuple[str, str]]:
        return [(item.value, item.label) for item in cls]

    @property
    def label(self) -> str:
        return {
            self.BIPAGEM: "Bipagem",
            self.ENTRADA: "Entrada",
            self.SAIDA: "Saida",
            self.ESTORNO: "Estorno",
        }[self]


class EscopoOperacional(str, Enum):
    PECA_PCP = "PECA_PCP"
    MODULO_PCP = "MODULO_PCP"
    MATERIAL_ESTOQUE = "MATERIAL_ESTOQUE"

    @classmethod
    def choices(cls) -> list[tuple[str, str]]:
        return [(item.value, item.label) for item in cls]

    @property
    def label(self) -> str:
        return {
            self.PECA_PCP: "Peca PCP",
            self.MODULO_PCP: "Modulo PCP",
            self.MATERIAL_ESTOQUE: "Material de Estoque",
        }[self]


class StatusEnvioExpedicao(str, Enum):
    ABERTO = "ABERTO"
    RECEBIDO = "RECEBIDO"
    LIBERADO = "LIBERADO"

    @classmethod
    def choices(cls) -> list[tuple[str, str]]:
        return [(item.value, item.label) for item in cls]

    @property
    def label(self) -> str:
        return {
            self.ABERTO: "Aberto",
            self.RECEBIDO: "Recebido na Expedicao",
            self.LIBERADO: "Liberado",
        }[self]


ROTEIRO_TO_ETAPA: dict[str, EtapaOperacional] = {
    "COR": EtapaOperacional.CORTE,
    "BOR": EtapaOperacional.BORDA,
    "USI": EtapaOperacional.USINAGEM,
    "FUR": EtapaOperacional.FURACAO,
    "DUP": EtapaOperacional.DUP,
    "MCX": EtapaOperacional.MCX,
    "MPE": EtapaOperacional.MPE,
    "MAR": EtapaOperacional.MAR,
    "MEL": EtapaOperacional.MEL,
    "XMAR": EtapaOperacional.XMAR,
    "XBOR": EtapaOperacional.XBOR,
    "CQL": EtapaOperacional.CQL,
    "EXP": EtapaOperacional.EXPEDICAO,
}

ETAPAS_PREENCHIMENTO_MODULO = {
    EtapaOperacional.DUP,
    EtapaOperacional.MCX,
    EtapaOperacional.MPE,
    EtapaOperacional.MAR,
    EtapaOperacional.MEL,
    EtapaOperacional.XMAR,
    EtapaOperacional.XBOR,
}

ETAPAS_AUDITAVEIS_PECA = {
    EtapaOperacional.RECEBIMENTO_ITEM,
    EtapaOperacional.SEPARACAO_RESERVA,
    EtapaOperacional.CORTE,
    EtapaOperacional.BORDA,
    EtapaOperacional.USINAGEM,
    EtapaOperacional.FURACAO,
    EtapaOperacional.SEPARACAO_DESTINOS,
    EtapaOperacional.DUP,
    EtapaOperacional.MCX,
    EtapaOperacional.MPE,
    EtapaOperacional.MAR,
    EtapaOperacional.MEL,
    EtapaOperacional.XMAR,
    EtapaOperacional.XBOR,
    EtapaOperacional.CQL,
    EtapaOperacional.EXPEDICAO,
}


def parse_roteiro_operacional(roteiro: str | None) -> list[EtapaOperacional]:
    if not roteiro:
        return []
    etapas: list[EtapaOperacional] = []
    for item in roteiro.split(">"):
        codigo = item.strip()
        etapa = ROTEIRO_TO_ETAPA.get(codigo)
        if etapa and etapa not in etapas:
            etapas.append(etapa)
    return etapas


def is_etapa_preenchimento_modulo(etapa: EtapaOperacional) -> bool:
    return etapa in ETAPAS_PREENCHIMENTO_MODULO

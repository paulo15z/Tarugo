from pydantic import BaseModel, Field

from apps.bipagem.domain.operacional import ETAPAS_AUDITAVEIS_PECA, EtapaOperacional


class SeparacaoDestinoInput(BaseModel):
    pid: str = Field(..., min_length=8, max_length=8)
    codigo_peca: str = Field(..., min_length=1)
    quantidade: int = Field(default=1, ge=1)
    usuario: str = Field(default="OPERADOR")
    localizacao: str = Field(default="SEPARACAO_DESTINOS")


class EnvioExpedicaoCreateInput(BaseModel):
    codigo: str | None = Field(default=None, min_length=4, max_length=30)
    descricao: str = Field(default="", max_length=255)
    transportadora: str = Field(default="", max_length=150)
    placa_veiculo: str = Field(default="", max_length=20)
    motorista: str = Field(default="", max_length=150)
    ajudante: str = Field(default="", max_length=150)
    destino_principal: str = Field(default="", max_length=255)
    destinos_secundarios: list[str] = Field(default_factory=list)
    observacoes: str = Field(default="")
    usuario: str = Field(default="SISTEMA")


class EnvioExpedicaoAddItemInput(BaseModel):
    envio_codigo: str = Field(..., min_length=4, max_length=30)
    pid: str = Field(..., min_length=8, max_length=8)
    codigo_peca: str = Field(..., min_length=1)
    quantidade: int = Field(default=1, ge=1)
    usuario: str = Field(default="OPERADOR")


class EnvioExpedicaoAddModuloInput(BaseModel):
    envio_codigo: str = Field(..., min_length=4, max_length=30)
    pid: str = Field(..., min_length=8, max_length=8)
    codigo_modulo: str = Field(..., min_length=1, max_length=50)
    ambiente: str = Field(default="")
    usuario: str = Field(default="OPERADOR")


class EnvioExpedicaoMovimentoInput(BaseModel):
    envio_codigo: str = Field(..., min_length=4, max_length=30)
    usuario: str = Field(default="OPERADOR")
    localizacao: str = Field(default="EXPEDICAO")
    observacao: str = Field(default="")


class EtapaOperacionalStatusInput(BaseModel):
    etapa: EtapaOperacional


class EventoPecaInput(BaseModel):
    pid: str = Field(..., min_length=8, max_length=8)
    codigo_peca: str = Field(..., min_length=1)
    etapa: EtapaOperacional
    quantidade: int = Field(default=1, ge=1)
    usuario: str = Field(default="OPERADOR")
    localizacao: str = Field(default="")
    observacao: str = Field(default="")

    @property
    def etapa_auditavel(self) -> bool:
        return self.etapa in ETAPAS_AUDITAVEIS_PECA

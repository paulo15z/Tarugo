from pydantic import BaseModel, field_validator
# fã numero 1 de pydantic

class MovimentacaoSchema(BaseModel):
    produto_id: int
    quantidade: int
    tipo: str
    #como deve ser
    
    @field_validator('tipo')
    def validar_tipo(cls, v):
        if v not in ['entrada', 'saida']:
            raise ValueError('Tipo inválido!!!')
        return v
    # garante o tipo

    @field_validator('quantidade')
    def validar_quantidade(cls, v):
        if v <= 0:
            raise ValueError('Quantidade deve ser positiva!!!')
        return v
    

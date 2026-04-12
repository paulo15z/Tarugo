# apps/pcp/schemas/processamento.py
"""
Schemas Pydantic para Processamento PCP 2.0.

Responsabilidade: Validação e tipagem de dados de entrada/saída.
Padrão: Pydantic v2, com validação de negócio.
"""

from typing import List, Optional, Dict, Any
from decimal import Decimal
from pydantic import BaseModel, Field, validator


class RoteiroSchema(BaseModel):
    """Schema para um roteiro de fabricação."""
    
    peca_codigo: str = Field(..., description="Código da peça")
    sequencia: List[str] = Field(default_factory=list, description="Sequência de etapas")
    tempo_estimado_minutos: int = Field(default=0, description="Tempo estimado")
    observacoes: str = Field(default="", description="Observações")
    
    class Config:
        json_schema_extra = {
            "example": {
                "peca_codigo": "P6246017",
                "sequencia": ["COR", "BOR", "FUR", "EXP"],
                "tempo_estimado_minutos": 45,
                "observacoes": "Encaminhar para duplagem"
            }
        }


class RipaSchema(BaseModel):
    """Schema para uma ripa."""
    
    material_name: str = Field(..., description="Nome do material")
    material_id: Optional[str] = Field(None, description="ID do material Dinabox")
    espessura_mm: Decimal = Field(..., description="Espessura em mm")
    comprimento_mm: Decimal = Field(..., description="Comprimento em mm")
    largura_mm: Decimal = Field(..., description="Largura em mm")
    quantidade: int = Field(default=1, description="Quantidade de ripas")
    origem: str = Field(default="CORTE", description="Origem (CORTE ou FONTE)")
    destino: str = Field(default="PENDENTE", description="Destino")
    observacoes: str = Field(default="", description="Observações")
    
    @property
    def area_m2(self) -> Decimal:
        """Calcula área em m²."""
        return (self.comprimento_mm * self.largura_mm) / Decimal(1_000_000)
    
    class Config:
        json_schema_extra = {
            "example": {
                "material_name": "Carvalho Poro - ARAUCO",
                "material_id": "1773428038",
                "espessura_mm": 30,
                "comprimento_mm": 250,
                "largura_mm": 1769,
                "quantidade": 1,
                "origem": "CORTE",
                "destino": "ESTOQUE"
            }
        }


class PlanoCorteSchema(BaseModel):
    """Schema para um plano de corte."""
    
    codigo_plano: str = Field(..., description="Código do plano (ex: 03, 05)")
    numero_sequencial: int = Field(..., description="Número sequencial")
    descricao: str = Field(default="", description="Descrição")
    peca_codigos: List[str] = Field(default_factory=list, description="Códigos das peças")
    total_pecas: int = Field(default=0, description="Total de peças")
    tempo_estimado_minutos: int = Field(default=0, description="Tempo estimado")
    prioridade: int = Field(default=0, description="Prioridade (0-3)")
    observacoes: str = Field(default="", description="Observações")
    
    @property
    def codigo_completo(self) -> str:
        """Código completo (ex: 03-001)."""
        return f"{self.codigo_plano}-{self.numero_sequencial:03d}"
    
    class Config:
        json_schema_extra = {
            "example": {
                "codigo_plano": "03",
                "numero_sequencial": 1,
                "descricao": "Chapas de MDF",
                "peca_codigos": ["P6246017", "P6246016"],
                "total_pecas": 2,
                "tempo_estimado_minutos": 30,
                "prioridade": 1
            }
        }


class CoordenadaUsinagem(BaseModel):
    """Coordenada de uma operação de usinagem."""
    
    x: Decimal = Field(..., description="Coordenada X em mm")
    y: Decimal = Field(..., description="Coordenada Y em mm")
    
    class Config:
        json_schema_extra = {
            "example": {"x": 125, "y": 50}
        }


class UsinagemSchema(BaseModel):
    """Schema para uma operação de usinagem."""
    
    peca_codigo: str = Field(..., description="Código da peça")
    tipo: str = Field(..., description="Tipo (FURO, RASGO, REBAIXO, etc.)")
    face: str = Field(..., description="Face (A-F)")
    coordenada_x: Decimal = Field(..., description="Coordenada X em mm")
    coordenada_y: Decimal = Field(..., description="Coordenada Y em mm")
    diametro_mm: Optional[Decimal] = Field(None, description="Diâmetro em mm")
    profundidade_mm: Optional[Decimal] = Field(None, description="Profundidade em mm")
    largura_mm: Optional[Decimal] = Field(None, description="Largura em mm")
    comprimento_mm: Optional[Decimal] = Field(None, description="Comprimento em mm")
    quantidade: int = Field(default=1, description="Quantidade")
    observacoes: str = Field(default="", description="Observações")
    
    @property
    def descricao_completa(self) -> str:
        """Descrição completa da operação."""
        desc = f"{self.tipo} - Face {self.face}"
        if self.tipo == "FURO" and self.diametro_mm:
            desc += f" Ø{self.diametro_mm}mm"
        return desc
    
    class Config:
        json_schema_extra = {
            "example": {
                "peca_codigo": "P6246017",
                "tipo": "FURO",
                "face": "A",
                "coordenada_x": 125,
                "coordenada_y": 50,
                "diametro_mm": 8,
                "profundidade_mm": 25,
                "quantidade": 1
            }
        }


class ProcessamentoPCPSchema(BaseModel):
    """Schema para resultado completo do processamento PCP."""
    
    lote_id: str = Field(..., description="ID do lote gerado")
    cliente_nome: str = Field(..., description="Nome do cliente")
    projeto_descricao: str = Field(..., description="Descrição do projeto")
    
    roteiros: List[RoteiroSchema] = Field(default_factory=list, description="Roteiros gerados")
    ripas: List[RipaSchema] = Field(default_factory=list, description="Ripas consolidadas")
    planos_corte: List[PlanoCorteSchema] = Field(default_factory=list, description="Planos de corte")
    usinagens: List[UsinagemSchema] = Field(default_factory=list, description="Operações de usinagem")
    
    total_pecas: int = Field(default=0, description="Total de peças")
    total_roteiros: int = Field(default=0, description="Total de roteiros")
    total_ripas: int = Field(default=0, description="Total de ripas")
    total_planos: int = Field(default=0, description="Total de planos")
    total_usinagens: int = Field(default=0, description="Total de usinagens")
    
    tempo_total_estimado_minutos: int = Field(default=0, description="Tempo total estimado")
    
    class Config:
        json_schema_extra = {
            "example": {
                "lote_id": "L20260411001",
                "cliente_nome": "1067 - THIAGO E GABY",
                "projeto_descricao": "COZINHA",
                "roteiros": [],
                "ripas": [],
                "planos_corte": [],
                "usinagens": [],
                "total_pecas": 5,
                "total_roteiros": 5,
                "total_ripas": 2,
                "total_planos": 3,
                "total_usinagens": 12,
                "tempo_total_estimado_minutos": 180
            }
        }


class XMLExportSchema(BaseModel):
    """Schema para exportação XML."""
    
    lote_id: str = Field(..., description="ID do lote")
    cliente_nome: str = Field(..., description="Nome do cliente")
    projeto_descricao: str = Field(..., description="Descrição do projeto")
    
    tipo_export: str = Field(..., description="Tipo de export (cut_planning, usinagem, completo)")
    conteudo_xml: str = Field(..., description="Conteúdo XML")
    
    data_geracao: str = Field(..., description="Data de geração (ISO format)")
    versao: str = Field(default="1.0", description="Versão do schema")
    
    class Config:
        json_schema_extra = {
            "example": {
                "lote_id": "L20260411001",
                "cliente_nome": "Cliente XYZ",
                "projeto_descricao": "Projeto ABC",
                "tipo_export": "cut_planning",
                "conteudo_xml": "<?xml version=\"1.0\"?>...",
                "data_geracao": "2026-04-11T10:30:00",
                "versao": "1.0"
            }
        }

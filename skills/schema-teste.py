# apps/integracoes/dinabox/schemas/dinabox_schemas_v2_mature.py
"""
SCHEMA MADURO DO DINABOX PARA TARUGO

Suporta ciclo completo de vida operacional:
- Processos administrativos (financeiro, pcp, compras, estoque)
- Processos de fábrica (bipagem, corte, bordo, duplagem, furação, usinagem)
- Processos de marcenaria (montagem, tamponamentos, itens especiais, agrupamento)
- Processos de logística (expedição, viagens, entrega)

Arquitetura: ProcessingState + FinancialMetadata + OperationalMetadata + AuditTrail
"""

from datetime import datetime
from typing import List, Optional, Dict, Any, Literal
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator


# =================== ENUMS DE ESTADO E ETAPA ===================

class ProcessingStateProject(str, Enum):
    """Estados do projeto (do Dinabox até conclusão)"""
    DRAFT = "DRAFT"              # Rascunho no Dinabox
    DESIGN = "DESIGN"            # Design aprovado, não processado ainda
    APPROVED = "APPROVED"        # Aprovado pelo cliente / administrativo
    WAITING_PCP = "WAITING_PCP" # Aguardando processamento do PCP
    IN_PRODUCTION = "IN_PRODUCTION"  # Em produção
    COMPLETED = "COMPLETED"      # Finalizado completamente
    CANCELLED = "CANCELLED"      # Cancelado


class OperationalStage(str, Enum):
    """14 Etapas operacionais no mapa da fábrica"""
    RECEBIMENTO_ITEM = "RECEBIMENTO_ITEM"
    SEPARACAO_RESERVA = "SEPARACAO_RESERVA"
    CORTE = "CORTE"
    BORDA = "BORDA"
    DUPLAGEM = "DUP"
    USINAGEM = "USI"
    FURACAO = "FUR"
    SEPARACAO_DESTINOS = "SEPARACAO_DESTINOS"
    MONTAGEM_CAIXA = "MCX"
    MONTAGEM_PERFIS = "MPE"
    MARCENARIA = "MAR"
    MARCENARIA_ESPECIAL = "XMAR"
    BORDA_MANUAL = "XBOR"
    MONTAGEM_ELETRICA = "MEL"
    CONTROLE_QUALIDADE = "CQL"
    EXPEDICAO = "EXPEDICAO"

    @property
    def sequence_order(self) -> int:
        """Retorna a ordem na sequência de produção para validação de transição"""
        order = {
            'RECEBIMENTO_ITEM': 1,
            'SEPARACAO_RESERVA': 2,
            'CORTE': 3,
            'BORDA': 4,
            'DUPLAGEM': 5,
            'USINAGEM': 6,
            'FURACAO': 7,
            'SEPARACAO_DESTINOS': 8,
            'MONTAGEM_CAIXA': 9,
            'MONTAGEM_PERFIS': 10,
            'MARCENARIA': 11,
            'MARCENARIA_ESPECIAL': 12,
            'BORDA_MANUAL': 13,
            'MONTAGEM_ELETRICA': 14,
            'CONTROLE_QUALIDADE': 15,
            'EXPEDICAO': 16,
        }
        return order.get(self.value, 0)


class ModuleProcessingState(str, Enum):
    """Estado de um módulo no processo de montagem"""
    PENDENTE = "PENDENTE"
    PARCIALMENTE_PROCESSADO = "PARCIALMENTE_PROCESSADO"
    AGUARDANDO_MONTAGEM = "AGUARDANDO_MONTAGEM"
    EM_MONTAGEM = "EM_MONTAGEM"
    PRONTO_PARA_EXPEDIÇÃO = "PRONTO_PARA_EXPEDIÇÃO"
    CONCLUÍDO = "CONCLUÍDO"


class FinancialCategory(str, Enum):
    """Categorias de custo para breakdown financeiro"""
    MATERIA_PRIMA = "MATERIA_PRIMA"
    MAO_DE_OBRA_CORTE = "MAO_DE_OBRA_CORTE"
    MAO_DE_OBRA_BORDO = "MAO_DE_OBRA_BORDO"
    MAO_DE_OBRA_USI = "MAO_DE_OBRA_USI"
    MAO_DE_OBRA_MARCENARIA = "MAO_DE_OBRA_MARCENARIA"
    INSUMOS_PROCESSAMENTO = "INSUMOS_PROCESSAMENTO"
    OVERHEAD_PRODUCAO = "OVERHEAD_PRODUCAO"
    TRANSITORIA = "TRANSITORIA"
    EXPEDIÇÃO = "EXPEDIÇÃO"


class ShipmentStatus(str, Enum):
    """Estado de expedição e viagem"""
    AGUARDANDO = "AGUARDANDO"
    CONFERIDO = "CONFERIDO"
    EMBALADO = "EMBALADO"
    EM_TRANSITO = "EM_TRANSITO"
    ENTREGUE = "ENTREGUE"
    DEVOLVIDO = "DEVOLVIDO"


# =================== MODELOS DE BASE ===================

class DinaboxBaseModel(BaseModel):
    """Base model com configuração comum"""
    model_config = ConfigDict(
        populate_by_name=True,
        extra="allow",
        arbitrary_types_allowed=True,
        from_attributes=True,
    )


class TraceabilityEvent(DinaboxBaseModel):
    """Evento único de rastreabilidade (uma transição de etapa)"""
    timestamp: datetime = Field(default_factory=datetime.now)
    stage: OperationalStage
    previous_stage: Optional[OperationalStage] = None
    operator_id: Optional[str] = None
    operator_name: Optional[str] = None
    location: Optional[str] = None  # Localização física (máquina, setor)
    notes: Optional[str] = None
    system_source: str = Field(default="MANUAL")  # MANUAL, BIPAGEM_SCANNER, PCP_AUTO, etc.
    batch_number: Optional[str] = None  # Lote PCP associado


class AuditTrail(DinaboxBaseModel):
    """Histórico completo de processamento de uma peça ou módulo"""
    created_by: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    last_modified_by: Optional[str] = None
    last_modified_at: datetime = Field(default_factory=datetime.now)
    events: List[TraceabilityEvent] = Field(default_factory=list)

    def add_event(self, event: TraceabilityEvent):
        """Adiciona um evento ao histórico"""
        self.events.append(event)
        self.last_modified_at = datetime.now()


class FinancialBreakdown(DinaboxBaseModel):
    """Decomposição de custos por categoria e etapa"""
    material_cost: float = Field(0.0, description="Custo da matéria-prima")
    labor_cost_by_stage: Dict[str, float] = Field(
        default_factory=dict,
        description="Custo de mão-de-obra por etapa {stage: cost}"
    )
    supplies_cost: float = Field(0.0, description="Insumos de processamento")
    overhead_allocation: float = Field(0.0, description="Alocação de overhead")
    subcontracting_cost: float = Field(0.0, description="Custos de terceirização")

    @property
    def total_cost(self) -> float:
        """Retorna custo total"""
        labor_total = sum(self.labor_cost_by_stage.values())
        return sum([
            self.material_cost,
            labor_total,
            self.supplies_cost,
            self.overhead_allocation,
            self.subcontracting_cost,
        ])


class StockAllocation(DinaboxBaseModel):
    """Alocação de material em estoque"""
    material_id: str = Field(..., description="ID do material em estoque")
    quantity_allocated: float = Field(..., description="Quantidade alocada/reservada")
    quantity_consumed: float = Field(0.0, description="Quantidade consumida")
    purchase_order_id: Optional[str] = None
    supplier_id: Optional[str] = None
    expected_delivery_date: Optional[datetime] = None
    actual_delivery_date: Optional[datetime] = None
    lot_number: Optional[str] = None


class OperationalMetadata(DinaboxBaseModel):
    """Metadados operacionais de uma peça ou módulo"""
    # Linkagem com sistemas
    pcp_batch_id: Optional[str] = None  # PID do processamento PCP
    pcp_order_id: Optional[str] = None  # ID da ordem de produção PCP
    bipagem_lot_number: Optional[str] = None  # Lote de bipagem associado
    
    # Estado operacional
    current_stage: OperationalStage = OperationalStage.RECEBIMENTO_ITEM
    previous_stage: Optional[OperationalStage] = None
    stage_entry_time: datetime = Field(default_factory=datetime.now)
    stage_exit_time: Optional[datetime] = None
    
    # Indicadores de sequência
    ready_for_next_stage: bool = False
    blocked_reason: Optional[str] = None  # Se não está pronto, por quê?
    
    # Localização e destino
    current_location: Optional[str] = None  # Setor/máquina atual
    destination_after_stage: Optional[str] = None
    
    # Viagem/Expedição
    shipment_id: Optional[str] = None
    trip_number: Optional[str] = None
    shipment_status: ShipmentStatus = ShipmentStatus.AGUARDANDO
    
    # Audit
    audit_trail: AuditTrail = Field(default_factory=AuditTrail)


class LogisticsInfo(DinaboxBaseModel):
    """Informações específicas de logística e expedição"""
    shipment_id: Optional[str] = None
    trip_id: Optional[str] = None
    customer_location: Optional[str] = None
    dispatch_date: Optional[datetime] = None
    delivery_date: Optional[datetime] = None
    tracking_number: Optional[str] = None
    carrier: Optional[str] = None
    weight_kg: Optional[float] = None
    volume_m3: Optional[float] = None
    special_handling: Optional[str] = None  # Frágil, controlado temperatura, etc.


# =================== MODELOS DE PEÇA ===================

class HoleDetail(DinaboxBaseModel):
    """Detalhe de um furo ou rasgo (usinagem)"""
    type: str = Field(..., alias="t", description="F=Furo, R=Rasgo")
    x: Optional[float] = Field(None, description="X coordinate para furos")
    x1: Optional[float] = Field(None, description="Start X para rasgos")
    x2: Optional[float] = Field(None, description="End X para rasgos")
    y1: Optional[float] = Field(None, description="Start Y para rasgos")
    y2: Optional[float] = Field(None, description="End Y para rasgos")
    y: float = Field(..., description="Y coordinate")
    z: float = Field(..., description="Z coordinate/profundidade")
    diameter: float = Field(..., alias="d", description="Diâmetro ou largura da ferramenta")
    r1: Optional[str] = Field(None, description="Referência 1 (pode incluir templates {{B01}})")
    r2: Optional[str] = Field(None, description="Referência 2")

    @field_validator("diameter", "x", "y", "z", "x1", "x2", "y1", "y2", mode="before")
    @classmethod
    def parse_float_values(cls, v: Any) -> Optional[float]:
        """Converte strings com vírgula em float"""
        if isinstance(v, str) and v.strip():
            try:
                return float(v.replace(",", "."))
            except ValueError:
                return None
        return v


class PartHoles(DinaboxBaseModel):
    """Furos organizados por face (A, B, C, D, E, F) - máximo 6"""
    face_a: Optional[List[HoleDetail]] = Field(None, alias="A")
    face_b: Optional[List[HoleDetail]] = Field(None, alias="B")
    face_c: Optional[List[HoleDetail]] = Field(None, alias="C")
    face_d: Optional[List[HoleDetail]] = Field(None, alias="D")
    face_e: Optional[List[HoleDetail]] = Field(None, alias="E")
    face_f: Optional[List[HoleDetail]] = Field(None, alias="F")
    invert: bool = False

    @property
    def total_holes(self) -> int:
        """Retorna total de operações de usinagem"""
        count = 0
        for face in [self.face_a, self.face_b, self.face_c, self.face_d, self.face_e, self.face_f]:
            if face:
                count += len(face)
        return count


class EdgeDetail(DinaboxBaseModel):
    """Detalhe de rebordo (borda) para um lado"""
    name: Optional[str] = Field(None, description="Nome do material de rebordo")
    material_id: Optional[str] = Field(None)
    perimeter: Optional[float] = Field(None, description="Perímetro em metros")
    thickness_abs: Optional[str] = Field(None, alias="abs", description="Espessura absoluta")
    factory_price: Optional[float] = Field(0.0)

    @field_validator("perimeter", mode="before")
    @classmethod
    def parse_perimeter(cls, v: Any) -> Optional[float]:
        if isinstance(v, str) and v.strip():
            try:
                return float(v.replace(",", "."))
            except:
                return None
        return v


class MaterialInfo(DinaboxBaseModel):
    """Informação consolidada de material"""
    id: str = Field(..., alias="material_id")
    name: str = Field(..., alias="material_name")
    manufacturer: Optional[str] = Field(None, alias="material_manufacturer")
    collection: Optional[str] = Field(None, alias="material_collection")
    m2: Optional[float] = Field(None, alias="material_m2", description="Área em m²")
    vein: bool = Field(False, alias="material_vein", description="Tem veio (madeira maciça)?")
    width: Optional[float] = Field(None, alias="material_width")
    height: Optional[float] = Field(None, alias="material_height")
    face: Optional[str] = Field(None, alias="material_face", description="Tipo de face (1f, 2f)")
    thumbnail: Optional[str] = Field(None, alias="material_thumbnail")
    reference: Optional[str] = Field(None, alias="material_ref", description="Ref do fornecedor")

    @field_validator("width", "height", "m2", mode="before")
    @classmethod
    def parse_float(cls, v: Any) -> Optional[float]:
        if isinstance(v, str) and v.strip():
            try:
                return float(v.replace(",", "."))
            except ValueError:
                return None
        return v


class Part(DinaboxBaseModel):
    """Peça individual dentro de um módulo - NÚCLEO DE RASTREABILIDADE"""
    
    # Identifição primária (Dinabox)
    id: str = Field(..., description="ID único da peça no Dinabox")
    ref: str = Field(..., description="Referência da peça no Dinabox")
    
    # Identificação para Tarugo (PCP/Bipagem)
    code_a: Optional[str] = Field(None, description="Código A (WMS/PCP)")
    code_b: Optional[str] = Field(None, description="Código B (WMS/PCP)")
    code_a2: Optional[str] = Field(None, description="Código A2 (variante)")
    code_b2: Optional[str] = Field(None, description="Código B2 (variante)")
    
    # Descrição
    name: str
    type: str  # cabinet, drawer, etc.
    entity: str  # Tipo de entidade Dinabox
    count: int = 1  # Quantidade de repetições desta peça no módulo
    note: Optional[str] = ""
    
    # Dimensões (em mm)
    width: float
    height: float
    thickness: float
    weight: float = 0.0
    
    # Material principal
    material: MaterialInfo
    
    # Rebordos (4 lados)
    edge_left: EdgeDetail = Field(default_factory=EdgeDetail)
    edge_right: EdgeDetail = Field(default_factory=EdgeDetail)
    edge_top: EdgeDetail = Field(default_factory=EdgeDetail)
    edge_bottom: EdgeDetail = Field(default_factory=EdgeDetail)
    
    # Usinagem (furação, rasgos)
    holes: Optional[PartHoles] = None
    
    # Preços (base Dinabox)
    factory_price: float = 0.0
    buy_price: float = 0.0
    sale_price: float = 0.0
    
    # Financeiro detalhado (para PCP/Compras)
    financial_breakdown: FinancialBreakdown = Field(default_factory=FinancialBreakdown)
    
    # Estoque (para compras e rastreabilidade)
    stock_allocations: List[StockAllocation] = Field(default_factory=list)
    
    # Operacional (rastreabilidade em fábrica)
    operational_metadata: OperationalMetadata = Field(default_factory=OperationalMetadata)
    
    # Logística (viagem, expedição)
    logistics_info: LogisticsInfo = Field(default_factory=LogisticsInfo)

    @classmethod
    def model_validate(cls, obj: Any, **kwargs) -> "Part":
        """Validação customizada para mapear campos flat do Dinabox"""
        if isinstance(obj, dict):
            # Mapear material
            material_data = {k: v for k, v in obj.items() if k.startswith("material_")}
            if material_data:
                obj["material"] = material_data
            
            # Mapear rebordos
            for side in ["left", "right", "top", "bottom"]:
                edge_key = f"edge_{side}"
                if edge_key not in obj or not obj[edge_key]:
                    edge_data = {
                        "name": obj.get(edge_key),
                        "material_id": obj.get(f"{edge_key}_id"),
                        "perimeter": obj.get(f"{edge_key}_perimeter"),
                        "thickness_abs": obj.get(f"{edge_key}_abs"),
                        "factory_price": obj.get(f"{edge_key}_factory"),
                    }
                    obj[edge_key] = edge_data
        
        return super().model_validate(obj, **kwargs)


# =================== MODELOS DE INPUT (HARDWARE) ===================

class InputItem(DinaboxBaseModel):
    """Item de insumo/hardware associado a um módulo"""
    id: str
    unique_id: str
    category_id: Optional[str] = None
    category_name: str
    name: str
    description: Optional[str] = ""
    qt: float = Field(..., description="Quantidade")
    unit: Optional[str] = None
    
    # Financeiro
    factory_price: float = 0.0
    buy_price: float = 0.0
    sale_price: float = 0.0
    
    # Estoque
    stock_allocations: List[StockAllocation] = Field(default_factory=list)
    
    # Operacional
    supplier_id: Optional[str] = None
    manufacturer: Optional[str] = None
    reference: Optional[str] = None


# =================== MODELOS DE MÓDULO ===================

class Module(DinaboxBaseModel):
    """Módulo contendo peças e insumos - UNIDADE DE MONTAGEM"""
    
    # Identifição (Dinabox)
    id: str
    mid: str = Field(..., description="ID do módulo no Dinabox")
    ref: str
    
    # Descrição
    name: str
    type: str  # cabinet, drawer, etc.
    qt: int = 1  # Quantidade de repetições deste módulo
    note: Optional[str] = ""
    
    # Dimensões
    width: float
    height: float
    thickness: float
    thumbnail: Optional[str] = None
    
    # Conteúdo
    parts: List[Part] = Field(default_factory=list)
    inputs: List[InputItem] = Field(default_factory=list)
    
    # Estado de processamento
    processing_state: ModuleProcessingState = ModuleProcessingState.PENDENTE
    
    # Metadados operacionais para a montagem
    operational_metadata: OperationalMetadata = Field(default_factory=OperationalMetadata)
    
    # Rastreamento de subfases de marcenaria
    # (útil para MCX, MPE, MAR, MEL)
    completed_stages: List[OperationalStage] = Field(default_factory=list)
    pending_stages: List[OperationalStage] = Field(default_factory=list)
    
    @property
    def total_parts(self) -> int:
        """Total de peças no módulo"""
        return len(self.parts)
    
    @property
    def total_inputs(self) -> int:
        """Total de insumos"""
        return len(self.inputs)
    
    @property
    def total_holes(self) -> int:
        """Total de operações de usinagem em todas as peças"""
        return sum(part.holes.total_holes if part.holes else 0 for part in self.parts)
    
    def add_completed_stage(self, stage: OperationalStage):
        """Marca uma etapa como concluída no módulo"""
        if stage not in self.completed_stages:
            self.completed_stages.append(stage)
        if stage in self.pending_stages:
            self.pending_stages.remove(stage)


# =================== MODELO DE PROJETO ===================

class ProjectHoleSummary(DinaboxBaseModel):
    """Resumo de hardware/furos a nível de projeto"""
    id: str
    ref: str = Field(default="")
    name: str
    qt: int
    dimensions: Optional[str] = None  # "50x50x30"
    weight: Optional[float] = None


class DinaboxProjectResponse(DinaboxBaseModel):
    """Resposta de projeto do Dinabox - RAIZ DA HIERARQUIA"""
    
    # Identifição do projeto
    project_id: str = Field(..., description="ID único do projeto no Dinabox")
    project_status: str = Field(..., description="Status no Dinabox (production, draft, etc.)")
    project_version: int
    
    # Descrição
    project_description: str
    project_note: Optional[str] = ""
    project_details: Optional[str] = ""
    
    # Cliente
    project_customer_id: str
    project_customer_name: str
    project_customer_address: Optional[str] = None
    
    # Timestamps
    project_created: str
    project_last_modified: str
    project_author_id: Optional[int] = None
    project_author_name: Optional[str] = None
    
    # Conteúdo
    woodwork: List[Module] = Field(default_factory=list)
    holes_summary: List[ProjectHoleSummary] = Field(default_factory=[], alias="holes")
    
    # Metadados administrativos
    processing_state: ProcessingStateProject = ProcessingStateProject.DESIGN
    audit_trail: AuditTrail = Field(default_factory=AuditTrail)
    
    # Linkagem com Tarugo
    pcp_processed: bool = False
    pcp_batch_ids: List[str] = Field(default_factory=list, description="Lista de PIDs dos processamentos PCP")
    
    # Timestamp de importação
    imported_at: datetime = Field(default_factory=datetime.now)
    last_synced_at: datetime = Field(default_factory=datetime.now)
    
    @field_validator("project_created", "project_last_modified", mode="before")
    @classmethod
    def parse_dates(cls, v: str) -> str:
        """Valida formatos de data do Dinabox"""
        return v
    
    @property
    def total_modules(self) -> int:
        """Total de módulos"""
        return len(self.woodwork)
    
    @property
    def total_parts(self) -> int:
        """Total de peças em todos os módulos"""
        return sum(m.total_parts for m in self.woodwork)
    
    @property
    def total_inputs(self) -> int:
        """Total de insumos em todos os módulos"""
        return sum(m.total_inputs for m in self.woodwork)
    
    @property
    def total_holes(self) -> int:
        """Total de operações de usinagem"""
        return sum(m.total_holes for m in self.woodwork)
    
    @property
    def estimated_total_cost(self) -> float:
        """Custo estimado total do projeto"""
        total = 0.0
        for module in self.woodwork:
            for part in module.parts:
                total += part.financial_breakdown.total_cost or part.factory_price
            for input_item in module.inputs:
                total += input_item.factory_price * input_item.qt
        return total
    
    def mark_as_pcp_processed(self, pcp_batch_id: str):
        """Marca projeto como processado pelo PCP"""
        self.pcp_processed = True
        self.pcp_batch_ids.append(pcp_batch_id)
        self.processing_state = ProcessingStateProject.IN_PRODUCTION


# =================== VALIDATORS PARA TRANSIÇÕES DE ETAPA ===================

@model_validator(mode="after")
def validate_stage_sequence(self: "Part") -> "Part":
    """Valida que as transições de etapa respeitam a sequência"""
    if hasattr(self, 'operational_metadata'):
        current = self.operational_metadata.current_stage
        previous = self.operational_metadata.previous_stage
        
        if previous:
            current_order = current.sequence_order
            previous_order = previous.sequence_order
            
            # Permite retorno (para retraços/correções)
            if current_order < previous_order - 2:
                raise ValueError(
                    f"Transição inválida: {previous.value} → {current.value}. "
                    "Retorno permitido apenas até 2 etapas anteriores (para retraços)."
                )
    
    return self


# =================== EXPORT DAS CLASSES MADURAS ===================

__all__ = [
    'ProcessingStateProject',
    'OperationalStage',
    'ModuleProcessingState',
    'FinancialCategory',
    'ShipmentStatus',
    'TraceabilityEvent',
    'AuditTrail',
    'FinancialBreakdown',
    'StockAllocation',
    'OperationalMetadata',
    'LogisticsInfo',
    'HoleDetail',
    'PartHoles',
    'EdgeDetail',
    'MaterialInfo',
    'Part',
    'InputItem',
    'Module',
    'ProjectHoleSummary',
    'DinaboxProjectResponse',
]
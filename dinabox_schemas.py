from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, ConfigDict, field_validator


class DinaboxBaseModel(BaseModel):
    """Base model with common configuration for all Dinabox schemas."""
    model_config = ConfigDict(
        populate_by_name=True,
        extra="allow",  # Allow extra fields to ensure future-proofing
        arbitrary_types_allowed=True
    )


class HoleDetail(DinaboxBaseModel):
    """Details of a single hole or slot (rasgo) operation."""
    type: str = Field(..., alias="t", description="Type of operation (F=Furo, R=Rasgo)")
    
    # Coordinates for circular holes
    x: Optional[float] = Field(None, description="X coordinate for holes")
    
    # Coordinates for slots (rasgos)
    x1: Optional[float] = Field(None, description="Start X for slots")
    x2: Optional[float] = Field(None, description="End X for slots")
    y1: Optional[float] = Field(None, description="Start Y for slots")
    y2: Optional[float] = Field(None, description="End Y for slots")
    
    y: float = Field(..., description="Y coordinate (or reference Y for slots)")
    z: float = Field(..., description="Z coordinate/depth")
    diameter: float = Field(..., alias="d", description="Diameter or width of the tool")
    
    r1: Optional[str] = Field(None, description="Reference 1")
    r2: Optional[str] = Field(None, description="Reference 2")


class PartHoles(DinaboxBaseModel):
    """Holes organized by face (A, B, C, D, E, F)."""
    face_a: Optional[List[HoleDetail]] = Field(None, alias="A")
    face_b: Optional[List[HoleDetail]] = Field(None, alias="B")
    face_c: Optional[List[HoleDetail]] = Field(None, alias="C")
    face_d: Optional[List[HoleDetail]] = Field(None, alias="D")
    face_e: Optional[List[HoleDetail]] = Field(None, alias="E")
    face_f: Optional[List[HoleDetail]] = Field(None, alias="F")
    invert: bool = False


class EdgeDetail(DinaboxBaseModel):
    """Details of edge banding for a specific side."""
    name: Optional[str] = Field(None)
    material_id: Optional[str] = Field(None)
    perimeter: Optional[float] = Field(None)
    thickness_abs: Optional[str] = Field(None, alias="abs")
    factory_price: Optional[float] = Field(0.0)


class MaterialInfo(DinaboxBaseModel):
    """Consolidated material information for a part."""
    id: str = Field(..., alias="material_id")
    name: str = Field(..., alias="material_name")
    manufacturer: Optional[str] = Field(None, alias="material_manufacturer")
    collection: Optional[str] = Field(None, alias="material_collection")
    m2: Optional[float] = Field(None, alias="material_m2")
    vein: bool = Field(False, alias="material_vein")
    width: Optional[float] = Field(None, alias="material_width")
    height: Optional[float] = Field(None, alias="material_height")
    face: Optional[str] = Field(None, alias="material_face")
    thumbnail: Optional[str] = Field(None, alias="material_thumbnail")

    @field_validator("width", "height", mode="before")
    @classmethod
    def parse_float(cls, v: Any) -> Optional[float]:
        if isinstance(v, str) and v.strip():
            try:
                return float(v.replace(",", "."))
            except ValueError:
                return None
        return v


class Part(DinaboxBaseModel):
    """Individual piece (part) within a module."""
    id: str
    ref: str
    name: str
    type: str
    entity: str
    count: int = 1
    note: Optional[str] = ""
    
    # Dimensions
    width: float
    height: float
    thickness: float
    weight: float = 0.0
    
    # Material
    material: MaterialInfo = Field(..., description="Flattened material info from the response")
    
    # Edge Banding
    edge_left: EdgeDetail = Field(default_factory=EdgeDetail)
    edge_right: EdgeDetail = Field(default_factory=EdgeDetail)
    edge_top: EdgeDetail = Field(default_factory=EdgeDetail)
    edge_bottom: EdgeDetail = Field(default_factory=EdgeDetail)
    
    # Technical / CNC
    holes: Optional[PartHoles] = None
    
    # Pricing
    factory_price: float = 0.0
    buy_price: float = 0.0
    sale_price: float = 0.0

    @classmethod
    def model_validate(cls, obj: Any, **kwargs) -> "Part":
        """Custom validation to handle flattened material and edge fields."""
        if isinstance(obj, dict):
            # Map material fields
            material_data = {k: v for k, v in obj.items() if k.startswith("material_")}
            obj["material"] = material_data
            
            # Map edge fields
            for side in ["left", "right", "top", "bottom"]:
                edge_key = f"edge_{side}"
                edge_data = {
                    "name": obj.get(edge_key),
                    "material_id": obj.get(f"{edge_key}_id"),
                    "perimeter": obj.get(f"{edge_key}_perimeter"),
                    "abs": obj.get(f"{edge_key}_abs"),
                    "factory_price": obj.get(f"{edge_key}_factory"),
                }
                obj[edge_key] = edge_data
        return super().model_validate(obj, **kwargs)


class InputItem(DinaboxBaseModel):
    """Hardware or other input items associated with a module."""
    id: str
    unique_id: str
    category_name: str
    name: str
    description: Optional[str] = ""
    qt: float
    unit: Optional[str] = None
    factory_price: float = 0.0


class Module(DinaboxBaseModel):
    """A module containing parts and inputs."""
    id: str
    mid: str
    ref: str
    name: str
    type: str
    qt: int = 1
    note: Optional[str] = ""
    width: float
    height: float
    thickness: float
    thumbnail: Optional[str] = None
    
    parts: List[Part] = Field(default_factory=list)
    inputs: List[InputItem] = Field(default_factory=list)


class ProjectHoleSummary(DinaboxBaseModel):
    """Summary of hardware/holes at project level."""
    id: str
    name: str
    qt: int


class DinaboxProjectResponse(DinaboxBaseModel):
    """Root object for the Dinabox API project response."""
    project_id: str
    project_status: str
    project_version: int
    project_description: str
    project_customer_id: str
    project_customer_name: str
    
    # Timestamps
    project_created: str
    project_last_modified: str
    
    # Content
    holes_summary: List[ProjectHoleSummary] = Field(default_factory=list, alias="holes")
    woodwork: List[Module] = Field(default_factory=list)
    
    # Metadata for Tarugo
    imported_at: datetime = Field(default_factory=datetime.now)

    @field_validator("project_created", "project_last_modified")
    @classmethod
    def validate_dates(cls, v: str) -> str:
        # Keep as string or convert to datetime if needed
        return v

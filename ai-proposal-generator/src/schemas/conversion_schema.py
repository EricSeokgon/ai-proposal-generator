"""변환 스키마 (Stage 5): PPTX → JSON → HTML → Figma"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class ShapeData(BaseModel):
    shape_id: int
    shape_type: str
    left: float
    top: float
    width: float
    height: float
    rotation: float = 0
    text: Optional[str] = None
    font_name: Optional[str] = None
    font_size: Optional[float] = None
    font_color: Optional[str] = None
    bold: Optional[bool] = None
    alignment: Optional[str] = None
    fill_color: Optional[str] = None
    fill_type: Optional[str] = None
    border_color: Optional[str] = None
    border_width: Optional[float] = None
    image_path: Optional[str] = None
    table_data: Optional[Dict[str, Any]] = None
    chart_data: Optional[Dict[str, Any]] = None

class SlideJSON(BaseModel):
    slide_index: int
    width: float = 13.333
    height: float = 7.5
    shapes: List[ShapeData] = Field(default_factory=list)
    background: Dict[str, Any] = Field(default_factory=dict)
    notes: Optional[str] = None
    layout_name: Optional[str] = None

class HTMLSlide(BaseModel):
    slide_index: int
    html_content: str
    css_content: str = ""
    inline_html: Optional[str] = None

class ConversionResult(BaseModel):
    json_data: List[SlideJSON] = Field(default_factory=list)
    json_output_path: Optional[str] = None
    html_slides: List[HTMLSlide] = Field(default_factory=list)
    html_output_dir: Optional[str] = None
    figma_ready: bool = False
    figma_import_method: str = "manual"
    figma_url: Optional[str] = None
    total_slides: int = 0
    success: bool = True
    errors: List[str] = Field(default_factory=list)

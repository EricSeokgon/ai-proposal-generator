"""기획 스키마 (Stage 3)"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from .proposal_schema import SlideContent, SlideType, WinTheme

class SlideSpec(BaseModel):
    slide_index: int
    phase_number: int
    topic: str
    purpose: str
    slide_type_hint: Optional[str] = None

class ProposalStructure(BaseModel):
    total_slides: int
    phase_breakdown: Dict[int, int] = Field(description="Phase별 슬라이드 수")
    slide_specs: List[SlideSpec] = Field(default_factory=list)
    win_themes: List[WinTheme] = Field(default_factory=list)
    one_sentence_pitch: Optional[str] = None
    proposal_type: str = "general"

class SlideScript(BaseModel):
    slide_index: int
    phase_number: int
    action_title: str
    slide_type: SlideType
    content: SlideContent
    key_message: Optional[str] = None
    speaker_notes: Optional[str] = None
    win_theme_reference: Optional[str] = None

class SlideScripts(BaseModel):
    scripts: List[SlideScript] = Field(default_factory=list)
    total_scripts: int = 0

class LayoutAssignment(BaseModel):
    slide_index: int
    layout_name: str
    layout_rationale: str
    visual_elements: List[str] = Field(default_factory=list)

class SlideLayouts(BaseModel):
    assignments: List[LayoutAssignment] = Field(default_factory=list)

class ColorPalette(BaseModel):
    primary: str = "#002C5F"
    secondary: str = "#00AAD2"
    teal: str = "#00A19C"
    accent: str = "#E63312"
    dark_bg: str = "#1A1A1A"
    light_bg: str = "#F5F5F5"
    additional: Dict[str, str] = Field(default_factory=dict)

class Typography(BaseModel):
    primary_font: str = "Pretendard"
    title_size: int = 36
    body_size: int = 18
    section_title_size: int = 48
    teaser_title_size: int = 72

class DesignPlan(BaseModel):
    theme_name: str = "modern"
    colors: ColorPalette = Field(default_factory=ColorPalette)
    typography: Typography = Field(default_factory=Typography)
    style_notes: str = ""
    cover_style: Optional[str] = None
    section_divider_style: Optional[str] = None
    per_slide_hints: List[Dict[str, Any]] = Field(default_factory=list)

class ProposalPlan(BaseModel):
    structure: ProposalStructure
    scripts: SlideScripts
    layouts: SlideLayouts
    design: DesignPlan
    rfp_analysis: Optional[Dict[str, Any]] = None
    research: Optional[Dict[str, Any]] = None

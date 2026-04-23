"""제작/검수 스키마 (Stage 4)"""
from typing import List, Optional
from pydantic import BaseModel, Field

class ProductionResult(BaseModel):
    pptx_path: str = ""
    generation_script_path: str = ""
    slide_count: int = 0
    success: bool = True
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)

class QAIssue(BaseModel):
    slide_index: int
    severity: str
    category: str
    description: str
    suggestion: str

class QAReport(BaseModel):
    total_issues: int = 0
    critical_count: int = 0
    warning_count: int = 0
    info_count: int = 0
    issues: List[QAIssue] = Field(default_factory=list)
    passed: bool = True
    summary: str = ""
    slide_count_match: bool = True
    font_consistent: bool = True
    color_consistent: bool = True
    placeholder_format: bool = True
    page_numbers_present: bool = True

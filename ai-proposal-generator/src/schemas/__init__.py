"""데이터 스키마 모듈"""
from .proposal_schema import (
    ProposalContent, PhaseContent, SlideContent, SlideType,
    BulletPoint, TableData, ChartData, WinTheme, KPIWithBasis,
)
from .rfp_schema import RFPAnalysis
from .research_schema import ResearchResult
from .planning_schema import (
    ProposalStructure, SlideSpec, SlideScript, SlideScripts,
    LayoutAssignment, SlideLayouts, DesignPlan, ProposalPlan,
)
from .production_schema import ProductionResult, QAIssue, QAReport
from .conversion_schema import SlideJSON, HTMLSlide, ConversionResult

__all__ = [
    "ProposalContent", "PhaseContent", "SlideContent", "SlideType",
    "BulletPoint", "TableData", "ChartData", "WinTheme", "KPIWithBasis",
    "RFPAnalysis", "ResearchResult",
    "ProposalStructure", "SlideSpec", "SlideScript", "SlideScripts",
    "LayoutAssignment", "SlideLayouts", "DesignPlan", "ProposalPlan",
    "ProductionResult", "QAIssue", "QAReport",
    "SlideJSON", "HTMLSlide", "ConversionResult",
]

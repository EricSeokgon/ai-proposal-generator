"""
리서치 결과 스키마
ResearchAgent가 웹 검색을 통해 수집한 시장/경쟁/트렌드 데이터
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class MarketData(BaseModel):
    category: str = Field(description="데이터 카테고리")
    data_points: List[Dict[str, Any]] = Field(default_factory=list)
    source: str = Field(description="데이터 출처")
    relevance: str = Field(description="프로젝트와의 관련성")

class CompetitorInfo(BaseModel):
    name: str = Field(description="경쟁사명")
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    market_position: str = Field(default="")
    recent_activities: Optional[List[str]] = None

class TrendData(BaseModel):
    trend_name: str = Field(description="트렌드명")
    description: str = Field(description="트렌드 설명")
    relevance_to_project: str = Field(description="프로젝트와의 관련성")
    data_source: str = Field(description="출처")
    supporting_data: Optional[Dict[str, Any]] = None

class CaseStudy(BaseModel):
    project_name: str = Field(description="프로젝트명")
    client: str = Field(default="")
    summary: str = Field(description="사례 요약")
    results: List[str] = Field(default_factory=list)
    relevance: str = Field(description="관련성")
    source_url: Optional[str] = None

class KPIBenchmark(BaseModel):
    metric: str = Field(description="지표명")
    industry_average: str = Field(description="업계 평균")
    top_performer: Optional[str] = None
    source: str = Field(description="출처")
    notes: Optional[str] = None

class ResearchResult(BaseModel):
    market_data: List[MarketData] = Field(default_factory=list)
    competitors: List[CompetitorInfo] = Field(default_factory=list)
    trends: List[TrendData] = Field(default_factory=list)
    case_studies: List[CaseStudy] = Field(default_factory=list)
    kpi_benchmarks: List[KPIBenchmark] = Field(default_factory=list)
    additional_insights: List[str] = Field(default_factory=list)
    sources: List[str] = Field(default_factory=list)
    search_queries: List[str] = Field(default_factory=list)

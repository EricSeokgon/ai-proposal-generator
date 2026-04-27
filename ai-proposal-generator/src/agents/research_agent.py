"""
리서치 에이전트 (Stage 2)

분석 결과를 기반으로 시장/경쟁/트렌드 추가 정보를 수집한다.

⚠️ 중요: 현재 본 에이전트는 **실제 웹 검색을 수행하지 않으며**, Claude 모델의 학습 데이터를
기반으로 응답한다. 따라서 시장 데이터/통계/경쟁사 정보가 **최신 정보가 아닐 수 있고
환각(hallucination)을 포함할 수 있다**. 실제 MCP WebSearch 또는 별도 검색 API 연동 시
``_perform_research`` 메서드를 확장해야 한다.
"""

import json
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from .base_agent import BaseAgent
from ..schemas.rfp_schema import RFPAnalysis
from ..schemas.research_schema import ResearchResult
from ..utils.logger import get_logger

logger = get_logger("research_agent")

# 출처 메타 — 사용자/하위 에이전트가 데이터의 신뢰도 컨텍스트를 알 수 있게 하는 마커
RESEARCH_SOURCE_MARKER_LLM = "claude_internal_knowledge"


class ResearchAgent(BaseAgent):
    """리서치 에이전트 — MCP WebSearch 연동으로 추가 정보 수집"""

    async def execute(
        self,
        input_data: Dict[str, Any],
        progress_callback: Optional[Callable] = None,
    ) -> ResearchResult:
        """
        분석 결과를 기반으로 추가 리서치 수행

        Args:
            input_data: {"rfp_analysis": RFPAnalysis (or dict)}
            progress_callback: 진행 상황 콜백

        Returns:
            ResearchResult: 리서치 결과
        """
        rfp_analysis = input_data.get("rfp_analysis")
        if isinstance(rfp_analysis, RFPAnalysis):
            rfp_dict = rfp_analysis.model_dump()
        else:
            rfp_dict = rfp_analysis or {}

        if progress_callback:
            progress_callback({
                "stage": "research",
                "step": 1,
                "total": 3,
                "message": "리서치 계획 수립 중...",
            })

        # Step 1: 리서치 계획 수립 (검색 쿼리 생성)
        search_queries = await self._generate_search_queries(rfp_dict)

        if progress_callback:
            progress_callback({
                "stage": "research",
                "step": 2,
                "total": 3,
                "message": f"웹 검색 수행 중... ({len(search_queries)}개 쿼리)",
            })

        # Step 2: 웹 검색 수행 (MCP WebSearch 또는 Claude 지식 기반)
        search_results = await self._perform_research(rfp_dict, search_queries)

        if progress_callback:
            progress_callback({
                "stage": "research",
                "step": 3,
                "total": 3,
                "message": "리서치 결과 구조화 중...",
            })

        # Step 3: 결과 구조화
        research_result = await self._structure_results(rfp_dict, search_results, search_queries)

        logger.info(
            f"리서치 완료: 시장데이터 {len(research_result.market_data)}건, "
            f"경쟁사 {len(research_result.competitors)}건, "
            f"트렌드 {len(research_result.trends)}건"
        )

        return research_result

    async def _generate_search_queries(self, rfp_dict: Dict) -> List[str]:
        """RFP 분석 기반 검색 쿼리 생성"""
        system_prompt = """당신은 제안서 작성을 위한 리서치 전문가입니다.
RFP 분석 결과를 보고 추가 조사가 필요한 검색 쿼리를 생성합니다.

다음 카테고리별로 검색 쿼리를 생성해주세요:
1. 시장 규모 및 동향 (2-3개)
2. 경쟁사/유사 사례 (2-3개)
3. 산업 트렌드 (2개)
4. KPI 벤치마크 (1-2개)

JSON 배열로 응답해주세요: ["쿼리1", "쿼리2", ...]"""

        user_message = f"""
프로젝트: {rfp_dict.get('project_name', '미확인')}
발주처: {rfp_dict.get('client_name', '미확인')}
개요: {rfp_dict.get('project_overview', '')}
유형: {rfp_dict.get('project_type', 'general')}
핵심 고민: {json.dumps(rfp_dict.get('pain_points', []), ensure_ascii=False)}
"""

        response = self._call_claude(system_prompt, user_message, max_tokens=2048)
        queries = self._extract_json(response)

        if isinstance(queries, list):
            return queries[:10]
        elif isinstance(queries, dict) and "queries" in queries:
            return queries["queries"][:10]

        # 폴백 쿼리 — 동적 연도 사용 (이전: "2024 2025" 하드코딩)
        current_year = datetime.now().year
        return [
            f"{rfp_dict.get('project_name', '')} 시장 규모",
            f"{rfp_dict.get('project_type', '')} 트렌드 {current_year - 1} {current_year}",
        ]

    async def _perform_research(
        self, rfp_dict: Dict, search_queries: List[str]
    ) -> str:
        """웹 검색 수행 및 결과 수집.

        ⚠️ 현재 외부 웹 검색이 연동되지 않아 Claude 모델의 학습 데이터에만 의존한다.
        결과는 학습 컷오프 이전 시점의 정보이며 환각이 포함될 수 있음을 호출자가
        반드시 인지해야 한다 (``ResearchResult.sources`` 에 마커 추가).
        실제 MCP WebSearch 연동 시 이 메서드를 확장한다.
        """
        self.logger.warning(
            "ResearchAgent: 외부 웹 검색 미연동 — Claude 학습 데이터 기반 응답이며 "
            "최신성/정확성을 보장하지 않음 (출처 마커: "
            f"{RESEARCH_SOURCE_MARKER_LLM})"
        )
        system_prompt = self._load_prompt("research")
        if not system_prompt:
            self.logger.warning(
                "프롬프트 부재 (research.txt) → 내장 default 사용"
            )
            system_prompt = self._get_default_research_prompt()

        user_message = f"""
## 프로젝트 정보
- 프로젝트명: {rfp_dict.get('project_name', '미확인')}
- 발주처: {rfp_dict.get('client_name', '미확인')}
- 개요: {rfp_dict.get('project_overview', '')}
- 유형: {rfp_dict.get('project_type', 'general')}

## 분석된 핵심 정보
- Pain Points: {json.dumps(rfp_dict.get('pain_points', []), ensure_ascii=False)}
- Win Theme 후보: {json.dumps(rfp_dict.get('win_theme_candidates', []), ensure_ascii=False)}
- 차별화 포인트: {json.dumps(rfp_dict.get('differentiation_points', []), ensure_ascii=False)}

## 조사 필요 항목
{json.dumps(search_queries, ensure_ascii=False, indent=2)}

위 프로젝트에 대해 다음을 조사해주세요:
1. 시장 데이터 (규모, 성장률, 주요 지표)
2. 경쟁사 분석 (주요 경쟁사, 강점/약점)
3. 산업 트렌드 (최신 동향, 기술 트렌드)
4. 유사 사례 (성공 사례, 참고할 프로젝트)
5. KPI 벤치마크 (업계 평균, 상위 성과 기준)

JSON 형식으로 응답해주세요.
"""

        return self._call_claude(system_prompt, user_message, max_tokens=8192)

    async def _structure_results(
        self, rfp_dict: Dict, raw_results: str, search_queries: List[str]
    ) -> ResearchResult:
        """리서치 결과를 ResearchResult 스키마로 구조화.

        외부 웹 검색이 미연동된 상태에서는 ``sources`` 리스트 마지막에
        ``RESEARCH_SOURCE_MARKER_LLM`` 마커를 자동 추가해 하위 단계가
        데이터 출처 컨텍스트를 인식할 수 있게 한다.
        """
        data = self._extract_json(raw_results)
        sources = list(data.get("sources", []))
        # 외부 검색 미연동 마커 — 중복 추가 방지
        if RESEARCH_SOURCE_MARKER_LLM not in sources:
            sources.append(RESEARCH_SOURCE_MARKER_LLM)

        return ResearchResult(
            market_data=[
                {"category": item.get("category", ""), "data_points": item.get("data_points", []),
                 "source": item.get("source", ""), "relevance": item.get("relevance", "")}
                for item in data.get("market_data", [])
            ],
            competitors=[
                {"name": item.get("name", ""), "strengths": item.get("strengths", []),
                 "weaknesses": item.get("weaknesses", []), "market_position": item.get("market_position", "")}
                for item in data.get("competitors", [])
            ],
            trends=[
                {"trend_name": item.get("trend_name", ""), "description": item.get("description", ""),
                 "relevance_to_project": item.get("relevance_to_project", ""),
                 "data_source": item.get("data_source", "")}
                for item in data.get("trends", [])
            ],
            case_studies=[
                {"project_name": item.get("project_name", ""), "client": item.get("client", ""),
                 "summary": item.get("summary", ""), "results": item.get("results", []),
                 "relevance": item.get("relevance", "")}
                for item in data.get("case_studies", [])
            ],
            kpi_benchmarks=[
                {"metric": item.get("metric", ""), "industry_average": item.get("industry_average", ""),
                 "top_performer": item.get("top_performer"), "source": item.get("source", "")}
                for item in data.get("kpi_benchmarks", [])
            ],
            additional_insights=data.get("additional_insights", []),
            sources=sources,
            search_queries=search_queries,
        )

    def _get_default_research_prompt(self) -> str:
        """기본 리서치 시스템 프롬프트"""
        return """당신은 입찰 제안서 작성을 위한 리서치 전문가입니다.
RFP 분석 결과를 바탕으로 제안서의 설득력을 높이기 위한 추가 정보를 조사합니다.

## 조사 원칙
1. **데이터 기반**: 가능한 한 구체적인 수치와 통계를 제공
2. **출처 명시**: 모든 데이터에 출처를 함께 기재
3. **관련성**: 프로젝트와 직접 관련 있는 정보 우선
4. **최신성**: 가능한 한 최근 데이터 제공

## 조사 카테고리
1. **시장 데이터**: 시장 규모, 성장률, 주요 지표
2. **경쟁사 분석**: 주요 경쟁사, 강점/약점, 시장 포지션
3. **산업 트렌드**: 최신 동향, 기술 트렌드, 소비자 변화
4. **유사 사례**: 성공 사례, 참고 프로젝트, 벤치마크
5. **KPI 벤치마크**: 업계 평균, 상위 성과 기준

응답은 반드시 유효한 JSON 형식으로 제공해주세요.

```json
{
    "market_data": [...],
    "competitors": [...],
    "trends": [...],
    "case_studies": [...],
    "kpi_benchmarks": [...],
    "additional_insights": [...],
    "sources": [...]
}
```"""

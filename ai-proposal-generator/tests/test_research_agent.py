"""G P1-2 — ResearchAgent 외부 API 명시 + 동적 연도 검증."""

from datetime import datetime
from unittest.mock import patch

import pytest

from src.agents.research_agent import (
    ResearchAgent,
    RESEARCH_SOURCE_MARKER_LLM,
)


class TestSourceMarker:
    def test_marker_constant_defined(self):
        assert RESEARCH_SOURCE_MARKER_LLM == "claude_internal_knowledge"


class TestDynamicYearInFallbackQueries:
    """폴백 쿼리에서 동적 연도 사용 (이전: '2024 2025' 하드코딩)."""

    @pytest.mark.asyncio
    async def test_fallback_queries_use_current_year(self):
        agent = ResearchAgent()
        rfp = {"project_name": "X", "project_type": "marketing_pr"}

        # _call_claude 응답을 비-list/dict 로 모킹 → 폴백 쿼리 트리거
        with patch.object(agent, "_call_claude", return_value="not json"):
            queries = await agent._generate_search_queries(rfp)

        current_year = datetime.now().year
        prev_year = current_year - 1
        joined = " ".join(queries)
        assert str(current_year) in joined
        assert str(prev_year) in joined
        # 하드코딩된 옛 연도(2024, 2025) 만 있는지 확인 — 2026 이후에도 정상 작동
        assert len(queries) == 2


class TestSourcesMarkerAddedAutomatically:
    """``_structure_results`` 가 sources 에 LLM 마커를 자동 추가."""

    @pytest.mark.asyncio
    async def test_marker_appended_when_absent(self):
        agent = ResearchAgent()
        raw = """```json
{
  "market_data": [],
  "competitors": [],
  "trends": [],
  "case_studies": [],
  "kpi_benchmarks": [],
  "sources": ["내부 보고서 2024"]
}
```"""
        result = await agent._structure_results({}, raw, ["q1"])
        assert RESEARCH_SOURCE_MARKER_LLM in result.sources
        assert "내부 보고서 2024" in result.sources

    @pytest.mark.asyncio
    async def test_marker_not_duplicated(self):
        agent = ResearchAgent()
        raw = f"""```json
{{
  "market_data": [],
  "competitors": [],
  "trends": [],
  "case_studies": [],
  "kpi_benchmarks": [],
  "sources": ["{RESEARCH_SOURCE_MARKER_LLM}"]
}}
```"""
        result = await agent._structure_results({}, raw, ["q1"])
        # 정확히 한 번만 등장해야 함
        assert result.sources.count(RESEARCH_SOURCE_MARKER_LLM) == 1

    @pytest.mark.asyncio
    async def test_marker_added_when_no_sources(self):
        agent = ResearchAgent()
        raw = """```json
{
  "market_data": [],
  "competitors": [],
  "trends": [],
  "case_studies": [],
  "kpi_benchmarks": []
}
```"""
        result = await agent._structure_results({}, raw, ["q1"])
        assert RESEARCH_SOURCE_MARKER_LLM in result.sources

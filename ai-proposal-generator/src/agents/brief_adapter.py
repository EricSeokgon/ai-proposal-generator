"""
브리프 어댑터 (브레인스토밍 → 제안서 연계)

campaign_brief.md를 RFPAnalysis + ResearchResult로 변환하여
제안서 파이프라인 Stage 1~2를 건너뛰고 Stage 3(기획)부터 시작
"""

import json
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from .base_agent import BaseAgent
from ..utils.logger import get_logger

logger = get_logger("brief_adapter")


class BriefAdapter(BaseAgent):
    """campaign_brief.md → RFPAnalysis + ResearchResult 변환"""

    async def execute(
        self,
        input_data: Dict[str, Any],
        progress_callback: Optional[Callable] = None,
    ) -> Dict[str, Any]:
        """
        브레인스토밍 산출물을 제안서 파이프라인 입력으로 변환

        Args:
            input_data: {
                "brief_path": str (campaign_brief.md 경로),
                "project_dir": str (output/프로젝트명/ 경로),
            }

        Returns:
            {
                "rfp_analysis": dict,
                "research": dict,
                "source": "brainstorm",
            }
        """
        brief_path = input_data.get("brief_path", "")
        project_dir = input_data.get("project_dir", "")

        if progress_callback:
            progress_callback({
                "stage": "brief_adapter",
                "step": 1,
                "total": 3,
                "message": "브레인스토밍 산출물 로드 중...",
            })

        # Step 1: 파일 로드
        brief = self._load_file(brief_path)
        strategy = ""
        creative = ""
        data = ""

        if project_dir:
            pdir = Path(project_dir)
            if not brief:
                brief = self._load_file(str(pdir / "campaign_brief.md"))
            strategy = self._load_file(str(pdir / "brainstorm_strategy.md"))
            creative = self._load_file(str(pdir / "brainstorm_creative.md"))
            data = self._load_file(str(pdir / "brainstorm_data.md"))

        if not brief:
            raise FileNotFoundError("campaign_brief.md를 찾을 수 없습니다")

        if progress_callback:
            progress_callback({
                "stage": "brief_adapter",
                "step": 2,
                "total": 3,
                "message": "브리프 → 분석 형식 변환 중...",
            })

        # Step 2: RFPAnalysis 변환
        rfp_analysis = await self._convert_to_rfp(brief, strategy, creative)

        if progress_callback:
            progress_callback({
                "stage": "brief_adapter",
                "step": 3,
                "total": 3,
                "message": "리서치 데이터 추출 중...",
            })

        # Step 3: ResearchResult 추출
        research = await self._extract_research(strategy, data, brief)

        logger.info(f"브리프 변환 완료: {rfp_analysis.get('project_name', '?')}")

        return {
            "rfp_analysis": rfp_analysis,
            "research": research,
            "source": "brainstorm",
        }

    async def _convert_to_rfp(self, brief: str, strategy: str, creative: str) -> Dict:
        """campaign_brief → RFPAnalysis dict"""

        system_prompt = """캠페인 기획안을 제안서 분석 형식(JSON)으로 변환하세요.
브레인스토밍에서 이미 도출된 Win Theme, 타겟, 전략을 그대로 활용합니다.
응답은 유효한 JSON으로."""

        user_message = f"""
## campaign_brief.md
{self._truncate_text(brief, 8000)}

## 전략 보고서
{self._truncate_text(strategy, 4000) if strategy else "(없음)"}

## 크리에이티브 보고서
{self._truncate_text(creative, 3000) if creative else "(없음)"}

JSON으로 변환:
```json
{{
    "project_name": "프로젝트명",
    "client_name": "브랜드명",
    "project_overview": "개요 2-3문장",
    "project_type": "marketing_pr",
    "key_requirements": [{{"category": "마케팅", "requirement": "요구사항", "priority": "필수"}}],
    "evaluation_criteria": [],
    "deliverables": [],
    "timeline": {{"total_duration": "기간"}},
    "budget": {{"total_budget": "예산"}},
    "pain_points": ["타겟 고민 1", "고민 2", "고민 3"],
    "hidden_needs": ["숨겨진 니즈 1"],
    "win_theme_candidates": [
        {{"name": "Win Theme 1", "rationale": "이유", "rfp_alignment": "전략 연결"}},
        {{"name": "Win Theme 2", "rationale": "이유", "rfp_alignment": "전략 연결"}},
        {{"name": "Win Theme 3", "rationale": "이유", "rfp_alignment": "전략 연결"}}
    ],
    "competitive_landscape": "경쟁 환경",
    "key_success_factors": ["성공 요인"],
    "differentiation_points": ["차별화 포인트"]
}}
```"""

        response = self._call_claude(system_prompt, user_message, max_tokens=4096)
        return self._extract_json(response)

    async def _extract_research(self, strategy: str, data: str, brief: str) -> Dict:
        """전략/데이터 보고서 → ResearchResult dict"""

        if not strategy and not data:
            return {"market_data": [], "competitors": [], "trends": [],
                    "case_studies": [], "kpi_benchmarks": [], "sources": []}

        system_prompt = """브레인스토밍 보고서에서 리서치 데이터를 JSON으로 추출하세요.
응답은 유효한 JSON으로."""

        user_message = f"""
## 전략 보고서
{self._truncate_text(strategy, 5000) if strategy else "(없음)"}

## 데이터 분석 보고서
{self._truncate_text(data, 5000) if data else "(없음)"}

JSON 추출:
```json
{{
    "market_data": [{{"category": "카테고리", "data_points": [{{"value": "수치"}}], "source": "출처", "relevance": "관련성"}}],
    "competitors": [{{"name": "경쟁사", "strengths": ["강점"], "weaknesses": ["약점"], "market_position": "포지션"}}],
    "trends": [{{"trend_name": "트렌드", "description": "설명", "relevance_to_project": "관련성", "data_source": "출처"}}],
    "case_studies": [{{"project_name": "사례", "summary": "요약", "results": ["성과"], "relevance": "관련성"}}],
    "kpi_benchmarks": [{{"metric": "지표", "industry_average": "평균", "source": "출처"}}],
    "sources": ["출처1"]
}}
```"""

        response = self._call_claude(system_prompt, user_message, max_tokens=4096)
        return self._extract_json(response)

    def _load_file(self, path: str) -> str:
        """파일 로드 — 인코딩 오류, 권한 오류는 워닝 후 빈 문자열 반환.

        브리프 파일 1개의 인코딩 문제로 전체 변환이 중단되지 않도록 한다.
        """
        if not path:
            return ""
        p = Path(path)
        if not p.exists():
            return ""
        try:
            return p.read_text(encoding="utf-8")
        except UnicodeDecodeError as e:
            self.logger.warning(
                f"파일 인코딩 오류 ({p.name}, UTF-8 디코드 실패: {e}) → cp949 재시도"
            )
            try:
                return p.read_text(encoding="cp949")
            except (UnicodeDecodeError, OSError) as e2:
                self.logger.error(f"cp949 폴백도 실패 ({p.name}): {e2} → 빈 문자열 반환")
                return ""
        except OSError as e:
            self.logger.warning(f"파일 읽기 실패 ({p.name}): {e} → 빈 문자열 반환")
            return ""

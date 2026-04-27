"""
구조 기획 에이전트 (Stage 3-1)

제안서 전체 구조 기획: Phase별 슬라이드 수, 토픽, Win Theme 확정
"""

import json
from typing import Any, Callable, Dict, Optional

from ..base_agent import BaseAgent
from ...schemas.planning_schema import (
    ProposalStructure,
    MIN_TOTAL_SLIDES,
    MAX_TOTAL_SLIDES,
)
from ...schemas.proposal_schema import PHASE_DEFINITIONS, get_phase_weights, ProposalType
from ...utils.logger import get_logger

logger = get_logger("structure_planner")

# Claude 응답이 비정상일 때 사용하는 합리적 폴백 슬라이드 수
_FALLBACK_TOTAL_SLIDES = 80


class StructurePlanner(BaseAgent):
    """제안서 전체 구조 기획 에이전트"""

    async def execute(
        self,
        input_data: Dict[str, Any],
        progress_callback: Optional[Callable] = None,
    ) -> ProposalStructure:
        """
        제안서 전체 구조를 기획

        Args:
            input_data: {
                "rfp_analysis": dict (RFPAnalysis),
                "research": dict (ResearchResult, optional),
                "proposal_type": str (optional),
            }
        """
        rfp = input_data.get("rfp_analysis", {})
        research = input_data.get("research", {})
        proposal_type = input_data.get("proposal_type") or rfp.get("project_type", "general")

        if progress_callback:
            progress_callback({
                "stage": "planning",
                "sub_stage": "structure",
                "step": 1,
                "total": 2,
                "message": "제안서 구조 기획 중...",
            })

        # Phase 가중치 로드
        try:
            weights = get_phase_weights(ProposalType(proposal_type))
        except (ValueError, KeyError):
            weights = get_phase_weights(ProposalType.GENERAL)

        system_prompt = self._load_prompt("planning_structure")
        if not system_prompt:
            self.logger.warning(
                "프롬프트 부재 (planning_structure.txt) → 내장 default 사용"
            )
            system_prompt = self._get_default_prompt()

        user_message = f"""
## RFP 분석 결과
- 프로젝트명: {rfp.get('project_name', '미확인')}
- 발주처: {rfp.get('client_name', '미확인')}
- 유형: {proposal_type}
- 개요: {rfp.get('project_overview', '')}

## Pain Points
{json.dumps(rfp.get('pain_points', []), ensure_ascii=False)}

## Win Theme 후보
{json.dumps(rfp.get('win_theme_candidates', []), ensure_ascii=False)}

## 평가 전략
{json.dumps(rfp.get('evaluation_strategy', {}), ensure_ascii=False)}

## 리서치 요약
- 시장 트렌드: {json.dumps([t.get('trend_name', '') for t in research.get('trends', [])], ensure_ascii=False)}
- 유사 사례: {json.dumps([c.get('project_name', '') for c in research.get('case_studies', [])], ensure_ascii=False)}

## Impact-8 Phase 가중치 ({proposal_type})
{json.dumps({{f"Phase {k}: {PHASE_DEFINITIONS[k]['title']}": f"{v*100:.0f}%" for k, v in weights.items()}}, ensure_ascii=False, indent=2)}

## Phase 정의
{json.dumps({{k: {{"title": v["title"], "recommended_slides": v["recommended_slides"]}} for k, v in PHASE_DEFINITIONS.items()}}, ensure_ascii=False, indent=2)}

위 정보를 기반으로 제안서 전체 구조를 기획해주세요.
JSON 형식으로 응답해주세요.

```json
{{
    "total_slides": 80,
    "proposal_type": "{proposal_type}",
    "one_sentence_pitch": "한 문장 핵심 메시지",
    "win_themes": [
        {{"name": "키워드", "description": "설명", "evidence": ["근거1", "근거2"], "related_phases": [2, 4, 6]}}
    ],
    "phase_breakdown": {{0: 5, 1: 3, 2: 10, 3: 10, 4: 30, 5: 8, 6: 10, 7: 4}},
    "slide_specs": [
        {{"slide_index": 0, "phase_number": 0, "topic": "토픽", "purpose": "목적", "slide_type_hint": "teaser"}}
    ]
}}
```
"""

        response = self._call_claude(system_prompt, user_message, max_tokens=8192)
        data = self._extract_json(response)

        if progress_callback:
            progress_callback({
                "stage": "planning",
                "sub_stage": "structure",
                "step": 2,
                "total": 2,
                "message": "구조 기획 완료",
            })

        # phase_breakdown 키를 int로 변환 + 음수/비정수 필터
        phase_breakdown: Dict[int, int] = {}
        for k, v in data.get("phase_breakdown", {}).items():
            try:
                phase_int = int(k)
                count_int = int(v)
            except (TypeError, ValueError):
                self.logger.warning(f"phase_breakdown 잘못된 항목 무시: {k}={v}")
                continue
            if 0 <= phase_int <= 7 and count_int >= 0:
                phase_breakdown[phase_int] = count_int
            else:
                self.logger.warning(f"phase_breakdown 범위 외 항목 무시: phase={phase_int}, count={count_int}")

        # total_slides 합리적 범위로 클램핑 (Pydantic Field 검증 실패 차단)
        total_slides = self._clamp_total_slides(data.get("total_slides"))

        # phase_breakdown 합계 검증 (불일치 시 워닝만)
        breakdown_sum = sum(phase_breakdown.values())
        if breakdown_sum > 0 and abs(breakdown_sum - total_slides) > total_slides * 0.2:
            self.logger.warning(
                f"phase_breakdown 합계({breakdown_sum}) 와 total_slides({total_slides}) 가 "
                f"20% 이상 차이 — 후속 단계에서 슬라이드 누락/추가 가능"
            )

        self.logger.info(
            f"구조 기획 완료: 총 {total_slides} 슬라이드 "
            f"(phase_breakdown 합계={breakdown_sum})"
        )

        return ProposalStructure(
            total_slides=total_slides,
            phase_breakdown=phase_breakdown,
            slide_specs=data.get("slide_specs", []),
            win_themes=data.get("win_themes", []),
            one_sentence_pitch=data.get("one_sentence_pitch"),
            proposal_type=proposal_type,
        )

    def _clamp_total_slides(self, raw_value: Any) -> int:
        """Claude 응답의 total_slides 를 합리적 범위로 클램핑.

        - None / 비정수 → ``_FALLBACK_TOTAL_SLIDES`` (80)
        - 범위 밖 → MIN_TOTAL_SLIDES~MAX_TOTAL_SLIDES 로 클램프
        - 워닝 로그로 추적 가능
        """
        try:
            value = int(raw_value)
        except (TypeError, ValueError):
            self.logger.warning(
                f"total_slides 비정수({raw_value!r}) → 폴백 {_FALLBACK_TOTAL_SLIDES}"
            )
            return _FALLBACK_TOTAL_SLIDES

        if value < MIN_TOTAL_SLIDES:
            self.logger.warning(
                f"total_slides={value} 가 최솟값({MIN_TOTAL_SLIDES}) 미만 → 클램프"
            )
            return MIN_TOTAL_SLIDES
        if value > MAX_TOTAL_SLIDES:
            self.logger.warning(
                f"total_slides={value} 가 최댓값({MAX_TOTAL_SLIDES}) 초과 → 클램프"
            )
            return MAX_TOTAL_SLIDES
        return value

    def _get_default_prompt(self) -> str:
        return """당신은 입찰 제안서 구조 설계 전문가입니다.
Impact-8 Framework (Phase 0~7) 기반으로 제안서 전체 구조를 기획합니다.

## 구조 기획 원칙
1. Phase 가중치에 따라 슬라이드 수 배분
2. ACTION PLAN (Phase 4)이 가장 많은 비중
3. Win Theme 3개를 확정하고 Phase별 연결
4. 각 슬라이드의 목적과 토픽을 명확히 정의
5. 평가 기준 고배점 항목에 대응하는 슬라이드 배치

응답은 반드시 유효한 JSON 형식으로 제공해주세요."""

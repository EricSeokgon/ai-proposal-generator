"""
레이아웃 기획 에이전트 (Stage 3-3)

슬라이드별 최적 레이아웃 및 시각 요소 선택
"""

import json
from typing import Any, Callable, Dict, List, Optional

from ..base_agent import BaseAgent
from ...schemas.planning_schema import SlideLayouts
from ...utils.logger import get_logger

logger = get_logger("layout_planner")

# slide_kit.LAYOUTS 30종 키 (단일 소스에서 동적 로딩)
# 임포트 실패 시 안전 폴백을 위한 30종 키 리스트(slide_kit.py:1036~의 키 목록)
_SLIDE_KIT_LAYOUTS_FALLBACK = frozenset({
    "FULL_BODY", "HIGHLIGHT_BODY", "TWO_COL", "THREE_COL", "FOUR_COL",
    "COMPARE_LR", "HIGHLIGHT_THREE_CARD", "KPI_GRID", "PROCESS_DESC",
    "TIMELINE_DESC", "PYRAMID_DESC", "MATRIX_DESC", "STAT_ROW",
    "KEY_VISUAL", "TABLE_INSIGHT", "LEFT_TEXT_RIGHT_IMG",
    "TOP_IMG_BOTTOM_TEXT", "ORG_CHART", "RISK_CARD", "GANTT",
    "SPLIT_DARK_LIGHT", "QUOTE_CENTER", "METRIC_HIGHLIGHT", "CHECKLIST",
    "NUMBERED_STEPS", "TWO_ROW_THREE_COL", "DONUT_STATS",
    "SIDEBAR_CONTENT", "AGENDA_LIST", "ICON_CARD_4",
})


def _load_valid_layouts() -> frozenset:
    """slide_kit.LAYOUTS 에서 동적으로 30종 키를 로드 (실패 시 폴백 사용)"""
    try:
        from src.generators.slide_kit import LAYOUTS
        return frozenset(LAYOUTS.keys())
    except Exception:
        return _SLIDE_KIT_LAYOUTS_FALLBACK


VALID_LAYOUT_NAMES: frozenset = _load_valid_layouts()
DEFAULT_LAYOUT = "FULL_BODY"  # 화이트리스트 미일치 시 폴백


# 콘텐츠 유형별 권장 레이아웃 매핑
CONTENT_LAYOUT_MAP = {
    "시장 환경": "THREE_COL",
    "핵심 인사이트": "HIGHLIGHT_BODY",
    "전략 프레임워크": "PYRAMID_DESC",
    "채널 비교": "COMPARE_LR",
    "실행 프로세스": "PROCESS_DESC",
    "KPI": "KPI_GRID",
    "일정": "GANTT",
    "조직도": "ORG_CHART",
    "실적": "GALLERY_3x2",
    "리스크": "RISK_CARD",
    "데이터 비교": "TABLE_INSIGHT",
    "통계": "FULL_BODY",
    "타임라인": "TIMELINE_DESC",
    "차별화": "FOUR_COL",
    "매트릭스": "MATRIX_DESC",
    "키비주얼": "KEY_VISUAL",
    "인용문": "HIGHLIGHT_BODY",
    "예산": "FULL_BODY",
    "차트": "FULL_BODY",
}


class LayoutPlanner(BaseAgent):
    """슬라이드별 레이아웃 기획 에이전트"""

    async def execute(
        self,
        input_data: Dict[str, Any],
        progress_callback: Optional[Callable] = None,
    ) -> SlideLayouts:
        """
        슬라이드별 레이아웃 배정

        Args:
            input_data: {
                "scripts": dict (SlideScripts),
                "structure": dict (ProposalStructure),
            }
        """
        scripts = input_data.get("scripts", {})
        structure = input_data.get("structure", {})
        slide_scripts = scripts.get("scripts", [])

        if progress_callback:
            progress_callback({
                "stage": "planning",
                "sub_stage": "layout",
                "step": 1,
                "total": 2,
                "message": f"레이아웃 배정 중... ({len(slide_scripts)}개 슬라이드)",
            })

        system_prompt = self._load_prompt("planning_layout")
        if not system_prompt:
            self.logger.warning(
                "프롬프트 부재 (planning_layout.txt) → 내장 default 사용"
            )
            system_prompt = self._get_default_prompt()

        # 스크립트 요약 (토큰 절약)
        script_summaries = []
        for s in slide_scripts:
            script_summaries.append({
                "slide_index": s.get("slide_index"),
                "phase_number": s.get("phase_number"),
                "action_title": s.get("action_title", ""),
                "slide_type": s.get("slide_type", "content"),
                "has_table": bool(s.get("content", {}).get("table")),
                "has_chart": bool(s.get("content", {}).get("chart")),
                "has_timeline": bool(s.get("content", {}).get("timeline")),
                "has_kpis": bool(s.get("content", {}).get("kpis")),
                "bullet_count": len(s.get("content", {}).get("bullets", [])),
            })

        user_message = f"""
## 슬라이드 스크립트 요약 ({len(script_summaries)}개)
{json.dumps(script_summaries, ensure_ascii=False, indent=2)}

## 사용 가능한 레이아웃
{json.dumps(CONTENT_LAYOUT_MAP, ensure_ascii=False, indent=2)}

## 추가 레이아웃
- THREE_COL: 3단 컬럼
- TWO_COL: 2단 컬럼
- FOUR_COL: 4단 컬럼
- FULL_BODY: 전면 본문
- HIGHLIGHT_BODY: 하이라이트 + 본문
- PROCESS_DESC: 프로세스 플로우
- PYRAMID_DESC: 피라미드
- COMPARE_LR: 좌우 비교
- KPI_GRID: KPI 그리드
- TIMELINE_DESC: 타임라인
- MATRIX_DESC: 2x2 매트릭스
- TABLE_INSIGHT: 테이블 + 인사이트
- GANTT: 간트 차트
- ORG_CHART: 조직도
- KEY_VISUAL: 키 비주얼

## 레이아웃 배정 원칙
1. 콘텐츠 유형에 맞는 레이아웃 선택
2. 연속 3장 이상 같은 레이아웃 금지 (시각 단조로움 방지)
3. Phase별로 다양한 레이아웃 배분
4. 각 슬라이드에 사용할 시각 요소 (KPIS, COLS, HIGHLIGHT, IMG_PH 등) 지정

각 슬라이드의 레이아웃을 JSON 배열로 응답해주세요:

```json
{{
    "assignments": [
        {{
            "slide_index": 0,
            "layout_name": "THREE_COL",
            "layout_rationale": "시장 데이터 3개 영역 비교에 적합",
            "visual_elements": ["COLS", "METRIC_CARD", "HIGHLIGHT"]
        }}
    ]
}}
```
"""

        response = self._call_claude(system_prompt, user_message, max_tokens=8192)
        data = self._extract_json(response)

        if progress_callback:
            progress_callback({
                "stage": "planning",
                "sub_stage": "layout",
                "step": 2,
                "total": 2,
                "message": "레이아웃 배정 완료",
            })

        assignments = data.get("assignments", [])
        assignments = self._sanitize_assignments(assignments)
        self.logger.info(f"레이아웃 배정 완료: {len(assignments)}개 슬라이드")

        return SlideLayouts(assignments=assignments)

    def _sanitize_assignments(self, raw_assignments: List[Dict]) -> List[Dict]:
        """Claude 응답의 layout_name 을 30종 화이트리스트로 강제 정합.

        - 유효하지 않은 layout_name → ``DEFAULT_LAYOUT`` 으로 폴백 (경고 로그)
        - layout_name 누락 → DEFAULT_LAYOUT 사용
        - 후속 PPTX 렌더링에서 KeyError 가 발생하지 않도록 사전 차단한다.
        """
        sanitized: List[Dict] = []
        for assignment in raw_assignments:
            if not isinstance(assignment, dict):
                self.logger.warning(f"잘못된 assignment 항목 (dict 아님): {type(assignment)} — 건너뜀")
                continue
            layout_name = assignment.get("layout_name", "")
            if layout_name not in VALID_LAYOUT_NAMES:
                self.logger.warning(
                    f"슬라이드 {assignment.get('slide_index', '?')}: "
                    f"무효한 layout_name '{layout_name}' → '{DEFAULT_LAYOUT}' 폴백"
                )
                assignment = dict(assignment)
                assignment["layout_name"] = DEFAULT_LAYOUT
                # 폴백 경위를 rationale 에 명시
                original_rationale = assignment.get("layout_rationale", "")
                assignment["layout_rationale"] = (
                    f"[자동 폴백: '{layout_name}' 미정의] {original_rationale}"
                ).strip()
            sanitized.append(assignment)
        return sanitized

    def _get_default_prompt(self) -> str:
        return """당신은 프레젠테이션 레이아웃 디자인 전문가입니다.
슬라이드 콘텐츠에 맞는 최적의 레이아웃을 선택합니다.

## 원칙
1. 콘텐츠가 레이아웃을 결정 (데이터 → 차트/테이블, 프로세스 → 플로우 등)
2. 시각 다양성 유지 (연속 3장 같은 레이아웃 금지)
3. Phase별 첫 슬라이드는 임팩트 있는 레이아웃
4. 데이터가 많은 슬라이드는 FULL_BODY + TABLE
5. 메시지 중심 슬라이드는 HIGHLIGHT_BODY

응답은 반드시 유효한 JSON 형식으로 제공해주세요."""

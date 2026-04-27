"""
디자인 기획 에이전트 (Stage 3-4)

컬러 팔레트, 타이포그래피, 비주얼 스타일 기획
"""

import json
from typing import Any, Callable, Dict, Optional

from ..base_agent import BaseAgent
from ...schemas.planning_schema import DesignPlan, ColorPalette, Typography
from ...utils.logger import get_logger

logger = get_logger("design_planner")


class DesignPlanner(BaseAgent):
    """디자인 기획 에이전트"""

    async def execute(
        self,
        input_data: Dict[str, Any],
        progress_callback: Optional[Callable] = None,
    ) -> DesignPlan:
        """
        디자인 시스템 기획

        Args:
            input_data: {
                "structure": dict (ProposalStructure),
                "rfp_analysis": dict,
                "reference_design": dict (optional, ReferenceAnalyzer 결과),
            }
        """
        structure = input_data.get("structure", {})
        rfp = input_data.get("rfp_analysis", {})
        reference = input_data.get("reference_design")

        if progress_callback:
            progress_callback({
                "stage": "planning",
                "sub_stage": "design",
                "step": 1,
                "total": 2,
                "message": "디자인 시스템 기획 중...",
            })

        # 레퍼런스 디자인이 있으면 반영
        reference_info = ""
        if reference:
            reference_info = f"""
## 디자인 레퍼런스 분석 결과
- 주요 색상: {json.dumps(reference.get('colors', {}), ensure_ascii=False)}
- 폰트: {reference.get('primary_font', '미확인')}
- 레이아웃 패턴: {reference.get('layout_pattern', '미확인')}
- 스타일: {reference.get('style_notes', '')}
"""

        system_prompt = self._load_prompt("planning_design")
        if not system_prompt:
            self.logger.warning(
                "프롬프트 부재 (planning_design.txt) → 내장 default 사용"
            )
            system_prompt = self._get_default_prompt()

        user_message = f"""
## 프로젝트 정보
- 프로젝트명: {rfp.get('project_name', '미확인')}
- 발주처: {rfp.get('client_name', '미확인')}
- 유형: {rfp.get('project_type', 'general')}
- 총 슬라이드: {structure.get('total_slides', 80)}

## Win Themes
{json.dumps(structure.get('win_themes', []), ensure_ascii=False)}
{reference_info}

## 기본 디자인 시스템 (Modern)
- Primary: #002C5F (다크 블루)
- Secondary: #00AAD2 (스카이 블루)
- Teal: #00A19C (Win Theme 뱃지)
- Accent: #E63312 (레드)
- Font: Pretendard
- 16:9 (1920×1080)

디자인 기획을 JSON으로 응답해주세요:

```json
{{
    "theme_name": "modern",
    "colors": {{
        "primary": "#002C5F",
        "secondary": "#00AAD2",
        "teal": "#00A19C",
        "accent": "#E63312",
        "dark_bg": "#1A1A1A",
        "light_bg": "#F5F5F5",
        "additional": {{}}
    }},
    "typography": {{
        "primary_font": "Pretendard",
        "title_size": 36,
        "body_size": 18,
        "section_title_size": 48,
        "teaser_title_size": 72
    }},
    "style_notes": "디자인 방향성 설명",
    "cover_style": "gradient",
    "section_divider_style": "dark_bg_large_number",
    "per_slide_hints": [
        {{"slide_index": 0, "visual_style": "dark", "accent_color": "#00AAD2"}}
    ]
}}
```
"""

        response = self._call_claude(system_prompt, user_message, max_tokens=4096)
        data = self._extract_json(response)

        if progress_callback:
            progress_callback({
                "stage": "planning",
                "sub_stage": "design",
                "step": 2,
                "total": 2,
                "message": "디자인 기획 완료",
            })

        colors_data = data.get("colors", {})
        typo_data = data.get("typography", {})

        logger.info(f"디자인 기획 완료: 테마 '{data.get('theme_name', 'modern')}'")

        return DesignPlan(
            theme_name=data.get("theme_name", "modern"),
            colors=ColorPalette(**colors_data) if colors_data else ColorPalette(),
            typography=Typography(**typo_data) if typo_data else Typography(),
            style_notes=data.get("style_notes", ""),
            cover_style=data.get("cover_style"),
            section_divider_style=data.get("section_divider_style"),
            per_slide_hints=data.get("per_slide_hints", []),
        )

    def _get_default_prompt(self) -> str:
        return """당신은 프레젠테이션 디자인 시스템 전문가입니다.
프로젝트 특성에 맞는 디자인 시스템을 기획합니다.

## 원칙
1. 프로젝트 성격에 맞는 컬러 톤 (공공: 신뢰감, 마케팅: 역동성)
2. 일관된 타이포그래피 계층 구조
3. 표지/섹션 구분자/콘텐츠 슬라이드 각각의 비주얼 스타일 정의
4. 레퍼런스 디자인이 있으면 최대한 반영

응답은 반드시 유효한 JSON 형식으로 제공해주세요."""

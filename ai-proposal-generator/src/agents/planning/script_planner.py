"""
스크립트 기획 에이전트 (Stage 3-2)

각 슬라이드의 Action Title, 콘텐츠, 키메시지 작성
"""

import json
from typing import Any, Callable, Dict, List, Optional

from ..base_agent import BaseAgent
from ...schemas.planning_schema import SlideScripts, ProposalStructure
from ...utils.logger import get_logger

logger = get_logger("script_planner")


class ScriptPlanner(BaseAgent):
    """슬라이드별 스크립트 기획 에이전트"""

    # Phase별 프롬프트 매핑 (기존 content_generator.py에서 이전)
    PHASE_PROMPTS = {
        0: "phase0_hook",
        1: "phase1_summary",
        2: "phase2_insight",
        3: "phase3_concept",
        4: "phase4_action",
        5: "phase5_management",
        6: "phase6_whyus",
        7: "phase7_investment",
    }

    async def execute(
        self,
        input_data: Dict[str, Any],
        progress_callback: Optional[Callable] = None,
    ) -> SlideScripts:
        """
        슬라이드별 스크립트 기획

        Args:
            input_data: {
                "structure": dict (ProposalStructure),
                "rfp_analysis": dict,
                "research": dict (optional),
            }
        """
        structure = input_data.get("structure", {})
        rfp = input_data.get("rfp_analysis", {})
        research = input_data.get("research", {})
        win_themes = structure.get("win_themes", [])

        all_scripts = []
        slide_specs = structure.get("slide_specs", [])

        # Phase별로 그룹핑
        phase_groups: Dict[int, List[Dict]] = {}
        for spec in slide_specs:
            phase_num = spec.get("phase_number", 0)
            phase_groups.setdefault(phase_num, []).append(spec)

        total_phases = len(phase_groups)
        current_phase = 0

        for phase_num in sorted(phase_groups.keys()):
            current_phase += 1
            specs = phase_groups[phase_num]

            if progress_callback:
                progress_callback({
                    "stage": "planning",
                    "sub_stage": "script",
                    "step": current_phase,
                    "total": total_phases,
                    "message": f"Phase {phase_num} 스크립트 작성 중...",
                })

            phase_scripts = await self._generate_phase_scripts(
                phase_num, specs, rfp, research, win_themes
            )
            all_scripts.extend(phase_scripts)

        logger.info(f"스크립트 기획 완료: {len(all_scripts)}개 슬라이드")

        return SlideScripts(
            scripts=all_scripts,
            total_scripts=len(all_scripts),
        )

    async def _generate_phase_scripts(
        self,
        phase_num: int,
        specs: List[Dict],
        rfp: Dict,
        research: Dict,
        win_themes: List[Dict],
    ) -> List[Dict]:
        """Phase별 슬라이드 스크립트 생성"""

        # Phase별 프롬프트 로드
        prompt_name = self.PHASE_PROMPTS.get(phase_num, f"phase{phase_num}_content")
        phase_prompt = self._load_prompt(prompt_name)

        system_prompt = self._load_prompt("planning_script")
        if not system_prompt:
            self.logger.warning(
                "프롬프트 부재 (planning_script.txt) → 내장 default 사용"
            )
            system_prompt = self._get_default_prompt()

        if phase_prompt:
            system_prompt += f"\n\n## Phase {phase_num} 전용 가이드\n{phase_prompt}"

        user_message = f"""
## Phase {phase_num} 스크립트 작성

### 슬라이드 명세 ({len(specs)}개)
{json.dumps(specs, ensure_ascii=False, indent=2)}

### 프로젝트 정보
- 프로젝트명: {rfp.get('project_name', '미확인')}
- 발주처: {rfp.get('client_name', '미확인')}
- 유형: {rfp.get('project_type', 'general')}

### Win Themes
{json.dumps(win_themes, ensure_ascii=False, indent=2)}

### 핵심 요구사항
{json.dumps(rfp.get('key_requirements', [])[:10], ensure_ascii=False, indent=2)}

### 리서치 데이터
- 시장 데이터: {json.dumps(research.get('market_data', [])[:3], ensure_ascii=False)}
- KPI 벤치마크: {json.dumps(research.get('kpi_benchmarks', [])[:3], ensure_ascii=False)}
- 트렌드: {json.dumps(research.get('trends', [])[:3], ensure_ascii=False)}

각 슬라이드의 스크립트를 JSON 배열로 응답해주세요:

```json
[
    {{
        "slide_index": 0,
        "phase_number": {phase_num},
        "action_title": "인사이트 기반 제목 (Action Title)",
        "slide_type": "content",
        "content": {{
            "slide_type": "content",
            "title": "Action Title",
            "bullets": [{{"text": "내용", "level": 0}}],
            "key_message": "핵심 메시지"
        }},
        "key_message": "핵심 메시지",
        "speaker_notes": "발표자 노트",
        "win_theme_reference": "관련 Win Theme (있는 경우)"
    }}
]
```
"""

        response = self._call_claude(system_prompt, user_message, max_tokens=8192)
        data = self._extract_json(response)

        scripts = self._coerce_scripts_list(data)
        if not scripts:
            self.logger.warning(
                f"Phase {phase_num}: Claude 응답에서 스크립트 배열 추출 실패 "
                f"(type={type(data).__name__}) — specs 기반 폴백 슬라이드 생성"
            )
            return self._build_fallback_scripts(specs, phase_num)

        # 각 항목이 dict 인지 정합성 검증 (잘못된 항목은 폴백으로 대체)
        validated: List[Dict] = []
        for i, item in enumerate(scripts):
            if not isinstance(item, dict):
                self.logger.warning(
                    f"Phase {phase_num} 스크립트[{i}] 가 dict 아님 ({type(item).__name__}) — 폴백"
                )
                spec = specs[i] if i < len(specs) else {"slide_index": -1, "phase_number": phase_num, "topic": ""}
                validated.append(self._make_fallback_script(spec, phase_num))
            else:
                validated.append(item)

        # 응답 슬라이드 수가 specs 보다 적으면 누락분 폴백 채움 (전체 손실 방지)
        if len(validated) < len(specs):
            self.logger.warning(
                f"Phase {phase_num}: Claude 응답 슬라이드 수({len(validated)}) "
                f"< specs({len(specs)}) — 누락분 폴백으로 채움"
            )
            received_indices = {s.get("slide_index") for s in validated if isinstance(s, dict)}
            for spec in specs:
                if spec.get("slide_index") not in received_indices:
                    validated.append(self._make_fallback_script(spec, phase_num))

        return validated

    @staticmethod
    def _coerce_scripts_list(data: Any) -> List[Dict]:
        """Claude 응답을 슬라이드 dict 리스트로 강제 변환.

        지원 형식:
        - ``[...]``           → 그대로
        - ``{"scripts": [...]}`` → 추출
        - 기타                → 빈 리스트
        """
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            if "scripts" in data and isinstance(data["scripts"], list):
                return data["scripts"]
            # 일부 응답이 {"slides": [...]} 등으로 올 가능성 처리
            for key in ("slides", "items", "data"):
                if key in data and isinstance(data[key], list):
                    return data[key]
        return []

    @staticmethod
    def _make_fallback_script(spec: Dict, phase_num: int) -> Dict:
        """단일 폴백 스크립트 — specs 정보로 최소 슬라이드 생성.

        후속 단계에서 ``[자동 폴백]`` 마커로 재생성 대상을 식별할 수 있다.
        """
        topic = spec.get("topic", "콘텐츠 미생성")
        return {
            "slide_index": spec.get("slide_index", -1),
            "phase_number": spec.get("phase_number", phase_num),
            "action_title": f"[자동 폴백] {topic}",
            "slide_type": "content",
            "content": {
                "slide_type": "content",
                "title": topic,
                "bullets": [],
                "key_message": "[자동 폴백 — 재생성 권장]",
            },
            "key_message": "[자동 폴백 — 재생성 권장]",
            "speaker_notes": "Claude 응답 파싱 실패로 인한 placeholder. 재생성 시 Action Title 보강 필요.",
            "win_theme_reference": None,
        }

    def _build_fallback_scripts(self, specs: List[Dict], phase_num: int) -> List[Dict]:
        """specs 전체에 대해 폴백 스크립트 생성"""
        return [self._make_fallback_script(spec, phase_num) for spec in specs]

    def _get_default_prompt(self) -> str:
        return """당신은 입찰 제안서 콘텐츠 전문가입니다.
각 슬라이드의 스크립트(내용)를 작성합니다.

## Action Title 원칙
- Topic Title이 아닌 Action Title (인사이트 기반)
- "타겟 분석" → "MZ세대 2030이 핵심, 하루 SNS 55분 사용"
- "채널 전략" → "인스타그램 중심, 릴스로 도달률 3배 확보"

## C-E-I 설득 구조
- Claim (주장): 슬라이드의 핵심 메시지
- Evidence (근거): 데이터, 사례, 통계
- Insight (인사이트): "그래서 우리는 이렇게 합니다"

## KPI 산출 근거
- 모든 수치에 산출 근거 포함
- "팔로워 +30% = 인플루언서 협업 +10% + 릴스 확대 +12% + 이벤트 +8%"

## Placeholder 형식
- [대괄호] 형식으로 통일
- [발주처명], [프로젝트명], [담당자 연락처]

응답은 반드시 유효한 JSON 형식으로 제공해주세요."""

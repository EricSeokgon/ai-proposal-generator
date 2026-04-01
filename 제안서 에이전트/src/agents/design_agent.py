"""
디자인 변환 에이전트 (Stage 5 — 프롬프트 패키지 생성)

Plan JSON + 디자인 레퍼런스 → 슬라이드별 프롬프트 패키지 생성
사용자가 Gemini 웹에서 직접 HTML 제작 (고품질) → html.to.design → Figma
"""

import json
import os
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from .base_agent import BaseAgent
from ..utils.logger import get_logger

logger = get_logger("design_agent")

# 슬라이드 유형별 디자인 가이드
SLIDE_DESIGN_GUIDE = {
    "cover": {
        "desc": "표지",
        "guide": "풀스크린 배경, 대형 타이틀(48~72px), 서브텍스트, 여백 충분히. 브랜드 컬러 강조. 하단에 로고/날짜.",
    },
    "section_divider": {
        "desc": "섹션 구분자",
        "guide": "다크 또는 포인트 컬러 배경, 큰 섹션 번호(01~07), 섹션 제목, 서브텍스트. Win Theme 뱃지.",
    },
    "content": {
        "desc": "일반 콘텐츠",
        "guide": "좌측 정렬 타이틀, 불릿 포인트 또는 카드형 레이아웃. 여백 넉넉히. 하단 출처 표기.",
    },
    "kpi": {
        "desc": "KPI/성과 지표",
        "guide": "대형 숫자(48~72px) + 작은 레이블. 카드 그리드(2×2 또는 1×4). 산출근거 작은 텍스트.",
    },
    "table": {
        "desc": "데이터 테이블",
        "guide": "클린 테이블, 헤더 행 강조(포인트 컬러 배경), 교차 행 배경, 하단 인사이트 박스.",
    },
    "timeline": {
        "desc": "타임라인/로드맵",
        "guide": "수평 타임라인, 단계별 카드, 연결선/화살표. 각 단계 기간+내용.",
    },
    "comparison": {
        "desc": "좌우 비교",
        "guide": "좌측(AS-IS, 회색톤) / 우측(TO-BE, 포인트 컬러). 중앙 화살표. 항목별 대비.",
    },
    "process": {
        "desc": "프로세스 플로우",
        "guide": "수평 또는 수직 플로우, 단계별 아이콘+제목+설명. 화살표 연결.",
    },
    "chart": {
        "desc": "차트/그래프",
        "guide": "차트 영역(60%) + 우측 또는 하단 인사이트 텍스트(40%). 범례 포함.",
    },
    "highlight": {
        "desc": "핵심 메시지 강조",
        "guide": "큰 인용문 스타일 또는 하이라이트 박스. 배경색 다르게. 핵심 한 문장 + 부연.",
    },
    "columns": {
        "desc": "다단 컬럼",
        "guide": "2~4단 카드 레이아웃. 각 카드: 아이콘/번호 + 제목 + 본문. 동일 높이. 간격 균등.",
    },
    "closing": {
        "desc": "클로징/감사",
        "guide": "다크 배경, 큰 'Thank You' 텍스트. 연락처 정보. 미니멀하게.",
    },
}

# 테마별 CSS 변수
THEME_CSS = {
    "warm_minimal": {
        "bg": "#F0EBE3", "card_bg": "#F5F2ED", "text": "#2D2D2D",
        "accent": "#B48C64", "secondary": "#8C8273", "teal": "#78826E",
        "radius": "12px", "shadow": "0 2px 8px rgba(0,0,0,0.06)",
    },
    "classic_blue": {
        "bg": "#FFFFFF", "card_bg": "#FAFAFC", "text": "#002C5F",
        "accent": "#E63312", "secondary": "#00AAD2", "teal": "#00A19C",
        "radius": "8px", "shadow": "0 2px 12px rgba(0,44,95,0.08)",
    },
    "forest": {
        "bg": "#EEF2EB", "card_bg": "#F2F5EE", "text": "#233C2D",
        "accent": "#B4783C", "secondary": "#5A8C64", "teal": "#3C7864",
        "radius": "10px", "shadow": "0 2px 8px rgba(35,60,45,0.06)",
    },
    "corporate": {
        "bg": "#F2F4F8", "card_bg": "#F5F7FA", "text": "#192337",
        "accent": "#C85032", "secondary": "#466496", "teal": "#327382",
        "radius": "8px", "shadow": "0 2px 10px rgba(25,35,55,0.08)",
    },
    "mono_black": {
        "bg": "#F5F5F5", "card_bg": "#F8F8F8", "text": "#141414",
        "accent": "#C83C28", "secondary": "#505050", "teal": "#646464",
        "radius": "6px", "shadow": "0 1px 6px rgba(0,0,0,0.08)",
    },
    "soft_purple": {
        "bg": "#F2EEF8", "card_bg": "#F6F3FA", "text": "#3C2D50",
        "accent": "#BE6482", "secondary": "#8264A0", "teal": "#5A8291",
        "radius": "12px", "shadow": "0 2px 10px rgba(60,45,80,0.06)",
    },
}


class DesignAgent(BaseAgent):
    """디자인 에이전트 — 프롬프트 패키지 생성 + Gemini 작업 가이드"""

    async def execute(
        self,
        input_data: Dict[str, Any],
        progress_callback: Optional[Callable] = None,
    ) -> Dict[str, Any]:
        """
        Plan JSON에서 슬라이드별 프롬프트 패키지 생성

        Args:
            input_data: {
                "plan": dict (ProposalPlan),
                "output_dir": str,
                "design_reference": str (optional),
                "design_note": str (optional),
                "theme": str (optional, default "warm_minimal"),
            }

        Returns:
            {
                "prompt_dir": str,
                "design_system_path": str,
                "total_prompts": int,
                "guide_path": str,
            }
        """
        plan = input_data.get("plan", {})
        output_dir = input_data.get("output_dir", "output/design")
        design_reference = input_data.get("design_reference")
        design_note = input_data.get("design_note", "")
        theme = input_data.get("theme", "warm_minimal")

        prompt_dir = os.path.join(output_dir, "prompts")
        html_dir = os.path.join(output_dir, "html")
        os.makedirs(prompt_dir, exist_ok=True)
        os.makedirs(html_dir, exist_ok=True)

        # ── 5a-1: 디자인 시스템 생성 ──
        if progress_callback:
            progress_callback({
                "stage": "design",
                "step": 1,
                "total": 3,
                "message": "디자인 시스템 구성 중...",
            })

        design_system = self._build_design_system(theme, plan, design_note, design_reference)
        ds_path = os.path.join(output_dir, "design_system.json")
        with open(ds_path, "w", encoding="utf-8") as f:
            json.dump(design_system, f, ensure_ascii=False, indent=2)

        # ── 5a-2: 슬라이드별 프롬프트 생성 ──
        if progress_callback:
            progress_callback({
                "stage": "design",
                "step": 2,
                "total": 3,
                "message": "슬라이드별 프롬프트 생성 중...",
            })

        scripts = plan.get("scripts", {}).get("scripts", [])
        layouts = plan.get("layouts", {}).get("assignments", [])
        structure = plan.get("structure", {})

        layout_map = {la.get("slide_index", -1): la for la in layouts}

        total_prompts = 0
        for script in scripts:
            idx = script.get("slide_index", 0)
            layout = layout_map.get(idx, {})
            prompt_text = self._build_slide_prompt(script, layout, design_system, structure)

            prompt_path = os.path.join(prompt_dir, f"slide_{idx:03d}.md")
            with open(prompt_path, "w", encoding="utf-8") as f:
                f.write(prompt_text)
            total_prompts += 1

        # ── 5a-3: 작업 가이드 생성 ──
        if progress_callback:
            progress_callback({
                "stage": "design",
                "step": 3,
                "total": 3,
                "message": "작업 가이드 생성 중...",
            })

        guide_path = os.path.join(output_dir, "DESIGN_GUIDE.md")
        self._write_guide(guide_path, total_prompts, design_system, output_dir)

        logger.info(f"프롬프트 패키지 생성 완료: {total_prompts}개 슬라이드")

        return {
            "prompt_dir": prompt_dir,
            "design_system_path": ds_path,
            "total_prompts": total_prompts,
            "guide_path": guide_path,
            "html_dir": html_dir,
        }

    def _build_design_system(
        self, theme: str, plan: Dict, note: str, reference: Optional[str]
    ) -> Dict:
        """디자인 시스템 JSON 구성"""

        css = THEME_CSS.get(theme, THEME_CSS["warm_minimal"]).copy()
        css["theme_name"] = theme
        css["font"] = "Pretendard"
        css["slide_width"] = "1920px"
        css["slide_height"] = "1080px"
        css["design_note"] = note

        # 기획 데이터에서 보강
        plan_design = plan.get("design", {})
        if plan_design.get("colors") and isinstance(plan_design["colors"], dict):
            colors = plan_design["colors"]
            if colors.get("primary"):
                css["text"] = colors["primary"]
            if colors.get("accent"):
                css["accent"] = colors["accent"]

        if reference:
            css["reference_path"] = reference

        # Win Themes
        css["win_themes"] = plan.get("structure", {}).get("win_themes", [])

        return css

    def _build_slide_prompt(
        self, script: Dict, layout: Dict, ds: Dict, structure: Dict
    ) -> str:
        """개별 슬라이드 프롬프트 생성"""

        idx = script.get("slide_index", 0)
        stype = script.get("slide_type", "content")
        title = script.get("action_title", "")
        content = script.get("content", {})
        key_msg = script.get("key_message", "")
        win_theme = script.get("win_theme_reference", "")
        layout_name = layout.get("layout_name", "FULL_BODY")
        visual_els = layout.get("visual_elements", [])

        # 슬라이드 유형별 디자인 가이드
        type_guide = SLIDE_DESIGN_GUIDE.get(stype, SLIDE_DESIGN_GUIDE["content"])

        # 콘텐츠 정리
        bullets = content.get("bullets", [])
        bullets_text = ""
        if bullets:
            bullets_text = "\n".join([f"  - {b.get('text', b) if isinstance(b, dict) else b}" for b in bullets[:10]])

        table = content.get("table")
        table_text = ""
        if table:
            table_text = f"\n테이블: {json.dumps(table, ensure_ascii=False)[:500]}"

        return f"""# 슬라이드 {idx + 1}: {title}

## 기본 정보
- **슬라이드 번호**: {idx + 1}
- **유형**: {type_guide['desc']} ({stype})
- **Action Title**: {title}
- **레이아웃**: {layout_name}
- **시각 요소**: {', '.join(visual_els) if visual_els else '없음'}
{f'- **Win Theme**: {win_theme}' if win_theme else ''}
{f'- **핵심 메시지**: {key_msg}' if key_msg else ''}

## 콘텐츠
{bullets_text}
{table_text}

## 디자인 시스템
- 배경색: `{ds.get('bg', '#F0EBE3')}`
- 카드 배경: `{ds.get('card_bg', '#F5F2ED')}`
- 텍스트 컬러: `{ds.get('text', '#2D2D2D')}`
- 포인트 컬러: `{ds.get('accent', '#B48C64')}`
- 보조 컬러: `{ds.get('secondary', '#8C8273')}`
- 폰트: `{ds.get('font', 'Pretendard')}` (Google Fonts)
- 라운드: `{ds.get('radius', '12px')}`
- 그림자: `{ds.get('shadow', '0 2px 8px rgba(0,0,0,0.06)')}`
{f'- 디자인 노트: {ds.get("design_note", "")}' if ds.get('design_note') else ''}

## 디자인 가이드
{type_guide['guide']}

## Gemini 프롬프트

아래를 Gemini에 붙여넣으세요:

---

다음 프레젠테이션 슬라이드를 HTML+CSS로 디자인해주세요.

**슬라이드 크기**: 1920px × 1080px (16:9)
**슬라이드 유형**: {type_guide['desc']}
**제목**: {title}
{f'**핵심 메시지**: {key_msg}' if key_msg else ''}

**콘텐츠**:
{bullets_text if bullets_text else '(위 콘텐츠 참조)'}
{table_text}

**디자인 시스템**:
- 배경: {ds.get('bg')} / 카드: {ds.get('card_bg')}
- 텍스트: {ds.get('text')} / 포인트: {ds.get('accent')} / 보조: {ds.get('secondary')}
- 폰트: Pretendard (https://fonts.googleapis.com/css2?family=Pretendard:wght@300;400;500;600;700&display=swap)
- 라운드: {ds.get('radius')} / 그림자: {ds.get('shadow')}
{f'- 디자인 노트: {ds.get("design_note")}' if ds.get('design_note') else ''}

**디자인 규칙**:
- {type_guide['guide']}
- 여백 충분히 (좌우 100px+, 상하 60px+)
- Behance/Dribbble 수준의 프레젠테이션 디자인
- 완전한 독립 HTML 파일 (인라인 CSS, 외부 의존 없음)
- overflow: hidden (1920×1080 밖으로 나가지 않게)

HTML 코드로 응답해주세요.

---
"""

    def _write_guide(self, path: str, total: int, ds: Dict, output_dir: str) -> None:
        """작업 가이드 문서 생성"""

        with open(path, "w", encoding="utf-8") as f:
            f.write(f"""# 디자인 작업 가이드

## 개요
- 총 {total}장의 슬라이드 프롬프트가 생성되었습니다
- 테마: **{ds.get('theme_name', 'warm_minimal')}**
- 각 프롬프트를 Gemini 웹에서 실행하여 HTML을 생성합니다

## 작업 순서

### Step 1: Gemini 웹 접속
1. https://gemini.google.com 접속
2. Gemini 2.5 Pro 모델 선택 (최고 품질)

### Step 2: 디자인 레퍼런스 공유 (선택)
{f'- 디자인 레퍼런스: `{ds.get("reference_path")}`' if ds.get('reference_path') else '- 디자인 레퍼런스가 없으면 이 단계를 건너뛰세요'}
- 레퍼런스 이미지가 있으면 첫 대화에서 이미지를 첨부하고
  "이 디자인 느낌으로 프레젠테이션 슬라이드를 만들어줘"라고 요청

### Step 3: 슬라이드별 HTML 생성
1. `prompts/slide_000.md` 파일을 열어 "Gemini 프롬프트" 섹션을 복사
2. Gemini에 붙여넣기
3. 생성된 HTML을 `html/slide_000.html`로 저장
4. 브라우저에서 열어 확인
5. 마음에 안 들면 "여기 수정해줘"로 Gemini와 대화하며 수정
6. 다음 슬라이드로 이동

### Step 4: 전체 확인
- 모든 HTML 파일을 브라우저에서 순서대로 확인
- 일관성 체크 (컬러, 폰트, 여백)

### Step 5: Figma JSON 생성 (Puppeteer 렌더링)
1. 터미널에서 figma-plugin 디렉토리로 이동
2. HTML 파일을 Puppeteer로 렌더링하여 정확한 좌표 JSON 생성:
   ```bash
   cd figma-plugin
   node render.js ../projects/[프로젝트명]/output/05_design/html/presentation.html
   ```
3. `presentation.figma.json` 파일이 html/ 폴더에 생성됨

### Step 6: Figma 플러그인으로 임포트
1. Figma 데스크톱 앱에서 **Proposal HTML to Figma** 플러그인 실행
   - Plugins > Development > Proposal HTML to Figma
   - (최초 1회: Plugins > Import plugin from manifest > `figma-plugin/manifest.json` 선택)
2. 생성된 `.figma.json` 파일을 플러그인에 드래그 앤 드롭
3. "Figma로 변환" 클릭 → 모든 슬라이드가 5장씩 행으로 배치됨
4. Figma에서 최종 디테일 수정
   - 간격 미세 조정
   - 실제 이미지/로고 교체
   - 폰트 재확인

## 디자인 시스템

```json
{json.dumps(ds, ensure_ascii=False, indent=2)}
```

## 팁
- 표지/클로징은 가장 마지막에 작업 (전체 톤 확정 후)
- KPI 슬라이드는 숫자 크기를 48~72px로 과감하게
- 연속 3장 이상 같은 레이아웃 금지
- Gemini에게 "이전 슬라이드와 같은 디자인 시스템 유지해줘"라고 요청하면 일관성 유지

## 파일 구조
```
{output_dir}/
├── DESIGN_GUIDE.md          ← 이 파일
├── design_system.json       ← 디자인 시스템
├── prompts/
│   ├── slide_000.md         ← 슬라이드별 프롬프트
│   ├── slide_001.md
│   └── ...
└── html/
    ├── presentation.html    ← 전체 슬라이드 HTML (또는 개별 파일)
    ├── presentation.figma.json  ← Puppeteer 렌더링 결과 (Figma 플러그인 입력)
    ├── slide_000.html
    ├── slide_001.html
    └── ...
```

## Figma 플러그인 위치
```
figma-plugin/
├── manifest.json       ← Figma에서 Import plugin from manifest
├── render.js           ← Puppeteer 렌더링: node render.js input.html
├── src/
│   ├── code.ts         ← Figma 요소 생성
│   ├── ui.ts           ← 플러그인 UI
│   └── ui.html
└── dist/               ← 빌드 결과
```
""")

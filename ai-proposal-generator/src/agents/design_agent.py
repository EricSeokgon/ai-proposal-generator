"""
디자인 변환 에이전트 (Stage 5 — Claude 자동 HTML 생성)

Plan JSON + 디자인 레퍼런스 → 슬라이드별 HTML 자동 생성
Claude API(claude-sonnet-4-6)가 슬라이드 단위로 HTML을 직접 생성한다.
프롬프트 패키지는 백업/추가 수정용으로 함께 저장된다.
HTML → Puppeteer(render.js) → JSON → Figma 플러그인 임포트.
"""

import asyncio
import json
import os
import re
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from .base_agent import BaseAgent
from ..utils.logger import get_logger

logger = get_logger("design_agent")

# Claude HTML 생성에 사용할 모델 (속도/비용/품질 균형)
DESIGN_MODEL = "claude-sonnet-4-6"

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
    """디자인 에이전트 — Claude로 슬라이드별 HTML 자동 생성"""

    async def execute(
        self,
        input_data: Dict[str, Any],
        progress_callback: Optional[Callable] = None,
    ) -> Dict[str, Any]:
        """
        Plan JSON에서 슬라이드별 HTML을 Claude로 자동 생성

        Args:
            input_data: {
                "plan": dict (ProposalPlan),
                "output_dir": str,
                "design_reference": str (optional),
                "design_note": str (optional),
                "theme": str (optional, default "warm_minimal"),
                "concurrency": int (optional, default 4),
            }

        Returns:
            {
                "prompt_dir": str,
                "design_system_path": str,
                "html_dir": str,
                "presentation_html_path": str,
                "total_slides": int,
                "generated_html": int,
                "failed_slides": List[int],
                "guide_path": str,
            }
        """
        plan = input_data.get("plan", {})
        output_dir = input_data.get("output_dir", "output/design")
        design_reference = input_data.get("design_reference")
        design_note = input_data.get("design_note", "")
        theme = input_data.get("theme", "warm_minimal")
        concurrency = max(1, min(8, int(input_data.get("concurrency", 4))))

        prompt_dir = os.path.join(output_dir, "prompts")
        html_dir = os.path.join(output_dir, "html")
        os.makedirs(prompt_dir, exist_ok=True)
        os.makedirs(html_dir, exist_ok=True)

        # ── 5-1: 디자인 시스템 구성 ──
        if progress_callback:
            progress_callback({
                "stage": "design",
                "step": 1,
                "total": 4,
                "message": "디자인 시스템 구성 중...",
            })

        design_system = self._build_design_system(theme, plan, design_note, design_reference)
        ds_path = os.path.join(output_dir, "design_system.json")
        with open(ds_path, "w", encoding="utf-8") as f:
            json.dump(design_system, f, ensure_ascii=False, indent=2)

        # ── 5-2: 슬라이드별 프롬프트 패키지 저장 (백업/수정용) ──
        if progress_callback:
            progress_callback({
                "stage": "design",
                "step": 2,
                "total": 4,
                "message": "슬라이드별 프롬프트 패키지 저장 중...",
            })

        scripts = plan.get("scripts", {}).get("scripts", [])
        layouts = plan.get("layouts", {}).get("assignments", [])
        structure = plan.get("structure", {})
        layout_map = {la.get("slide_index", -1): la for la in layouts}

        slide_jobs: List[Dict[str, Any]] = []
        for script in scripts:
            idx = script.get("slide_index", 0)
            layout = layout_map.get(idx, {})
            prompt_text = self._build_slide_prompt(script, layout, design_system, structure)

            prompt_path = os.path.join(prompt_dir, f"slide_{idx:03d}.md")
            with open(prompt_path, "w", encoding="utf-8") as f:
                f.write(prompt_text)

            slide_jobs.append({
                "index": idx,
                "script": script,
                "layout": layout,
                "prompt_path": prompt_path,
            })

        total_slides = len(slide_jobs)

        # ── 5-3: Claude로 슬라이드별 HTML 생성 (병렬) ──
        if progress_callback:
            progress_callback({
                "stage": "design",
                "step": 3,
                "total": 4,
                "message": f"Claude로 HTML 생성 중... (총 {total_slides}장)",
            })

        generated, failed = await self._generate_all_html(
            slide_jobs, design_system, html_dir, concurrency, progress_callback
        )

        # 전체 묶음 HTML 생성
        presentation_path = os.path.join(html_dir, "presentation.html")
        self._write_presentation_html(html_dir, slide_jobs, presentation_path, design_system)

        # ── 5-4: 작업 가이드 생성 ──
        if progress_callback:
            progress_callback({
                "stage": "design",
                "step": 4,
                "total": 4,
                "message": "작업 가이드 생성 중...",
            })

        guide_path = os.path.join(output_dir, "DESIGN_GUIDE.md")
        self._write_guide(
            guide_path, total_slides, generated, failed, design_system, output_dir
        )

        logger.info(
            f"디자인 단계 완료: 생성 {generated}/{total_slides} (실패 {len(failed)}장)"
        )

        return {
            "prompt_dir": prompt_dir,
            "design_system_path": ds_path,
            "html_dir": html_dir,
            "presentation_html_path": presentation_path,
            "total_slides": total_slides,
            "generated_html": generated,
            "failed_slides": failed,
            "guide_path": guide_path,
        }

    # ────────────────────────────────────────────────
    # HTML 자동 생성 (Claude API)
    # ────────────────────────────────────────────────

    async def _generate_all_html(
        self,
        slide_jobs: List[Dict[str, Any]],
        ds: Dict,
        html_dir: str,
        concurrency: int,
        progress_callback: Optional[Callable],
    ) -> tuple[int, List[int]]:
        """슬라이드별 HTML을 병렬 생성"""
        sem = asyncio.Semaphore(concurrency)
        total = len(slide_jobs)
        done = {"count": 0, "ok": 0}
        failed: List[int] = []

        async def _run(job: Dict[str, Any]) -> None:
            idx = job["index"]
            async with sem:
                try:
                    html = await asyncio.to_thread(
                        self._generate_html_for_slide, job, ds
                    )
                    out_path = os.path.join(html_dir, f"slide_{idx:03d}.html")
                    with open(out_path, "w", encoding="utf-8") as f:
                        f.write(html)
                    done["ok"] += 1
                except Exception as e:
                    logger.error(f"슬라이드 {idx} HTML 생성 실패: {e}")
                    failed.append(idx)
                finally:
                    done["count"] += 1
                    if progress_callback:
                        progress_callback({
                            "stage": "design",
                            "step": 3,
                            "total": 4,
                            "message": f"HTML 생성 진행: {done['count']}/{total}",
                        })

        await asyncio.gather(*[_run(j) for j in slide_jobs])
        return done["ok"], sorted(failed)

    def _generate_html_for_slide(self, job: Dict[str, Any], ds: Dict) -> str:
        """단일 슬라이드 HTML 생성 (Claude API 동기 호출)"""
        script = job["script"]
        layout = job["layout"]
        idx = job["index"]

        stype = script.get("slide_type", "content")
        title = script.get("action_title", "")
        content = script.get("content", {})
        key_msg = script.get("key_message", "")
        win_theme = script.get("win_theme_reference", "")
        layout_name = layout.get("layout_name", "FULL_BODY")
        visual_els = layout.get("visual_elements", [])
        type_guide = SLIDE_DESIGN_GUIDE.get(stype, SLIDE_DESIGN_GUIDE["content"])

        bullets = content.get("bullets", []) or []
        bullets_text = "\n".join(
            f"  - {b.get('text', b) if isinstance(b, dict) else b}"
            for b in bullets[:12]
        )
        table = content.get("table")
        table_text = f"\n테이블: {json.dumps(table, ensure_ascii=False)[:600]}" if table else ""

        system_prompt = self._html_system_prompt(ds)
        user_message = f"""슬라이드 {idx + 1}을 1920x1080 풀스크린 HTML로 디자인해주세요.

## 기본 정보
- 슬라이드 번호: {idx + 1}
- 유형: {type_guide['desc']} ({stype})
- 레이아웃 프리셋: {layout_name}
- 시각 요소: {', '.join(visual_els) if visual_els else '없음'}
{f'- Win Theme: {win_theme}' if win_theme else ''}

## 콘텐츠
- Action Title: {title}
{f'- 핵심 메시지: {key_msg}' if key_msg else ''}
{bullets_text}
{table_text}

## 디자인 규칙
{type_guide['guide']}

## 디자인 시스템 (반드시 준수)
- 배경: {ds.get('bg')} / 카드: {ds.get('card_bg')}
- 텍스트: {ds.get('text')}
- 포인트: {ds.get('accent')} / 보조: {ds.get('secondary')}
- 라운드: {ds.get('radius')} / 그림자: {ds.get('shadow')}
- 폰트: Pretendard
{f'- 디자인 노트: {ds.get("design_note")}' if ds.get('design_note') else ''}

## 출력 형식
- 완전한 단일 HTML 파일 (`<!DOCTYPE html>`부터 `</html>`까지)
- 인라인 CSS만 사용 (외부 의존 없음, Pretendard는 Google Fonts CDN 허용)
- `body`는 정확히 1920x1080, `overflow: hidden`
- 코드 블록(```html ... ```)으로 감싸서 응답
"""
        # 슬라이드 1장 = 약 2~6KB HTML, 8K 토큰이면 충분
        response = self._call_claude_html(system_prompt, user_message, max_tokens=8192)
        return self._extract_html(response)

    def _call_claude_html(
        self, system_prompt: str, user_message: str, max_tokens: int
    ) -> str:
        """디자인 전용 Claude 호출 (Sonnet 4.6 강제)"""
        try:
            message = self.client.messages.create(
                model=DESIGN_MODEL,
                max_tokens=max_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}],
            )
            return message.content[0].text
        except Exception as e:
            # 모델 미지원 등으로 실패 시 기본 모델로 폴백
            logger.warning(f"DESIGN_MODEL({DESIGN_MODEL}) 호출 실패, 기본 모델로 폴백: {e}")
            return self._call_claude(system_prompt, user_message, max_tokens=max_tokens)

    @staticmethod
    def _html_system_prompt(ds: Dict) -> str:
        return f"""당신은 Behance/Dribbble 수준의 프레젠테이션 디자이너입니다.
1920x1080(16:9) 슬라이드 한 장을 완전한 HTML+인라인 CSS로 만듭니다.

## 절대 규칙
- 출력은 단일 HTML 문서 1개. 코드 블록(```html ... ```)으로 감싸기.
- `body`는 width:1920px; height:1080px; overflow:hidden; margin:0; 으로 고정.
- 외부 CSS/JS 라이브러리 금지 (Pretendard Google Fonts CDN만 허용).
- 컬러는 디자인 시스템 값을 그대로 사용. 임의로 변경 금지.
- 텍스트가 1080px를 넘지 않도록 폰트 크기/줄 수 조절.
- 한글 폰트는 반드시 Pretendard. font-weight 400~700 사이.
- 좌우 여백 100px+, 상하 여백 60px+. 카드 간 간격 24px+.
- 이미지 placeholder가 필요하면 `<div>`에 배경/레이블로 표현 (외부 이미지 URL 금지).

## 디자인 시스템
- 배경: {ds.get('bg')} / 카드: {ds.get('card_bg')}
- 텍스트: {ds.get('text')} / 포인트: {ds.get('accent')} / 보조: {ds.get('secondary')}
- 라운드: {ds.get('radius')} / 그림자: {ds.get('shadow')}

## 품질 기준
- 여백, 그리드, 정렬을 의식적으로 사용.
- 한 슬라이드에 핵심 메시지 1개를 시각적으로 가장 크게.
- KPI 숫자는 48~72px로 과감하게.
- 표지/클로징은 풀블리드 배경 가능, 일반 콘텐츠는 흰/카드 배경 위주.
"""

    @staticmethod
    def _extract_html(text: str) -> str:
        """응답에서 HTML 본문 추출"""
        m = re.search(r"```html\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
        if m:
            return m.group(1).strip()
        m = re.search(r"```\s*([\s\S]*?)\s*```", text)
        if m:
            return m.group(1).strip()
        m = re.search(r"<!DOCTYPE[\s\S]*</html>", text, re.IGNORECASE)
        if m:
            return m.group(0).strip()
        return text.strip()

    # ────────────────────────────────────────────────
    # 묶음 HTML / 가이드
    # ────────────────────────────────────────────────

    def _write_presentation_html(
        self,
        html_dir: str,
        slide_jobs: List[Dict[str, Any]],
        out_path: str,
        ds: Dict,
    ) -> None:
        """개별 slide_NNN.html들을 iframe으로 묶은 presentation.html 생성"""
        bg = ds.get("bg", "#F0EBE3")
        sections = []
        for job in slide_jobs:
            idx = job["index"]
            slide_path = f"slide_{idx:03d}.html"
            sections.append(
                f'  <iframe class="slide" src="{slide_path}" '
                f'width="1920" height="1080" frameborder="0" '
                f'loading="lazy" title="Slide {idx + 1}"></iframe>'
            )
        body = "\n".join(sections)

        html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<title>Presentation</title>
<style>
  html, body {{ margin: 0; padding: 0; background: {bg}; }}
  .deck {{ display: flex; flex-direction: column; gap: 24px; padding: 24px; }}
  .slide {{ display: block; width: 1920px; height: 1080px; border: 0; box-shadow: 0 4px 24px rgba(0,0,0,0.08); }}
</style>
</head>
<body>
<div class="deck">
{body}
</div>
</body>
</html>
"""
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html)

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

        plan_design = plan.get("design", {})
        if plan_design.get("colors") and isinstance(plan_design["colors"], dict):
            colors = plan_design["colors"]
            if colors.get("primary"):
                css["text"] = colors["primary"]
            if colors.get("accent"):
                css["accent"] = colors["accent"]

        if reference:
            css["reference_path"] = reference

        css["win_themes"] = plan.get("structure", {}).get("win_themes", [])
        return css

    def _build_slide_prompt(
        self, script: Dict, layout: Dict, ds: Dict, structure: Dict
    ) -> str:
        """프롬프트 패키지(MD) — 백업/수동 수정용"""
        idx = script.get("slide_index", 0)
        stype = script.get("slide_type", "content")
        title = script.get("action_title", "")
        content = script.get("content", {})
        key_msg = script.get("key_message", "")
        win_theme = script.get("win_theme_reference", "")
        layout_name = layout.get("layout_name", "FULL_BODY")
        visual_els = layout.get("visual_elements", [])
        type_guide = SLIDE_DESIGN_GUIDE.get(stype, SLIDE_DESIGN_GUIDE["content"])

        bullets = content.get("bullets", []) or []
        bullets_text = "\n".join(
            f"  - {b.get('text', b) if isinstance(b, dict) else b}"
            for b in bullets[:10]
        )
        table = content.get("table")
        table_text = (
            f"\n테이블: {json.dumps(table, ensure_ascii=False)[:500]}" if table else ""
        )

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
- 배경: `{ds.get('bg')}` / 카드: `{ds.get('card_bg')}`
- 텍스트: `{ds.get('text')}` / 포인트: `{ds.get('accent')}` / 보조: `{ds.get('secondary')}`
- 폰트: `{ds.get('font', 'Pretendard')}` (Google Fonts)
- 라운드: `{ds.get('radius')}` / 그림자: `{ds.get('shadow')}`
{f'- 디자인 노트: {ds.get("design_note", "")}' if ds.get('design_note') else ''}

## 디자인 가이드
{type_guide['guide']}

> 이 파일은 Claude가 자동으로 HTML을 생성하기 위한 입력 사양입니다.
> 자동 생성된 HTML은 같은 디렉토리의 `../html/slide_{idx:03d}.html`에 있습니다.
> 결과가 마음에 들지 않으면 Claude Code에서 다음과 같이 요청하세요:
>   "slide_{idx:03d}.html 다시 디자인해줘 — [수정 요청]"
"""

    def _write_guide(
        self,
        path: str,
        total: int,
        generated: int,
        failed: List[int],
        ds: Dict,
        output_dir: str,
    ) -> None:
        """작업 가이드 문서 생성"""
        failed_str = ", ".join(str(i) for i in failed) if failed else "없음"
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"""# 디자인 작업 가이드 (Claude 자동 생성)

## 개요
- 총 {total}장의 슬라이드 HTML을 Claude로 자동 생성했습니다
- 사용 모델: **{DESIGN_MODEL}**
- 테마: **{ds.get('theme_name', 'warm_minimal')}**
- 생성 성공: **{generated} / {total}장**
- 생성 실패 슬라이드: {failed_str}

## 작업 흐름

```
Plan JSON → DesignAgent(Claude) → HTML → Puppeteer(render.js) → JSON → Figma 플러그인
```

Gemini 웹 복붙 단계가 제거되었습니다. Claude API가 슬라이드 단위로 HTML을 직접 생성합니다.

## 결과 확인

### 1) 브라우저로 미리보기
```
{output_dir}/html/presentation.html
```
모든 슬라이드를 세로로 이어 본 뷰어입니다 (1920×1080 iframe).

개별 슬라이드는 `html/slide_000.html`, `slide_001.html` ... 형태입니다.

### 2) 마음에 안 드는 슬라이드 재생성
Claude Code 세션에서 다음과 같이 요청하세요:

- "slide_005.html 다시 디자인해줘 — KPI 숫자를 더 크게, 카드 4개로"
- "slide_010.html 컬러를 좀 더 다크하게"
- "표지(slide_000)를 풀블리드 이미지 스타일로 다시"

Claude가 `prompts/slide_NNN.md`와 `html/slide_NNN.html`을 읽고 해당 파일을 직접 재작성합니다.

### 3) 실패한 슬라이드 재생성
실패 목록(위)이 있으면 다음 명령으로 재시도:
```
"실패한 슬라이드들 다시 생성해줘"
```

## Figma 임포트

### Step 1: Puppeteer로 Figma JSON 생성
```bash
cd figma-plugin
node render.js ../{output_dir}/html/presentation.html
```
→ `presentation.figma.json`이 같은 폴더에 생성됩니다.

### Step 2: Figma 플러그인 설치 (최초 1회)
1. Figma 데스크톱 앱 실행
2. Plugins > Development > Import plugin from manifest...
3. `figma-plugin/manifest.json` 선택

### Step 3: 임포트 실행
1. Plugins > Development > **Proposal HTML to Figma** 실행
2. 생성된 `.figma.json`을 플러그인 창에 드래그 앤 드롭
3. "Figma로 변환" 클릭 → 5장씩 행으로 자동 배치
4. Figma에서 텍스트/이미지/간격 미세 조정

## 디자인 시스템

```json
{json.dumps(ds, ensure_ascii=False, indent=2)}
```

## 파일 구조
```
{output_dir}/
├── DESIGN_GUIDE.md             ← 이 파일
├── design_system.json          ← 디자인 시스템(컬러/폰트)
├── prompts/                    ← 슬라이드별 입력 사양 (백업/재생성용)
│   ├── slide_000.md
│   └── ...
└── html/                       ← Claude 자동 생성 결과물
    ├── presentation.html       ← 전체 묶음 뷰어
    ├── presentation.figma.json ← (Puppeteer 실행 후) Figma 입력
    ├── slide_000.html
    └── ...
```

## 팁
- 표지/클로징은 가장 마지막에 다시 다듬으면 톤 매칭이 쉽습니다
- KPI 슬라이드는 48~72px 숫자로 과감하게
- 연속 3장 이상 같은 레이아웃은 시각적으로 단조로워집니다
- 실제 이미지/로고는 Figma 임포트 후 교체
""")

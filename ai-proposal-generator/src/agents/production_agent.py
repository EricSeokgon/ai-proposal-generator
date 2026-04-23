"""
제작 에이전트 (Stage 4-1)

ProposalPlan → slide_kit Python 코드 생성 → PPTX 렌더링
"""

import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from .base_agent import BaseAgent
from ..schemas.production_schema import ProductionResult
from ..utils.logger import get_logger

logger = get_logger("production_agent")


class ProductionAgent(BaseAgent):
    """PPTX 제작 에이전트 — slide_kit 코드 생성 + 실행"""

    async def execute(
        self,
        input_data: Dict[str, Any],
        progress_callback: Optional[Callable] = None,
    ) -> ProductionResult:
        """
        ProposalPlan으로부터 PPTX 생성

        Args:
            input_data: {
                "plan": dict (ProposalPlan),
                "output_dir": str,
                "qa_feedback": dict (optional, QAReport — 재생성 시),
            }
        """
        plan = input_data.get("plan", {})
        output_dir = input_data.get("output_dir", "output")
        qa_feedback = input_data.get("qa_feedback")

        if progress_callback:
            progress_callback({
                "stage": "production",
                "step": 1,
                "total": 3,
                "message": "slide_kit 코드 생성 중...",
            })

        # Step 1: slide_kit API 레퍼런스 로드
        slide_kit_ref = self._load_slide_kit_reference()

        # Step 2: Python 코드 생성
        code = await self._generate_code(plan, slide_kit_ref, qa_feedback)

        # Step 3: 스크립트 저장
        os.makedirs(output_dir, exist_ok=True)
        script_path = os.path.join(output_dir, "generate_제안서.py")
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(code)

        if progress_callback:
            progress_callback({
                "stage": "production",
                "step": 2,
                "total": 3,
                "message": "PPTX 렌더링 중...",
            })

        # Step 4: 스크립트 실행
        pptx_path, errors = self._execute_script(script_path, output_dir)

        if progress_callback:
            progress_callback({
                "stage": "production",
                "step": 3,
                "total": 3,
                "message": "제작 완료" if not errors else "제작 완료 (경고 있음)",
            })

        success = pptx_path is not None and os.path.exists(pptx_path)

        logger.info(f"PPTX 제작 {'성공' if success else '실패'}: {pptx_path}")

        return ProductionResult(
            pptx_path=pptx_path or "",
            generation_script_path=script_path,
            slide_count=self._count_slides(pptx_path) if success else 0,
            success=success,
            errors=errors,
        )

    async def _generate_code(
        self, plan: Dict, slide_kit_ref: str, qa_feedback: Optional[Dict] = None
    ) -> str:
        """ProposalPlan → slide_kit Python 코드"""

        system_prompt = self._load_prompt("production")
        if not system_prompt:
            system_prompt = self._get_default_prompt()

        # slide_kit 레퍼런스 추가
        system_prompt += f"\n\n## slide_kit API 레퍼런스\n{slide_kit_ref[:15000]}"

        qa_section = ""
        if qa_feedback:
            qa_section = f"""
## QA 피드백 (이전 생성 결과의 문제점 — 반드시 수정)
{json.dumps(qa_feedback.get('issues', [])[:20], ensure_ascii=False, indent=2)}
"""

        user_message = f"""
## 제안서 기획 데이터

### 구조
{json.dumps(plan.get('structure', {}), ensure_ascii=False, indent=2)[:5000]}

### 스크립트 (슬라이드별 콘텐츠)
{json.dumps(plan.get('scripts', {}), ensure_ascii=False, indent=2)[:10000]}

### 레이아웃 배정
{json.dumps(plan.get('layouts', {}), ensure_ascii=False, indent=2)[:3000]}

### 디자인 기획
{json.dumps(plan.get('design', {}), ensure_ascii=False, indent=2)[:3000]}
{qa_section}

위 기획 데이터를 기반으로 slide_kit.py를 사용하는 Python 스크립트를 생성해주세요.

## 필수 규칙
1. 스크립트 상단에 반드시 PROJECT_ROOT 설정 + `from src.generators.slide_kit import *`
2. 모든 색상은 C["primary"] 등 상수 사용 (하드코딩 금지)
3. 모든 폰트는 FONT 상수 사용 (Pretendard)
4. 겹침/공백 방지 규칙 준수
5. Action Title 사용

완전한 Python 코드만 응답해주세요 (```python ... ``` 블록).
"""

        response = self._call_claude(system_prompt, user_message, max_tokens=16384)

        # 코드 블록 추출
        import re
        code_match = re.search(r"```python\s*([\s\S]*?)\s*```", response)
        if code_match:
            return code_match.group(1)

        code_match = re.search(r"```\s*([\s\S]*?)\s*```", response)
        if code_match:
            return code_match.group(1)

        return response

    def _execute_script(self, script_path: str, output_dir: str) -> tuple:
        """생성된 스크립트 실행"""
        errors = []
        pptx_path = None

        try:
            result = subprocess.run(
                ["python3", script_path],
                capture_output=True,
                text=True,
                timeout=120,
                cwd=os.path.dirname(os.path.dirname(os.path.dirname(script_path))),
            )

            if result.returncode != 0:
                errors.append(f"스크립트 실행 오류: {result.stderr[:1000]}")
                logger.error(f"스크립트 실행 실패: {result.stderr[:500]}")
            else:
                logger.info(f"스크립트 실행 성공: {result.stdout[:200]}")

            # 생성된 PPTX 파일 찾기
            for f in os.listdir(output_dir):
                if f.endswith(".pptx"):
                    pptx_path = os.path.join(output_dir, f)
                    break

        except subprocess.TimeoutExpired:
            errors.append("스크립트 실행 타임아웃 (120초)")
        except Exception as e:
            errors.append(f"스크립트 실행 예외: {str(e)}")

        return pptx_path, errors

    def _load_slide_kit_reference(self) -> str:
        """slide_kit API 레퍼런스 로드"""
        from config.settings import get_settings
        settings = get_settings()
        ref_path = settings.base_dir / "docs" / "slide_kit_reference.md"

        if ref_path.exists():
            return ref_path.read_text(encoding="utf-8")

        return "slide_kit API 레퍼런스를 찾을 수 없습니다."

    def _count_slides(self, pptx_path: Optional[str]) -> int:
        """PPTX 슬라이드 수 확인"""
        if not pptx_path or not os.path.exists(pptx_path):
            return 0
        try:
            from pptx import Presentation
            prs = Presentation(pptx_path)
            return len(prs.slides)
        except Exception:
            return 0

    def _get_default_prompt(self) -> str:
        return """당신은 slide_kit.py API를 사용하여 PPTX 제안서를 생성하는 전문 코드 생성기입니다.
기획 데이터(구조, 스크립트, 레이아웃, 디자인)를 받아 완전한 Python 스크립트를 생성합니다.

## 필수 패턴
```python
#!/usr/bin/env python3
import sys, os
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, PROJECT_ROOT)
from src.generators.slide_kit import *
```

## 금지 사항
- RGBColor 하드코딩 → C["primary"] 사용
- 폰트명 직접 입력 → FONT 상수 사용
- 헬퍼 함수 재정의 금지
- "맑은 고딕" 등 비 Pretendard 폰트 금지"""

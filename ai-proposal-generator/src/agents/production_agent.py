"""
제작 에이전트 (Stage 4-1)

ProposalPlan → slide_kit Python 코드 생성 → PPTX 렌더링
"""

import ast
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from .base_agent import BaseAgent
from ..schemas.production_schema import ProductionResult
from ..utils.logger import get_logger

logger = get_logger("production_agent")


# ────────────────────────────────────────────────
# 생성 스크립트 보안 검증 정책
# ────────────────────────────────────────────────
# 차단 대상 모듈 — 임의 명령 실행/네트워크/직렬화 위험
_BLOCKED_IMPORT_ROOTS = {
    "subprocess", "socket", "ctypes", "ftplib", "telnetlib", "smtplib",
    "pickle", "marshal", "shelve", "multiprocessing", "asyncio.subprocess",
    "urllib", "urllib2", "urllib3", "requests", "httpx", "aiohttp",
    "paramiko", "fabric", "winreg", "_winreg", "msvcrt",
}

# 차단 대상 함수 호출 — 동적 실행/임의 코드 평가
_BLOCKED_CALL_NAMES = {
    "eval", "exec", "compile", "__import__",
    "execfile",  # py2 잔재 — 발견 시 차단
}

# 차단 대상 속성 호출 — os.system / os.popen / shutil.rmtree 등
_BLOCKED_ATTR_CALLS = {
    ("os", "system"), ("os", "popen"), ("os", "execv"), ("os", "execve"),
    ("os", "execvp"), ("os", "execvpe"), ("os", "spawn"), ("os", "spawnv"),
    ("os", "remove"), ("os", "removedirs"), ("os", "unlink"), ("os", "rmdir"),
    ("shutil", "rmtree"), ("shutil", "move"),
    ("pathlib.Path", "unlink"),  # Path().unlink() — 베스트 에포트
}


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
            qa_section = self._format_qa_feedback(qa_feedback)

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

    @staticmethod
    def _format_qa_feedback(qa_feedback: Dict) -> str:
        """QA 피드백을 우선순위 정렬 + 카테고리 요약으로 포맷팅.

        - severity 정렬: critical(0) → warning(1) → info(2) → unknown(3)
        - 상위 20개만 전달 (critical 누락 방지)
        - 카운트 메타와 통과 여부를 헤더에 노출
        """
        issues = qa_feedback.get("issues", []) or []

        severity_rank = {"critical": 0, "warning": 1, "info": 2}
        sorted_issues = sorted(
            issues,
            key=lambda x: severity_rank.get(str(x.get("severity", "")).lower(), 3),
        )[:20]

        meta_lines = [
            f"- 통과 여부: {'PASS' if qa_feedback.get('passed') else 'FAIL'}",
            f"- 총 이슈: {qa_feedback.get('total_issues', len(issues))}건",
            f"- Critical: {qa_feedback.get('critical_count', 0)}건",
            f"- Warning: {qa_feedback.get('warning_count', 0)}건",
            f"- Info: {qa_feedback.get('info_count', 0)}건",
        ]
        summary = qa_feedback.get("summary")
        if summary:
            meta_lines.append(f"- 요약: {summary}")

        return (
            "\n## QA 피드백 (이전 생성 결과의 문제점 — Critical 우선 수정)\n"
            + "\n".join(meta_lines)
            + "\n\n### 우선순위 정렬된 이슈 (상위 20건)\n"
            + json.dumps(sorted_issues, ensure_ascii=False, indent=2)
            + "\n"
        )

    def _execute_script(self, script_path: str, output_dir: str) -> tuple:
        """생성된 스크립트 실행 — AST 보안 검증 후 subprocess로 격리 실행"""
        errors: List[str] = []
        pptx_path = None

        # ── 보안: AST 정적 분석으로 위험 패턴 차단 ──
        try:
            source = Path(script_path).read_text(encoding="utf-8")
        except OSError as e:
            errors.append(f"스크립트 읽기 실패: {e}")
            return None, errors

        violations = self._validate_script_safety(source)
        if violations:
            for v in violations:
                logger.error(f"[보안] 차단: {v}")
            errors.append(
                "보안 검증 실패 — 위험 패턴이 감지되어 실행을 거부했습니다:\n  - "
                + "\n  - ".join(violations)
            )
            return None, errors

        # ── 격리 실행 ──
        # 동일 Python 인터프리터 사용 (Windows에서 python3 누락 회피 + venv 일치 보장)
        # cwd는 PROJECT_ROOT (스크립트 내부 ../../.. 경로 계산과 무관하게 안전)
        try:
            result = subprocess.run(
                [sys.executable, script_path],
                capture_output=True,
                text=True,
                timeout=120,
                cwd=str(self.settings.base_dir),
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

    @staticmethod
    def _validate_script_safety(source: str) -> List[str]:
        """생성 스크립트의 AST를 검사해 위험 패턴 목록 반환 (빈 리스트 = 안전)"""
        violations: List[str] = []

        try:
            tree = ast.parse(source)
        except SyntaxError as e:
            return [f"구문 오류: line {e.lineno}: {e.msg}"]

        for node in ast.walk(tree):
            # 1) import 검사
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root = alias.name.split(".")[0]
                    if root in _BLOCKED_IMPORT_ROOTS:
                        violations.append(
                            f"line {node.lineno}: 차단된 모듈 import: {alias.name}"
                        )
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    root = node.module.split(".")[0]
                    if root in _BLOCKED_IMPORT_ROOTS:
                        violations.append(
                            f"line {node.lineno}: 차단된 모듈 from-import: {node.module}"
                        )

            # 2) 함수 호출 검사
            elif isinstance(node, ast.Call):
                # eval(...), exec(...) 등 직접 호출
                if isinstance(node.func, ast.Name) and node.func.id in _BLOCKED_CALL_NAMES:
                    violations.append(
                        f"line {node.lineno}: 차단된 함수 호출: {node.func.id}()"
                    )
                # os.system(...), shutil.rmtree(...) 등 속성 호출
                elif isinstance(node.func, ast.Attribute):
                    target = ProductionAgent._resolve_attr_chain(node.func)
                    if target:
                        # 마지막 두 토큰만 비교 (예: 'os.system', 'shutil.rmtree')
                        parts = target.split(".")
                        if len(parts) >= 2:
                            tail = (parts[-2], parts[-1])
                            if tail in _BLOCKED_ATTR_CALLS:
                                violations.append(
                                    f"line {node.lineno}: 차단된 속성 호출: {target}()"
                                )

        return violations

    @staticmethod
    def _resolve_attr_chain(node: ast.Attribute) -> Optional[str]:
        """ast.Attribute 체인을 'a.b.c' 문자열로 환원 (실패 시 None)"""
        parts: List[str] = []
        current: ast.AST = node
        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value
        if isinstance(current, ast.Name):
            parts.append(current.id)
            return ".".join(reversed(parts))
        return None

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

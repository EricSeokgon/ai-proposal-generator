"""애플리케이션 설정.

환경변수는 ``Settings()`` 호출 시점에 동적으로 평가된다 (Pydantic v2 ``default_factory``).
이렇게 하면 런타임 환경변수 변경 + 테스트 환경 격리가 모두 지원된다.
"""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field

load_dotenv()


_BASE_DIR = Path(__file__).parent.parent


class Settings(BaseModel):
    """앱 설정"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    # API
    # 모델 ID는 Anthropic 공식 별칭(stable alias)을 사용한다.
    # - claude-sonnet-4-6: 기본 (전 단계 공통)
    # - claude-opus-4-7: 고난도 분석/기획 (옵션)
    # - claude-haiku-4-5: 빠른 보조 작업 (옵션)
    anthropic_api_key: str = Field(
        default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", "")
    )
    claude_model: str = Field(
        default_factory=lambda: os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")
    )
    claude_model_heavy: str = Field(
        default_factory=lambda: os.getenv("CLAUDE_MODEL_HEAVY", "claude-opus-4-7")
    )
    claude_model_fast: str = Field(
        default_factory=lambda: os.getenv("CLAUDE_MODEL_FAST", "claude-haiku-4-5")
    )
    # Stage 5 (DesignAgent) HTML 생성 전용 모델 — 기본은 Sonnet 4.6 (속도/비용 균형)
    claude_model_design: str = Field(
        default_factory=lambda: os.getenv("CLAUDE_MODEL_DESIGN", "claude-sonnet-4-6")
    )
    # DesignAgent 글로벌 타임아웃 (초) — Claude API 다중 호출 안전망
    design_global_timeout_seconds: int = Field(
        default_factory=lambda: int(os.getenv("DESIGN_GLOBAL_TIMEOUT_SECONDS", "1800"))
    )
    max_text_chars: int = Field(
        default_factory=lambda: int(os.getenv("MAX_TEXT_CHARS", "30000"))
    )
    max_rfp_text_chars: int = Field(
        default_factory=lambda: int(os.getenv("MAX_RFP_TEXT_CHARS", "25000"))
    )
    max_tables_chars: int = Field(
        default_factory=lambda: int(os.getenv("MAX_TABLES_CHARS", "5000"))
    )

    # Paths
    base_dir: Path = _BASE_DIR
    templates_dir: Path = _BASE_DIR / "templates"
    prompts_dir: Path = _BASE_DIR / "config" / "prompts"
    company_data_dir: Path = _BASE_DIR / "company_data"
    output_dir: Path = _BASE_DIR / "output"
    input_dir: Path = _BASE_DIR / "input"

    # PPTX Settings
    default_template: str = "base_template"
    slide_width_inches: float = 13.33
    slide_height_inches: float = 7.5

    # 제안서 출력 포맷 (Phase 1)
    # legacy_16_9 / delivery_a4_portrait / presentation_a4_landscape
    proposal_format: str = Field(
        default_factory=lambda: os.getenv("PROPOSAL_FORMAT", "legacy_16_9")
    )


_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """싱글톤 설정 반환"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings

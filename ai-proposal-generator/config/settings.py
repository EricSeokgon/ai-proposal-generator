"""애플리케이션 설정"""

import os
from pathlib import Path
from typing import Optional
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseModel):
    """앱 설정"""

    # API
    # 모델 ID는 Anthropic 공식 별칭(stable alias)을 사용한다.
    # - claude-sonnet-4-6: 기본 (전 단계 공통)
    # - claude-opus-4-7: 고난도 분석/기획 (옵션)
    # - claude-haiku-4-5: 빠른 보조 작업 (옵션)
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    claude_model: str = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")
    claude_model_heavy: str = os.getenv("CLAUDE_MODEL_HEAVY", "claude-opus-4-7")
    claude_model_fast: str = os.getenv("CLAUDE_MODEL_FAST", "claude-haiku-4-5")
    max_text_chars: int = int(os.getenv("MAX_TEXT_CHARS", "30000"))
    max_rfp_text_chars: int = int(os.getenv("MAX_RFP_TEXT_CHARS", "25000"))
    max_tables_chars: int = int(os.getenv("MAX_TABLES_CHARS", "5000"))

    # Paths
    base_dir: Path = Path(__file__).parent.parent
    templates_dir: Path = base_dir / "templates"
    prompts_dir: Path = base_dir / "config" / "prompts"
    company_data_dir: Path = base_dir / "company_data"
    output_dir: Path = base_dir / "output"
    input_dir: Path = base_dir / "input"

    # PPTX Settings
    default_template: str = "base_template"
    slide_width_inches: float = 13.33
    slide_height_inches: float = 7.5

    class Config:
        arbitrary_types_allowed = True


_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """싱글톤 설정 반환"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings

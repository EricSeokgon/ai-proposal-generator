"""공통 픽스처와 경로/환경 설정.

핵심 책임:
1. 프로젝트 루트를 sys.path 에 추가 (config / src 임포트 가능하게)
2. 테스트 환경에서 ``ANTHROPIC_API_KEY`` 가 비어있지 않도록 보장
   — 실제 API 호출은 모킹/생성-검증으로 우회하므로 더미 값으로 충분
"""

import os
import sys
from pathlib import Path

# ── 1. sys.path 설정 ───────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# ── 2. 더미 API 키 (모듈 import 전에 설정해야 settings 평가 시 반영됨) ──
os.environ.setdefault("ANTHROPIC_API_KEY", "test-dummy-key-not-real")


import pytest


@pytest.fixture
def reset_settings_cache():
    """싱글톤 ``Settings`` 인스턴스 캐시를 리셋한다.

    환경변수를 변경하는 테스트 전후에 사용해 격리를 보장한다.
    """
    import config.settings as cs
    original = cs._settings
    cs._settings = None
    try:
        yield
    finally:
        cs._settings = original


@pytest.fixture
def project_root() -> Path:
    """프로젝트 루트 경로를 반환."""
    return PROJECT_ROOT

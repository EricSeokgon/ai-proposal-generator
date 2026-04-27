"""Critical #1 — Claude API 모델 ID 및 settings 환경변수화 검증."""

import os

import pytest


def test_default_model_is_sonnet_4_6(reset_settings_cache, monkeypatch):
    """기본 모델 ID는 Anthropic 공식 별칭 ``claude-sonnet-4-6``."""
    monkeypatch.delenv("CLAUDE_MODEL", raising=False)
    from config.settings import get_settings
    settings = get_settings()
    assert settings.claude_model == "claude-sonnet-4-6"


def test_heavy_and_fast_models_are_set(reset_settings_cache):
    from config.settings import get_settings
    settings = get_settings()
    assert settings.claude_model_heavy == "claude-opus-4-7"
    assert settings.claude_model_fast == "claude-haiku-4-5"


def test_design_model_default(reset_settings_cache):
    from config.settings import get_settings
    settings = get_settings()
    assert settings.claude_model_design == "claude-sonnet-4-6"


def test_design_model_override_via_env(reset_settings_cache, monkeypatch):
    monkeypatch.setenv("CLAUDE_MODEL_DESIGN", "claude-opus-4-7")
    from config.settings import get_settings
    settings = get_settings()
    assert settings.claude_model_design == "claude-opus-4-7"


def test_design_global_timeout_default(reset_settings_cache):
    from config.settings import get_settings
    settings = get_settings()
    assert settings.design_global_timeout_seconds == 1800


def test_design_global_timeout_override(reset_settings_cache, monkeypatch):
    monkeypatch.setenv("DESIGN_GLOBAL_TIMEOUT_SECONDS", "600")
    from config.settings import get_settings
    settings = get_settings()
    assert settings.design_global_timeout_seconds == 600


def test_model_override_via_env(reset_settings_cache, monkeypatch):
    monkeypatch.setenv("CLAUDE_MODEL", "claude-opus-4-7")
    from config.settings import get_settings
    settings = get_settings()
    assert settings.claude_model == "claude-opus-4-7"


def test_text_limits_are_configurable(reset_settings_cache, monkeypatch):
    monkeypatch.setenv("MAX_TEXT_CHARS", "12345")
    monkeypatch.setenv("MAX_RFP_TEXT_CHARS", "6789")
    monkeypatch.setenv("MAX_TABLES_CHARS", "1234")
    from config.settings import get_settings
    settings = get_settings()
    assert settings.max_text_chars == 12345
    assert settings.max_rfp_text_chars == 6789
    assert settings.max_tables_chars == 1234


def test_text_limits_have_sane_defaults(reset_settings_cache, monkeypatch):
    for k in ("MAX_TEXT_CHARS", "MAX_RFP_TEXT_CHARS", "MAX_TABLES_CHARS"):
        monkeypatch.delenv(k, raising=False)
    from config.settings import get_settings
    settings = get_settings()
    assert settings.max_text_chars == 30000
    assert settings.max_rfp_text_chars == 25000
    assert settings.max_tables_chars == 5000

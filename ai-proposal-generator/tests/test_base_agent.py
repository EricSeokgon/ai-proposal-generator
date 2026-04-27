"""Critical #2 (API 키 검증) + Major 3-3 (도메인 카드 합류 확장) 검증."""

import pytest


class _DummyAgent:
    """추상 메서드만 구현한 BaseAgent 서브클래스."""

    @classmethod
    def make(cls, **kw):
        from src.agents.base_agent import BaseAgent

        class Dummy(BaseAgent):
            async def execute(self, *a, **k):
                return None

        return Dummy(**kw)


class TestApiKeyValidation:
    """Critical #2 — API 키 누락/공백 차단."""

    def test_empty_string_raises(self, reset_settings_cache, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "")
        with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
            _DummyAgent.make(api_key="")

    def test_whitespace_only_raises(self, reset_settings_cache, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "   ")
        with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
            _DummyAgent.make(api_key="   ")

    def test_explicit_key_overrides_env(self, reset_settings_cache, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "")
        agent = _DummyAgent.make(api_key="explicit-key")
        assert agent.api_key == "explicit-key"

    def test_env_var_used_when_no_explicit_key(self, reset_settings_cache, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "from-env-key")
        agent = _DummyAgent.make()
        assert agent.api_key == "from-env-key"


class TestPromptDomainMerge:
    """Major 3-3 — 도메인 카드 합류 정책 (PUBLIC vs 비-PUBLIC)."""

    @pytest.fixture
    def agent(self):
        return _DummyAgent.make()

    def test_public_with_domain_merges_all(self, agent):
        from config.proposal_types import ProposalType, PublicDomain
        result = agent._load_prompt_with_domain(
            "phase4_action",
            proposal_type=ProposalType.PUBLIC,
            public_domain=PublicDomain.AI,
        )
        assert "[부록: config/domains/ai.md]" in result
        assert "[부록: config/public_bidding/evaluation_criteria.md]" in result
        assert "[부록: config/public_bidding/compliance.md]" in result

    def test_non_public_with_domain_merges_only_domain(self, agent):
        from config.proposal_types import ProposalType, PublicDomain
        result = agent._load_prompt_with_domain(
            "phase4_action",
            proposal_type=ProposalType.IT_SYSTEM,
            public_domain=PublicDomain.AI,
        )
        assert "[부록: config/domains/ai.md]" in result
        # 평가기준·컴플라이언스 카드는 PUBLIC 한정 → 미합류
        assert "[부록: config/public_bidding/evaluation_criteria.md]" not in result
        assert "[부록: config/public_bidding/compliance.md]" not in result
        # 비-공공 헤더 사용
        assert "도메인 컨텍스트 — 비-공공" in result

    def test_non_public_no_domain_no_appendix(self, agent):
        from config.proposal_types import ProposalType
        result = agent._load_prompt_with_domain(
            "phase4_action",
            proposal_type=ProposalType.IT_SYSTEM,
            public_domain=None,
        )
        assert "부록" not in result

    def test_public_uses_public_prompt_variant(self, agent):
        """PUBLIC 분기 시 phase4_action_public.txt 본체가 로드돼야 함."""
        from config.proposal_types import ProposalType
        result = agent._load_prompt_with_domain(
            "phase4_action",
            proposal_type=ProposalType.PUBLIC,
            public_domain=None,
        )
        # phase4_action_public.txt 의 특징적 표현
        assert "공공" in result or "ISMS-P" in result or "WBS" in result

    def test_missing_prompt_returns_empty(self, agent):
        result = agent._load_prompt_with_domain(
            "phase999_does_not_exist",
            proposal_type=None,
        )
        assert result == ""


class TestTruncateText:
    """settings 연동된 텍스트 절단."""

    def test_uses_settings_default(self, reset_settings_cache, monkeypatch):
        monkeypatch.setenv("MAX_TEXT_CHARS", "100")
        agent = _DummyAgent.make()
        long_text = "가" * 200
        out = agent._truncate_text(long_text)
        assert len(out) > 100  # 잘림 표식 포함
        assert "텍스트가 잘렸습니다" in out

    def test_explicit_limit_overrides(self, reset_settings_cache):
        agent = _DummyAgent.make()
        out = agent._truncate_text("abcdefg", max_chars=3)
        assert out.startswith("abc")
        assert "잘렸습니다" in out

    def test_short_text_unchanged(self, reset_settings_cache):
        agent = _DummyAgent.make()
        assert agent._truncate_text("short", max_chars=100) == "short"

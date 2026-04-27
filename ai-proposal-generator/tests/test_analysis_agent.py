"""Critical #3 — 공공입찰 신호어 감지 정확도 검증."""

import pytest

from src.agents.analysis_agent import (
    AnalysisAgent,
    PUBLIC_SIGNAL_THRESHOLD,
    PUBLIC_SIGNAL_WEIGHTS,
    PUBLIC_SIGNAL_REGEX_KEYS,
)


class TestSignalWeights:
    """가중치 사전 구성."""

    def test_threshold_value(self):
        assert PUBLIC_SIGNAL_THRESHOLD == 5

    def test_strong_signals_have_high_weight(self):
        for kw in ["나라장터", "조달청", "협상에 의한 계약", "ISMS-P", "KCMVP"]:
            assert PUBLIC_SIGNAL_WEIGHTS[kw] == 3, f"{kw} 는 strong(3점) 이어야 함"

    def test_weak_signals_have_low_weight(self):
        assert PUBLIC_SIGNAL_WEIGHTS["정부"] == 1

    def test_regex_keys_are_subset_of_weights(self):
        """정규식 매칭 키는 모두 weights 사전에 등록돼야 함."""
        assert PUBLIC_SIGNAL_REGEX_KEYS.issubset(PUBLIC_SIGNAL_WEIGHTS.keys())


class TestScorePublicSignals:
    """``_score_public_signals`` 동작."""

    def test_strong_signals_pass_threshold(self):
        score, matched = AnalysisAgent._score_public_signals(
            "나라장터 협상에 의한 계약 ISMS-P"
        )
        assert score >= PUBLIC_SIGNAL_THRESHOLD
        assert len(matched) == 3

    def test_three_weak_to_medium_just_passes(self):
        # 정부(1) + 용역(2) + 공공기관(2) = 5 → 임계값 달성
        score, _ = AnalysisAgent._score_public_signals("정부 용역 공공기관")
        assert score == 5

    def test_isms_p_word_boundary_blocks_false_positive(self):
        """``IST-MS-PASS`` 같은 우연 부분일치는 차단되어야 한다."""
        score, matched = AnalysisAgent._score_public_signals(
            "우리 회사는 IST-MS-PASS 시스템을 개발했다"
        )
        assert score == 0
        assert matched == []

    def test_legitimate_isms_p_matches(self):
        score, matched = AnalysisAgent._score_public_signals(
            "이 회사는 ISMS-P 인증을 보유하고 있다"
        )
        assert score == 3
        assert any("ISMS-P" in m for m in matched)

    def test_marketing_text_scores_zero(self):
        score, _ = AnalysisAgent._score_public_signals(
            "브랜드 캠페인을 위한 SNS 콘텐츠 운영 제안서"
        )
        assert score == 0

    def test_duplicate_keyword_counts_once(self):
        # "나라장터" 가 3번 나와도 한 번만 카운트 (다양성 우선)
        score, matched = AnalysisAgent._score_public_signals(
            "나라장터 나라장터 나라장터"
        )
        assert score == 3  # 3점 × 1회
        assert len([m for m in matched if "나라장터" in m]) == 1

    def test_empty_text_returns_zero(self):
        score, matched = AnalysisAgent._score_public_signals("")
        assert score == 0
        assert matched == []


class TestDetectPublicBidding:
    """``_detect_public_bidding`` 통합 동작."""

    def _make_agent(self):
        # BaseAgent 인스턴스화에는 API 키만 있으면 됨 (실 호출 X)
        from src.agents.analysis_agent import AnalysisAgent
        return AnalysisAgent()

    def test_force_domain_short_circuits(self):
        agent = self._make_agent()
        is_public, domain = agent._detect_public_bidding("", force_domain="cctv")
        from config.proposal_types import PublicDomain
        assert is_public is True
        assert domain == PublicDomain.CCTV

    def test_invalid_force_domain_logs_and_falls_through(self):
        agent = self._make_agent()
        is_public, _ = agent._detect_public_bidding(
            "", force_domain="not_a_real_domain"
        )
        # 잘못된 force_domain 은 무시되고 자동 감지로 진행 → 빈 텍스트라 False
        assert is_public is False

    def test_force_public_returns_true(self):
        agent = self._make_agent()
        is_public, _ = agent._detect_public_bidding(
            "통합관제 CCTV 스마트시티", force_public=True
        )
        assert is_public is True

    def test_low_signal_text_returns_false(self):
        agent = self._make_agent()
        is_public, domain = agent._detect_public_bidding(
            "브랜드 마케팅 SNS 캠페인 운영"
        )
        assert is_public is False
        assert domain is None

    def test_high_signal_text_returns_true(self):
        agent = self._make_agent()
        is_public, _ = agent._detect_public_bidding(
            "나라장터 공고 협상에 의한 계약 ISMS-P 인증 평가기준표"
        )
        assert is_public is True

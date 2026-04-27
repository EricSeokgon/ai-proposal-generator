"""Critical #4 — PublicDomain 매칭 가중치 알고리즘 검증."""

import pytest

from config.proposal_types import (
    PublicDomain,
    PUBLIC_DOMAIN_MATCH_THRESHOLD,
    _keyword_weight,
    detect_public_domain,
    get_domain_card_paths,
)


class TestKeywordWeight:
    """길이 기반 변별력 가중치."""

    @pytest.mark.parametrize(
        "keyword, expected",
        [
            ("AI", 1),            # 2글자 → 우연 일치 가능
            ("DR", 1),
            ("CCTV", 2),          # 4글자 → 중간
            ("ETL", 2),           # 3글자 → 중간
            ("MLOps", 3),         # 5글자 → 높음
            ("K-Cloud 전환", 3),  # 7글자 → 높음
            ("데이터 거버넌스", 3),
            ("스마트시티", 3),
        ],
    )
    def test_weight_by_length(self, keyword, expected):
        assert _keyword_weight(keyword) == expected


class TestDetectPublicDomain:
    """도메인 자동 감지."""

    def test_empty_text_returns_none(self):
        assert detect_public_domain("") is None
        assert detect_public_domain(None) is None

    def test_low_signal_returns_none(self):
        # "빅데이터" 단독 반복은 변별력이 부족해 None 이어야 함
        result = detect_public_domain("빅데이터 빅데이터 빅데이터")
        assert result is None

    def test_cctv_domain_detection(self):
        text = "통합관제 지능형 CCTV 스마트시티 어린이 안전구역"
        assert detect_public_domain(text) == PublicDomain.CCTV

    def test_analytics_domain_detection(self):
        text = "공공데이터 분석 정책 분석 대시보드 시각화 인사이트 도출"
        assert detect_public_domain(text) == PublicDomain.BIGDATA_ANALYTICS

    def test_ai_domain_detection(self):
        text = "LLM 생성형 AI MLOps RAG 챗봇 AI 신뢰성"
        assert detect_public_domain(text) == PublicDomain.AI

    def test_infra_domain_detection(self):
        text = "K-Cloud 전환 가상화 쿠버네티스 망분리 이중화 데이터센터"
        assert detect_public_domain(text) == PublicDomain.INFRA

    def test_data_governance_domain_detection(self):
        text = "데이터 거버넌스 메타데이터 데이터 카탈로그 가명처리 마이데이터"
        assert detect_public_domain(text) == PublicDomain.DATA_GOVERNANCE

    def test_threshold_constant(self):
        """임계값이 상향됐는지 확인 (이전 < 2 → 현재 < 3)."""
        assert PUBLIC_DOMAIN_MATCH_THRESHOLD == 3


class TestDomainCardPaths:
    """공공입찰 카드 합류 헬퍼."""

    def test_public_with_domain_returns_all(self):
        paths = get_domain_card_paths(PublicDomain.AI, include_bidding_cards=True)
        assert "config/public_bidding/evaluation_criteria.md" in paths
        assert "config/public_bidding/compliance.md" in paths
        assert "config/domains/ai.md" in paths

    def test_no_bidding_cards_returns_only_domain(self):
        paths = get_domain_card_paths(PublicDomain.CCTV, include_bidding_cards=False)
        assert paths == ["config/domains/cctv.md"]

    def test_no_domain_returns_only_bidding(self):
        paths = get_domain_card_paths(None, include_bidding_cards=True)
        assert "config/domains" not in " ".join(paths)
        assert len(paths) == 2  # evaluation + compliance

    def test_neither_returns_empty(self):
        paths = get_domain_card_paths(None, include_bidding_cards=False)
        assert paths == []

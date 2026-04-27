"""Major 3-1 — PlanningAgent 슬라이드 수 추정 검증."""

import pytest

from src.agents.planning_agent import PlanningAgent, _DEFAULT_SLIDE_ESTIMATE


class TestEstimateSlideCount:
    """``_estimate_slide_count`` — RFP project_type 기반 추정."""

    @pytest.mark.parametrize(
        "project_type, expected",
        [
            ("marketing_pr", 125),  # (100+150)//2
            ("event",        100),  # (80+120)//2
            ("it_system",    80),   # (60+100)//2
            ("public",       75),   # (60+90)//2
            ("consulting",   65),   # (50+80)//2
            ("general",      65),   # (50+80)//2
        ],
    )
    def test_each_proposal_type(self, project_type, expected):
        n = PlanningAgent._estimate_slide_count({"project_type": project_type})
        assert n == expected

    def test_unknown_type_falls_back_to_general(self):
        n = PlanningAgent._estimate_slide_count({"project_type": "unknown_type"})
        assert n == 65  # GENERAL 평균

    def test_empty_rfp_uses_general(self):
        n = PlanningAgent._estimate_slide_count({})
        assert n == 65

    def test_none_project_type_uses_general(self):
        n = PlanningAgent._estimate_slide_count({"project_type": None})
        assert n == 65

    def test_case_insensitive(self):
        n = PlanningAgent._estimate_slide_count({"project_type": "PUBLIC"})
        assert n == 75

    def test_whitespace_stripped(self):
        n = PlanningAgent._estimate_slide_count({"project_type": "  it_system  "})
        assert n == 80

    def test_no_longer_returns_hardcoded_80(self):
        """이전 결함: 항상 80 반환. 마케팅에는 80이 부적절했음."""
        n = PlanningAgent._estimate_slide_count({"project_type": "marketing_pr"})
        assert n != 80
        assert n == 125

    def test_default_constant_exists(self):
        assert _DEFAULT_SLIDE_ESTIMATE > 0
        assert _DEFAULT_SLIDE_ESTIMATE == 70

    def test_returns_positive_integer(self):
        for ptype in [None, "", "x", "marketing_pr", "public"]:
            n = PlanningAgent._estimate_slide_count({"project_type": ptype})
            assert isinstance(n, int)
            assert n >= 1

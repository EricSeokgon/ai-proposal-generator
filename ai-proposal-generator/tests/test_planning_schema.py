"""F P0-2 — ProposalStructure Field 제약 + StructurePlanner 클램핑 검증."""

import pytest
from pydantic import ValidationError

from src.schemas.planning_schema import (
    ProposalStructure,
    SlideSpec,
    MIN_TOTAL_SLIDES,
    MAX_TOTAL_SLIDES,
)
from src.agents.planning.structure_planner import (
    StructurePlanner,
    _FALLBACK_TOTAL_SLIDES,
)


class TestProposalStructureFieldConstraints:
    """``total_slides`` 범위 강제."""

    def test_minimum_constant(self):
        assert MIN_TOTAL_SLIDES == 20

    def test_maximum_constant(self):
        assert MAX_TOTAL_SLIDES == 300

    def test_valid_total_slides_accepted(self):
        ps = ProposalStructure(total_slides=80, phase_breakdown={0: 5, 4: 30})
        assert ps.total_slides == 80

    def test_below_minimum_rejected(self):
        with pytest.raises(ValidationError):
            ProposalStructure(total_slides=10, phase_breakdown={})

    def test_zero_rejected(self):
        with pytest.raises(ValidationError):
            ProposalStructure(total_slides=0, phase_breakdown={})

    def test_above_maximum_rejected(self):
        with pytest.raises(ValidationError):
            ProposalStructure(total_slides=1000, phase_breakdown={})

    def test_boundary_min(self):
        ps = ProposalStructure(total_slides=MIN_TOTAL_SLIDES, phase_breakdown={})
        assert ps.total_slides == MIN_TOTAL_SLIDES

    def test_boundary_max(self):
        ps = ProposalStructure(total_slides=MAX_TOTAL_SLIDES, phase_breakdown={})
        assert ps.total_slides == MAX_TOTAL_SLIDES


class TestPhaseBreakdownValidator:
    """``phase_breakdown`` 키/값 정합성."""

    def test_valid_breakdown(self):
        ps = ProposalStructure(
            total_slides=80,
            phase_breakdown={0: 5, 1: 3, 2: 10, 4: 30},
        )
        assert ps.phase_breakdown == {0: 5, 1: 3, 2: 10, 4: 30}

    def test_phase_out_of_range_rejected(self):
        with pytest.raises(ValidationError, match="phase 키는 0~7"):
            ProposalStructure(total_slides=80, phase_breakdown={9: 5})

    def test_negative_count_rejected(self):
        with pytest.raises(ValidationError, match="0 이상 정수"):
            ProposalStructure(total_slides=80, phase_breakdown={0: -1})


class TestSlideSpecConstraints:
    def test_valid_slide_spec(self):
        s = SlideSpec(slide_index=0, phase_number=4, topic="t", purpose="p")
        assert s.phase_number == 4

    def test_phase_number_out_of_range_rejected(self):
        with pytest.raises(ValidationError):
            SlideSpec(slide_index=0, phase_number=99, topic="t", purpose="p")

    def test_negative_slide_index_rejected(self):
        with pytest.raises(ValidationError):
            SlideSpec(slide_index=-1, phase_number=0, topic="t", purpose="p")


class TestClampTotalSlides:
    """``StructurePlanner._clamp_total_slides`` — Claude 응답 안전 변환."""

    def _planner(self):
        return StructurePlanner()

    def test_within_range(self):
        assert self._planner()._clamp_total_slides(80) == 80

    def test_below_min_clamps_to_min(self):
        assert self._planner()._clamp_total_slides(5) == MIN_TOTAL_SLIDES

    def test_above_max_clamps_to_max(self):
        assert self._planner()._clamp_total_slides(99999) == MAX_TOTAL_SLIDES

    def test_zero_clamps_to_min(self):
        assert self._planner()._clamp_total_slides(0) == MIN_TOTAL_SLIDES

    def test_negative_clamps_to_min(self):
        assert self._planner()._clamp_total_slides(-50) == MIN_TOTAL_SLIDES

    def test_none_uses_fallback(self):
        assert self._planner()._clamp_total_slides(None) == _FALLBACK_TOTAL_SLIDES

    def test_string_uses_fallback(self):
        assert self._planner()._clamp_total_slides("not a number") == _FALLBACK_TOTAL_SLIDES

    def test_string_number_converts(self):
        # int() 가 "80" 을 80으로 변환 → 정상 처리
        assert self._planner()._clamp_total_slides("80") == 80

    def test_float_truncates(self):
        assert self._planner()._clamp_total_slides(80.7) == 80

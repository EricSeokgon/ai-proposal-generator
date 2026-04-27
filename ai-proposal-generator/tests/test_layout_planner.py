"""F P0-1 — LayoutPlanner 30종 화이트리스트 검증."""

import pytest

from src.agents.planning.layout_planner import (
    LayoutPlanner,
    VALID_LAYOUT_NAMES,
    DEFAULT_LAYOUT,
    _SLIDE_KIT_LAYOUTS_FALLBACK,
)


class TestValidLayoutsConstant:
    """30종 화이트리스트 자체."""

    def test_has_30_layouts(self):
        # slide_kit.py LAYOUTS 와 폴백 모두 30개
        assert len(VALID_LAYOUT_NAMES) == 30
        assert len(_SLIDE_KIT_LAYOUTS_FALLBACK) == 30

    def test_default_layout_in_whitelist(self):
        assert DEFAULT_LAYOUT in VALID_LAYOUT_NAMES

    def test_fallback_matches_slide_kit(self):
        """slide_kit.LAYOUTS 와 폴백 리스트가 동기화되어야 함."""
        try:
            from src.generators.slide_kit import LAYOUTS
            actual = set(LAYOUTS.keys())
            assert actual == set(_SLIDE_KIT_LAYOUTS_FALLBACK), (
                f"slide_kit 추가/제거: {actual ^ set(_SLIDE_KIT_LAYOUTS_FALLBACK)}"
            )
        except ImportError:
            pytest.skip("slide_kit import 불가 (CI 환경)")

    def test_known_layouts_present(self):
        for name in [
            "FULL_BODY", "THREE_COL", "KPI_GRID", "ORG_CHART",
            "GANTT", "TIMELINE_DESC", "PYRAMID_DESC",
        ]:
            assert name in VALID_LAYOUT_NAMES


class TestSanitizeAssignments:
    """``_sanitize_assignments`` — Claude 응답 정합성 강제."""

    def _agent(self):
        return LayoutPlanner()

    def test_valid_layouts_unchanged(self):
        agent = self._agent()
        original = [
            {"slide_index": 0, "layout_name": "THREE_COL", "layout_rationale": "비교", "visual_elements": []},
            {"slide_index": 1, "layout_name": "KPI_GRID",  "layout_rationale": "성과", "visual_elements": []},
        ]
        result = agent._sanitize_assignments(original)
        assert len(result) == 2
        assert result[0]["layout_name"] == "THREE_COL"
        assert result[1]["layout_name"] == "KPI_GRID"
        assert "[자동 폴백" not in result[0]["layout_rationale"]

    def test_invalid_layout_falls_back_to_default(self):
        agent = self._agent()
        original = [
            {"slide_index": 0, "layout_name": "EVIL_LAYOUT", "layout_rationale": "원본", "visual_elements": []},
        ]
        result = agent._sanitize_assignments(original)
        assert result[0]["layout_name"] == DEFAULT_LAYOUT
        assert "[자동 폴백: 'EVIL_LAYOUT' 미정의]" in result[0]["layout_rationale"]
        assert "원본" in result[0]["layout_rationale"]

    def test_missing_layout_name_falls_back(self):
        agent = self._agent()
        original = [{"slide_index": 0, "layout_rationale": "...", "visual_elements": []}]
        result = agent._sanitize_assignments(original)
        assert result[0]["layout_name"] == DEFAULT_LAYOUT

    def test_non_dict_assignment_dropped(self):
        agent = self._agent()
        original = [
            {"slide_index": 0, "layout_name": "FULL_BODY", "layout_rationale": "ok", "visual_elements": []},
            "not a dict",
            None,
            ["also bad"],
        ]
        result = agent._sanitize_assignments(original)
        assert len(result) == 1
        assert result[0]["layout_name"] == "FULL_BODY"

    def test_empty_input(self):
        agent = self._agent()
        assert agent._sanitize_assignments([]) == []

    def test_xss_payload_sanitized(self):
        """악의적 layout_name 입력도 화이트리스트로 차단."""
        agent = self._agent()
        original = [
            {"slide_index": 0, "layout_name": "<script>alert(1)</script>", "layout_rationale": "x", "visual_elements": []},
        ]
        result = agent._sanitize_assignments(original)
        assert result[0]["layout_name"] == DEFAULT_LAYOUT

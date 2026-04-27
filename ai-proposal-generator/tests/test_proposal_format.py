"""ProposalFormat enum + 포맷별 슬라이드 사이즈/페이지 검증."""

import pytest
from pydantic import ValidationError

from config.proposal_types import (
    ProposalFormat,
    PROPOSAL_FORMAT_SPECS,
    get_format_spec,
)
from src.agents.planning_agent import PlanningAgent


class TestProposalFormatEnum:
    def test_three_formats_defined(self):
        values = {f.value for f in ProposalFormat}
        assert values == {
            "legacy_16_9",
            "delivery_a4_portrait",
            "presentation_a4_landscape",
        }

    def test_each_format_has_spec(self):
        for fmt in ProposalFormat:
            spec = PROPOSAL_FORMAT_SPECS[fmt]
            assert "name" in spec
            assert "width_inches" in spec
            assert "height_inches" in spec
            assert "slide_count_range" in spec
            assert "purpose" in spec


class TestFormatSpecValues:
    """각 포맷의 사이즈 + 페이지 범위 검증."""

    def test_legacy_16_9_spec(self):
        spec = PROPOSAL_FORMAT_SPECS[ProposalFormat.LEGACY_16_9]
        assert spec["width_inches"] == 13.333
        assert spec["height_inches"] == 7.5
        assert spec["slide_count_range"] == (70, 140)

    def test_delivery_a4_portrait_spec(self):
        spec = PROPOSAL_FORMAT_SPECS[ProposalFormat.DELIVERY_A4_PORTRAIT]
        # A4 portrait: 210mm × 297mm = 8.27" × 11.69"
        assert spec["width_inches"] == 8.27
        assert spec["height_inches"] == 11.69
        assert spec["slide_count_range"] == (70, 150)
        # 사용자 요구: 70~150장
        lo, hi = spec["slide_count_range"]
        assert lo == 70 and hi == 150

    def test_presentation_a4_landscape_spec(self):
        spec = PROPOSAL_FORMAT_SPECS[ProposalFormat.PRESENTATION_A4_LANDSCAPE]
        # A4 landscape: 297mm × 210mm = 11.69" × 8.27"
        assert spec["width_inches"] == 11.69
        assert spec["height_inches"] == 8.27
        assert spec["slide_count_range"] == (30, 50)
        # 사용자 요구: 30~50장
        lo, hi = spec["slide_count_range"]
        assert lo == 30 and hi == 50

    def test_portrait_taller_than_wide(self):
        spec = PROPOSAL_FORMAT_SPECS[ProposalFormat.DELIVERY_A4_PORTRAIT]
        assert spec["height_inches"] > spec["width_inches"]

    def test_landscape_wider_than_tall(self):
        spec = PROPOSAL_FORMAT_SPECS[ProposalFormat.PRESENTATION_A4_LANDSCAPE]
        assert spec["width_inches"] > spec["height_inches"]


class TestGetFormatSpec:
    """``get_format_spec()`` — 안전 폴백 동작."""

    def test_with_enum(self):
        spec = get_format_spec(ProposalFormat.DELIVERY_A4_PORTRAIT)
        assert spec["name"] == "A4 세로 (납품본)"

    def test_with_string(self):
        spec = get_format_spec("presentation_a4_landscape")
        assert spec["slide_count_range"] == (30, 50)

    def test_none_falls_back_to_legacy(self):
        spec = get_format_spec(None)
        assert spec["width_inches"] == 13.333

    def test_invalid_string_falls_back_to_legacy(self):
        spec = get_format_spec("not_a_real_format")
        assert spec["width_inches"] == 13.333


class TestEstimateSlideCountWithFormat:
    """``PlanningAgent._estimate_slide_count`` — format 우선 처리."""

    def test_delivery_a4_portrait_uses_format_range(self):
        # (70 + 150) // 2 = 110
        n = PlanningAgent._estimate_slide_count(
            {"project_type": "marketing_pr"},  # 정상이면 125장
            proposal_format="delivery_a4_portrait",
        )
        assert n == 110

    def test_presentation_a4_landscape_uses_format_range(self):
        # (30 + 50) // 2 = 40
        n = PlanningAgent._estimate_slide_count(
            {"project_type": "public"},  # 정상이면 75장
            proposal_format="presentation_a4_landscape",
        )
        assert n == 40

    def test_legacy_16_9_uses_format_range_too(self):
        # (70 + 140) // 2 = 105
        n = PlanningAgent._estimate_slide_count(
            {"project_type": "general"},  # 정상이면 65장
            proposal_format="legacy_16_9",
        )
        assert n == 105

    def test_no_format_falls_back_to_project_type(self):
        # format 미지정 → project_type 사용
        n = PlanningAgent._estimate_slide_count(
            {"project_type": "marketing_pr"},
            proposal_format=None,
        )
        assert n == 125  # (100+150)//2

    def test_invalid_format_falls_back_to_legacy(self):
        # 잘못된 format → get_format_spec 이 legacy 반환 → (70+140)//2 = 105
        n = PlanningAgent._estimate_slide_count(
            {"project_type": "general"},
            proposal_format="invalid_format_xyz",
        )
        # 무효한 format도 LEGACY 폴백 → 105
        assert n == 105


class TestSlideKitApplyFormat:
    """``slide_kit.apply_format()`` — globals SW/SH/CW 갱신."""

    def test_apply_legacy_16_9(self):
        from src.generators import slide_kit
        spec = slide_kit.apply_format("legacy_16_9")
        assert spec["width_inches"] == 13.333
        # globals 갱신 검증
        from src.generators.slide_kit import SW, SH
        from pptx.util import Inches
        assert SW == Inches(13.333)
        assert SH == Inches(7.5)

    def test_apply_a4_portrait(self):
        from src.generators import slide_kit
        spec = slide_kit.apply_format("delivery_a4_portrait")
        assert spec["height_inches"] > spec["width_inches"]
        # 적용 후 SW < SH (세로형)
        assert slide_kit.SW < slide_kit.SH
        # 다음 테스트를 위해 16:9 로 복원
        slide_kit.apply_format("legacy_16_9")

    def test_apply_a4_landscape(self):
        from src.generators import slide_kit
        spec = slide_kit.apply_format("presentation_a4_landscape")
        assert spec["width_inches"] > spec["height_inches"]
        assert slide_kit.SW > slide_kit.SH
        slide_kit.apply_format("legacy_16_9")

    def test_apply_unknown_format_falls_back_to_legacy(self):
        from src.generators import slide_kit
        spec = slide_kit.apply_format("unknown_format_xyz")
        assert spec["width_inches"] == 13.333
        slide_kit.apply_format("legacy_16_9")


class TestNewPresentationFormat:
    """``new_presentation(format=...)`` 사이즈 적용."""

    def test_default_no_format(self):
        from src.generators import slide_kit
        # 16:9 복원
        slide_kit.apply_format("legacy_16_9")
        prs = slide_kit.new_presentation()
        from pptx.util import Inches
        assert prs.slide_width == Inches(13.333)
        assert prs.slide_height == Inches(7.5)

    def test_a4_portrait_applied(self):
        from src.generators import slide_kit
        prs = slide_kit.new_presentation(format="delivery_a4_portrait")
        # 세로형 — height > width
        assert prs.slide_height > prs.slide_width
        # 16:9 복원
        slide_kit.apply_format("legacy_16_9")

    def test_a4_landscape_applied(self):
        from src.generators import slide_kit
        prs = slide_kit.new_presentation(format="presentation_a4_landscape")
        # 가로형 — width > height
        assert prs.slide_width > prs.slide_height
        slide_kit.apply_format("legacy_16_9")


class TestSettingsProposalFormat:
    """settings.proposal_format — 환경변수 동적 평가."""

    def test_default_legacy(self, reset_settings_cache, monkeypatch):
        monkeypatch.delenv("PROPOSAL_FORMAT", raising=False)
        from config.settings import get_settings
        settings = get_settings()
        assert settings.proposal_format == "legacy_16_9"

    def test_override_via_env(self, reset_settings_cache, monkeypatch):
        monkeypatch.setenv("PROPOSAL_FORMAT", "delivery_a4_portrait")
        from config.settings import get_settings
        settings = get_settings()
        assert settings.proposal_format == "delivery_a4_portrait"

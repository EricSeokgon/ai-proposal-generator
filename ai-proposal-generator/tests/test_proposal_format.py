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


class TestPhase2LayoutsBuilder:
    """Phase 2 — LAYOUTS 30종이 모든 포맷에서 슬라이드 경계 내."""

    @pytest.mark.parametrize(
        "format_name, expected_w, expected_h",
        [
            ("legacy_16_9", 13.333, 7.5),
            ("delivery_a4_portrait", 8.27, 11.69),
            ("presentation_a4_landscape", 11.69, 8.27),
        ],
    )
    def test_all_zones_within_bounds(self, format_name, expected_w, expected_h):
        from src.generators import slide_kit
        slide_kit.apply_format(format_name)
        layouts = slide_kit.LAYOUTS

        out_of_bounds = []
        for name, layout in layouts.items():
            for zone in layout["zones"]:
                x, y, w, h = zone["x"], zone["y"], zone["w"], zone["h"]
                if (
                    x < -0.01
                    or y < -0.01
                    or x + w > expected_w + 0.01
                    or y + h > expected_h + 0.01
                ):
                    out_of_bounds.append(
                        f"{name}.{zone['id']}: x+w={x + w:.2f}, y+h={y + h:.2f}"
                    )

        # 16:9 복원
        slide_kit.apply_format("legacy_16_9")

        assert not out_of_bounds, (
            f"{format_name}: {len(out_of_bounds)} zone(s) 경계 초과:\n"
            + "\n".join(out_of_bounds[:10])
        )

    def test_layouts_count_36_after_format_change(self):
        """LAYOUTS 36종 (기존 30 + 신규 6) 모두 포맷 변경 후 유지."""
        from src.generators import slide_kit
        for fmt in ["legacy_16_9", "delivery_a4_portrait", "presentation_a4_landscape"]:
            slide_kit.apply_format(fmt)
            assert len(slide_kit.LAYOUTS) == 36, f"{fmt}: LAYOUTS 36종 아님"
        slide_kit.apply_format("legacy_16_9")

    def test_per_format_margins(self):
        from src.generators import slide_kit
        from pptx.util import Inches

        slide_kit.apply_format("legacy_16_9")
        assert slide_kit.ML == Inches(1.2)

        slide_kit.apply_format("delivery_a4_portrait")
        assert slide_kit.ML == Inches(0.6)  # 좁은 슬라이드 → 여백 축소

        slide_kit.apply_format("presentation_a4_landscape")
        assert slide_kit.ML == Inches(0.9)

        slide_kit.apply_format("legacy_16_9")  # 복원

    def test_zone_z_scales_with_height(self):
        from src.generators import slide_kit
        slide_kit.apply_format("delivery_a4_portrait")
        # 11.69 / 7.5 = 1.5587x — Z 의 모든 값이 비례 증가
        assert slide_kit.Z["ct_y"] > 1.1  # 16:9 의 1.1 보다 큼
        assert slide_kit.Z["ct_h"] > 5.4
        slide_kit.apply_format("legacy_16_9")
        # 16:9 복원 시 원래 값
        assert abs(slide_kit.Z["ct_y"] - 1.1) < 0.01

    def test_split_dark_light_no_absolute_coords(self):
        """SPLIT_DARK_LIGHT 가 절대값(1.0/5.0/7.5) 대신 비율 기반."""
        from src.generators import slide_kit
        slide_kit.apply_format("delivery_a4_portrait")
        sdl = slide_kit.LAYOUTS["SPLIT_DARK_LIGHT"]
        # A4 세로(8.27") 에서 zone 들이 경계 내
        for zone in sdl["zones"]:
            assert zone["x"] + zone["w"] <= 8.27 + 0.01, f"SPLIT_DARK_LIGHT.{zone['id']} 경계 초과"
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

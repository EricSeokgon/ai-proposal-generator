"""디자인 시스템 — 10 테마 + 36 LAYOUTS 검증."""

import pytest


# ════════════════════════════════════════════════════════════
# THEMES — 10종 검증
# ════════════════════════════════════════════════════════════

class TestThemes:
    """10 테마 정의 + 일관성."""

    def test_ten_themes_defined(self):
        from src.generators.slide_kit import THEMES
        assert len(THEMES) == 10

    def test_legacy_six_themes_present(self):
        from src.generators.slide_kit import THEMES
        for name in [
            "warm_minimal", "classic_blue", "forest",
            "corporate", "mono_black", "soft_purple",
        ]:
            assert name in THEMES, f"기존 테마 {name} 누락"

    def test_new_four_themes_present(self):
        from src.generators.slide_kit import THEMES
        for name in [
            "sunset_orange", "ocean_teal", "gold_luxury", "arctic_white",
        ]:
            assert name in THEMES, f"신규 테마 {name} 누락"

    def test_each_theme_has_required_keys(self):
        """모든 테마는 14개 컬러 키 + _meta 보유."""
        from src.generators.slide_kit import THEMES
        required_color_keys = {
            "primary", "secondary", "teal", "accent", "dark", "light",
            "white", "gray", "lgray", "green", "orange", "gold",
            "card_bg", "card_border",
        }
        for name, theme in THEMES.items():
            missing = required_color_keys - set(theme.keys())
            assert not missing, f"{name}: 누락 키 {missing}"
            assert "_meta" in theme, f"{name}: _meta 누락"

    def test_each_theme_meta_complete(self):
        """모든 테마 _meta 는 margin/font_hero/font_action/font_body 보유."""
        from src.generators.slide_kit import THEMES
        for name, theme in THEMES.items():
            meta = theme["_meta"]
            for k in ["margin", "font_hero", "font_action", "font_body"]:
                assert k in meta, f"{name}._meta.{k} 누락"

    def test_color_values_are_rgb_tuples(self):
        """컬러 값은 (R,G,B) 0~255 tuple."""
        from src.generators.slide_kit import THEMES
        for name, theme in THEMES.items():
            for key, value in theme.items():
                if key.startswith("_"):
                    continue
                assert isinstance(value, tuple) and len(value) == 3, f"{name}.{key} != RGB tuple"
                for c in value:
                    assert 0 <= c <= 255, f"{name}.{key}={value} 범위 초과"


class TestApplyTheme:
    """``apply_theme()`` — 신규 테마 포함 동작."""

    @pytest.mark.parametrize("theme_name", [
        "warm_minimal", "classic_blue", "forest", "corporate",
        "mono_black", "soft_purple",
        "sunset_orange", "ocean_teal", "gold_luxury", "arctic_white",
    ])
    def test_apply_each_theme(self, theme_name):
        from src.generators import slide_kit
        result = slide_kit.apply_theme(theme_name)
        assert result == theme_name
        # 적용 후 C 가 새 컬러로 갱신
        assert slide_kit.C["primary"] is not None
        # warm_minimal 로 복원
        slide_kit.apply_theme("warm_minimal")

    def test_unknown_theme_raises(self):
        from src.generators import slide_kit
        with pytest.raises(ValueError, match="Unknown theme"):
            slide_kit.apply_theme("not_a_real_theme")


# ════════════════════════════════════════════════════════════
# LAYOUTS — 36종 검증
# ════════════════════════════════════════════════════════════

class TestNewLayouts:
    """신규 6 레이아웃 정의 + 동작."""

    @pytest.mark.parametrize("name", [
        "VERTICAL_STEPS", "TIMELINE_VERTICAL", "HEADLINE_NUMBER",
        "CARD_GRID_6", "AGENDA_TWO_COL", "PRICING_TABLE",
    ])
    def test_new_layout_in_LAYOUTS(self, name):
        from src.generators.slide_kit import LAYOUTS
        assert name in LAYOUTS

    def test_total_count_36(self):
        from src.generators.slide_kit import LAYOUTS
        assert len(LAYOUTS) == 36

    def test_vertical_steps_has_5_zones(self):
        from src.generators.slide_kit import LAYOUTS
        zones = LAYOUTS["VERTICAL_STEPS"]["zones"]
        assert len(zones) == 5

    def test_timeline_vertical_has_8_zones(self):
        """4 단계 × 2 (date+event)"""
        from src.generators.slide_kit import LAYOUTS
        zones = LAYOUTS["TIMELINE_VERTICAL"]["zones"]
        assert len(zones) == 8

    def test_headline_number_has_3_zones(self):
        from src.generators.slide_kit import LAYOUTS
        zones = LAYOUTS["HEADLINE_NUMBER"]["zones"]
        assert len(zones) == 3
        ids = [z["id"] for z in zones]
        assert "big_number" in ids and "headline" in ids and "detail" in ids

    def test_card_grid_6_has_6_zones(self):
        from src.generators.slide_kit import LAYOUTS
        zones = LAYOUTS["CARD_GRID_6"]["zones"]
        assert len(zones) == 6

    def test_agenda_two_col_has_10_zones(self):
        """좌5 + 우5 = 10 항목."""
        from src.generators.slide_kit import LAYOUTS
        zones = LAYOUTS["AGENDA_TWO_COL"]["zones"]
        assert len(zones) == 10

    def test_pricing_table_has_9_zones(self):
        """3 플랜 × 3 (header + price + features)."""
        from src.generators.slide_kit import LAYOUTS
        zones = LAYOUTS["PRICING_TABLE"]["zones"]
        assert len(zones) == 9


class TestNewLayoutsAcrossFormats:
    """신규 6 layout 도 3 포맷 모두에서 경계 내."""

    @pytest.mark.parametrize("format_name, sw, sh", [
        ("legacy_16_9", 13.333, 7.5),
        ("delivery_a4_portrait", 8.27, 11.69),
        ("presentation_a4_landscape", 11.69, 8.27),
    ])
    def test_new_layouts_within_bounds(self, format_name, sw, sh):
        from src.generators import slide_kit
        slide_kit.apply_format(format_name)

        new_layouts = [
            "VERTICAL_STEPS", "TIMELINE_VERTICAL", "HEADLINE_NUMBER",
            "CARD_GRID_6", "AGENDA_TWO_COL", "PRICING_TABLE",
        ]
        for name in new_layouts:
            layout = slide_kit.LAYOUTS[name]
            for zone in layout["zones"]:
                x, y, w, h = zone["x"], zone["y"], zone["w"], zone["h"]
                assert x >= -0.01, f"{format_name}.{name}.{zone['id']}: x={x} < 0"
                assert y >= -0.01, f"{format_name}.{name}.{zone['id']}: y={y} < 0"
                assert x + w <= sw + 0.01, (
                    f"{format_name}.{name}.{zone['id']}: x+w={x + w:.2f} > {sw}"
                )
                assert y + h <= sh + 0.01, (
                    f"{format_name}.{name}.{zone['id']}: y+h={y + h:.2f} > {sh}"
                )

        slide_kit.apply_format("legacy_16_9")  # 복원

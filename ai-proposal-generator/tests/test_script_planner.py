"""G P1-4 — ScriptPlanner JSON 응답 검증 + 폴백 검증."""

import pytest

from src.agents.planning.script_planner import ScriptPlanner


class TestCoerceScriptsList:
    """``_coerce_scripts_list`` — 다양한 응답 형식 정규화."""

    def test_list_passthrough(self):
        data = [{"slide_index": 0}, {"slide_index": 1}]
        assert ScriptPlanner._coerce_scripts_list(data) == data

    def test_dict_with_scripts_key(self):
        data = {"scripts": [{"slide_index": 0}]}
        assert ScriptPlanner._coerce_scripts_list(data) == [{"slide_index": 0}]

    def test_dict_with_slides_key(self):
        data = {"slides": [{"slide_index": 0}]}
        assert ScriptPlanner._coerce_scripts_list(data) == [{"slide_index": 0}]

    def test_dict_with_items_key(self):
        data = {"items": [{"slide_index": 0}]}
        assert ScriptPlanner._coerce_scripts_list(data) == [{"slide_index": 0}]

    def test_unrecognized_dict_returns_empty(self):
        data = {"random_key": "value"}
        assert ScriptPlanner._coerce_scripts_list(data) == []

    def test_string_returns_empty(self):
        assert ScriptPlanner._coerce_scripts_list("not a list") == []

    def test_none_returns_empty(self):
        assert ScriptPlanner._coerce_scripts_list(None) == []

    def test_dict_with_non_list_scripts_key(self):
        # scripts 키는 있지만 list 아닌 경우
        data = {"scripts": "wrong type"}
        assert ScriptPlanner._coerce_scripts_list(data) == []


class TestMakeFallbackScript:
    """단일 폴백 슬라이드 생성."""

    def test_fallback_uses_topic_from_spec(self):
        spec = {"slide_index": 5, "phase_number": 4, "topic": "타겟 분석", "purpose": "p"}
        result = ScriptPlanner._make_fallback_script(spec, phase_num=4)
        assert result["slide_index"] == 5
        assert result["phase_number"] == 4
        assert "[자동 폴백]" in result["action_title"]
        assert "타겟 분석" in result["action_title"]
        assert result["slide_type"] == "content"
        assert result["content"]["bullets"] == []

    def test_fallback_marker_in_messages(self):
        spec = {"slide_index": 0, "phase_number": 0, "topic": "x"}
        result = ScriptPlanner._make_fallback_script(spec, phase_num=0)
        assert "재생성" in result["key_message"]
        assert "재생성" in result["content"]["key_message"]

    def test_fallback_phase_from_arg_if_missing_in_spec(self):
        spec = {"slide_index": 0}
        result = ScriptPlanner._make_fallback_script(spec, phase_num=4)
        assert result["phase_number"] == 4

    def test_fallback_handles_empty_topic(self):
        spec = {"slide_index": 0, "phase_number": 0}
        result = ScriptPlanner._make_fallback_script(spec, phase_num=0)
        assert "콘텐츠 미생성" in result["action_title"]


class TestBuildFallbackScripts:
    """``_build_fallback_scripts`` — specs 전체에 폴백 적용."""

    def test_one_fallback_per_spec(self):
        planner = ScriptPlanner()
        specs = [
            {"slide_index": 0, "phase_number": 4, "topic": "a"},
            {"slide_index": 1, "phase_number": 4, "topic": "b"},
            {"slide_index": 2, "phase_number": 4, "topic": "c"},
        ]
        result = planner._build_fallback_scripts(specs, phase_num=4)
        assert len(result) == 3
        assert [s["slide_index"] for s in result] == [0, 1, 2]
        for s in result:
            assert "[자동 폴백]" in s["action_title"]

    def test_empty_specs_returns_empty(self):
        planner = ScriptPlanner()
        assert planner._build_fallback_scripts([], phase_num=0) == []

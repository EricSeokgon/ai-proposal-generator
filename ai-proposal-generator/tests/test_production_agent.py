"""Critical #5 (AST 보안 검증) + Major 3-5 (QA 피드백 정렬) 검증."""

import pytest

from src.agents.production_agent import ProductionAgent


# ════════════════════════════════════════════════════════════
# Critical #5 — AST 보안 검증
# ════════════════════════════════════════════════════════════

class TestSafeScripts:
    """안전한 코드는 통과해야 한다."""

    def test_minimal_safe_script(self):
        code = """
import sys, os
from pathlib import Path
from src.generators.slide_kit import *
prs = new_presentation()
save_pptx(prs, "output.pptx")
"""
        assert ProductionAgent._validate_script_safety(code) == []

    def test_typical_generated_script(self):
        code = """
import sys, os
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, PROJECT_ROOT)
from src.generators.slide_kit import *
import json

apply_theme("warm_minimal")
prs = new_presentation()
slide_cover(prs, title="제안서", client="발주처")
save_pptx(prs, "output.pptx")
"""
        assert ProductionAgent._validate_script_safety(code) == []

    def test_pathlib_path_usage_allowed(self):
        code = """
from pathlib import Path
p = Path("output").resolve()
print(p)
"""
        assert ProductionAgent._validate_script_safety(code) == []


class TestDangerousScripts:
    """위험 코드는 차단되어야 한다."""

    def test_subprocess_import_blocked(self):
        code = "import subprocess\nsubprocess.run(['ls'])"
        violations = ProductionAgent._validate_script_safety(code)
        assert any("subprocess" in v for v in violations)

    def test_socket_import_blocked(self):
        code = "import socket\ns = socket.socket()"
        violations = ProductionAgent._validate_script_safety(code)
        assert any("socket" in v for v in violations)

    def test_urllib_import_blocked(self):
        code = "from urllib import request\nrequest.urlopen('http://x')"
        violations = ProductionAgent._validate_script_safety(code)
        assert any("urllib" in v for v in violations)

    def test_eval_blocked(self):
        code = "x = eval('1+1')"
        violations = ProductionAgent._validate_script_safety(code)
        assert any("eval" in v for v in violations)

    def test_exec_blocked(self):
        code = 'exec("print(1)")'
        violations = ProductionAgent._validate_script_safety(code)
        assert any("exec" in v for v in violations)

    def test_dunder_import_blocked(self):
        code = '__import__("socket")'
        violations = ProductionAgent._validate_script_safety(code)
        assert any("__import__" in v for v in violations)

    def test_os_system_blocked(self):
        code = 'import os\nos.system("rm -rf /")'
        violations = ProductionAgent._validate_script_safety(code)
        assert any("os.system" in v for v in violations)

    def test_shutil_rmtree_blocked(self):
        code = 'import shutil\nshutil.rmtree("/")'
        violations = ProductionAgent._validate_script_safety(code)
        assert any("shutil.rmtree" in v for v in violations)

    def test_multiple_violations_all_reported(self):
        code = """
import subprocess
import socket
exec("x")
__import__("os")
"""
        violations = ProductionAgent._validate_script_safety(code)
        assert len(violations) >= 4

    def test_syntax_error_reported(self):
        violations = ProductionAgent._validate_script_safety("import os\nos.system(")
        assert len(violations) == 1
        assert "구문 오류" in violations[0]


class TestAttrChainResolution:
    """``_resolve_attr_chain`` 체인 환원."""

    def test_simple_chain(self):
        import ast
        node = ast.parse("os.path.join('a', 'b')", mode="eval").body
        assert isinstance(node, ast.Call)
        # node.func 은 Attribute
        assert ProductionAgent._resolve_attr_chain(node.func) == "os.path.join"

    def test_two_level(self):
        import ast
        node = ast.parse("os.system('x')", mode="eval").body
        assert ProductionAgent._resolve_attr_chain(node.func) == "os.system"


# ════════════════════════════════════════════════════════════
# Major 3-5 — QA 피드백 정렬
# ════════════════════════════════════════════════════════════

class TestFormatQaFeedback:
    """``_format_qa_feedback`` — severity 우선 정렬과 메타 노출."""

    def _mock_qa(self):
        return {
            "passed": False,
            "total_issues": 25,
            "critical_count": 2,
            "warning_count": 8,
            "info_count": 15,
            "summary": "빈 슬라이드 다수",
            "issues": [
                # info 가 앞에 위치 → 단순 [:20] 이면 critical 누락됨
                *[
                    {
                        "slide_index": i,
                        "severity": "info",
                        "category": "placeholder",
                        "description": f"info-{i}",
                        "suggestion": "...",
                    }
                    for i in range(15)
                ],
                *[
                    {
                        "slide_index": i,
                        "severity": "warning",
                        "category": "overlap",
                        "description": f"warn-{i}",
                        "suggestion": "...",
                    }
                    for i in range(8)
                ],
                {
                    "slide_index": 99,
                    "severity": "critical",
                    "category": "structure",
                    "description": "CRITICAL-1",
                    "suggestion": "재제작",
                },
                {
                    "slide_index": 100,
                    "severity": "critical",
                    "category": "structure",
                    "description": "CRITICAL-2",
                    "suggestion": "재제작",
                },
            ],
        }

    def test_critical_issues_included_after_sort(self):
        out = ProductionAgent._format_qa_feedback(self._mock_qa())
        assert "CRITICAL-1" in out
        assert "CRITICAL-2" in out

    def test_critical_appears_before_info(self):
        out = ProductionAgent._format_qa_feedback(self._mock_qa())
        assert out.find("CRITICAL-1") < out.find("info-0")

    def test_critical_appears_before_warning(self):
        out = ProductionAgent._format_qa_feedback(self._mock_qa())
        assert out.find("CRITICAL-1") < out.find("warn-0")

    def test_meta_counts_included(self):
        out = ProductionAgent._format_qa_feedback(self._mock_qa())
        assert "Critical: 2건" in out
        assert "Warning: 8건" in out
        assert "Info: 15건" in out
        assert "총 이슈: 25건" in out

    def test_summary_included(self):
        out = ProductionAgent._format_qa_feedback(self._mock_qa())
        assert "빈 슬라이드 다수" in out

    def test_pass_status_displayed(self):
        passing = {**self._mock_qa(), "passed": True}
        out = ProductionAgent._format_qa_feedback(passing)
        assert "PASS" in out

    def test_only_top_20_included(self):
        """이슈가 25개여도 상위 20개만 노출."""
        out = ProductionAgent._format_qa_feedback(self._mock_qa())
        # critical 2 + warning 8 + info 10 = 20개 (info 5개는 제외)
        assert "info-0" in out
        assert "info-9" in out
        assert "info-10" not in out
        assert "info-14" not in out

    def test_empty_issues_handles_gracefully(self):
        out = ProductionAgent._format_qa_feedback({"passed": True, "issues": []})
        assert "PASS" in out
        assert "Critical: 0건" in out

    def test_unknown_severity_sorted_last(self):
        feedback = {
            "passed": False,
            "issues": [
                {"slide_index": 0, "severity": "weird", "category": "x", "description": "WEIRD-issue", "suggestion": "..."},
                {"slide_index": 1, "severity": "critical", "category": "y", "description": "REAL-critical", "suggestion": "..."},
            ],
        }
        out = ProductionAgent._format_qa_feedback(feedback)
        assert out.find("REAL-critical") < out.find("WEIRD-issue")

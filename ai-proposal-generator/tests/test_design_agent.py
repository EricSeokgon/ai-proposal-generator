"""F P0-4 — DesignAgent output_dir 경로 검증."""

import os
from pathlib import Path

import pytest

from src.agents.design_agent import DesignAgent


class TestResolveSafeOutputDir:
    """``_resolve_safe_output_dir`` — path traversal 차단."""

    def test_relative_path_resolved_under_base(self, project_root):
        out = DesignAgent._resolve_safe_output_dir("output/test")
        # 정규화된 절대 경로
        assert os.path.isabs(out)
        # 프로젝트 루트 아래
        assert Path(out).resolve().is_relative_to(project_root.resolve())

    def test_default_when_empty(self, project_root):
        out = DesignAgent._resolve_safe_output_dir("")
        assert "output" in out  # 기본 'output/design'

    def test_default_when_none(self, project_root):
        out = DesignAgent._resolve_safe_output_dir(None)
        assert "output" in out

    def test_traversal_attempt_resolved(self, project_root):
        """``../../etc`` 같은 상대 traversal 은 정규화 후 절대 경로가 됨."""
        # project_root/../../etc 는 시스템에 따라 /etc 또는 다른 경로
        # 차단되거나 정규화 되어야 함
        try:
            out = DesignAgent._resolve_safe_output_dir("../../../etc")
            # 차단되지 않으면 최소한 절대경로로 정규화돼야 함
            assert os.path.isabs(out)
            # /etc 자체로 향하면 차단되었어야 함 (linux)
            if Path(out).as_posix().startswith("/etc"):
                pytest.fail("/etc 경로가 차단되지 않음")
        except ValueError as e:
            assert "시스템 경로" in str(e)

    @pytest.mark.skipif(os.name != "posix", reason="Linux 전용 테스트")
    def test_etc_blocked_on_linux(self):
        with pytest.raises(ValueError, match="시스템 경로"):
            DesignAgent._resolve_safe_output_dir("/etc/proposal")

    @pytest.mark.skipif(os.name != "posix", reason="Linux 전용 테스트")
    def test_sys_blocked_on_linux(self):
        with pytest.raises(ValueError, match="시스템 경로"):
            DesignAgent._resolve_safe_output_dir("/sys/fs/cgroup")

    @pytest.mark.skipif(os.name != "nt", reason="Windows 전용 테스트")
    def test_windows_path_blocked(self):
        with pytest.raises(ValueError, match="시스템 경로"):
            DesignAgent._resolve_safe_output_dir("C:\\Windows\\System32\\evil")

    def test_absolute_path_under_base_allowed(self, project_root):
        target = str(project_root / "output" / "custom")
        out = DesignAgent._resolve_safe_output_dir(target)
        assert Path(out).resolve().is_relative_to(project_root.resolve())

    def test_returns_string(self):
        out = DesignAgent._resolve_safe_output_dir("output/test")
        assert isinstance(out, str)

    def test_path_object_input(self, project_root):
        """Path 객체로도 처리 가능 (str 강제 변환)."""
        out = DesignAgent._resolve_safe_output_dir(Path("output/test"))
        assert os.path.isabs(out)


class TestBlockedRootsList:
    """차단 시스템 디렉토리 정의."""

    def test_blocked_roots_defined(self):
        assert len(DesignAgent._BLOCKED_OUTPUT_ROOTS) > 0

    def test_includes_etc_and_windows(self):
        # Path("/etc") 는 Windows 에서 "\etc", Linux 에서 "/etc" 로 변환됨
        # → 마지막 컴포넌트로 비교
        names = [Path(r).name for r in DesignAgent._BLOCKED_OUTPUT_ROOTS]
        assert "etc" in names
        # Windows 시스템 디렉토리도 포함
        roots_str = [str(r) for r in DesignAgent._BLOCKED_OUTPUT_ROOTS]
        assert any("Windows" in r for r in roots_str)

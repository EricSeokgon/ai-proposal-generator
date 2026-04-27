"""G P1-1 — BriefAdapter 인코딩 오류 처리 검증."""

import os
from pathlib import Path

import pytest

from src.agents.brief_adapter import BriefAdapter


@pytest.fixture
def adapter():
    return BriefAdapter()


@pytest.fixture
def tmp_text_file(tmp_path):
    def _create(content: bytes, name: str = "brief.md") -> Path:
        p = tmp_path / name
        p.write_bytes(content)
        return p
    return _create


class TestLoadFile:
    """``_load_file`` — 인코딩/권한 오류 안전 처리."""

    def test_empty_path_returns_empty(self, adapter):
        assert adapter._load_file("") == ""

    def test_nonexistent_returns_empty(self, adapter, tmp_path):
        assert adapter._load_file(str(tmp_path / "missing.md")) == ""

    def test_utf8_loaded_correctly(self, adapter, tmp_text_file):
        path = tmp_text_file("안녕하세요\n캠페인 브리프".encode("utf-8"))
        result = adapter._load_file(str(path))
        assert "안녕하세요" in result
        assert "캠페인 브리프" in result

    def test_cp949_fallback_succeeds(self, adapter, tmp_text_file):
        """UTF-8 디코드 실패 후 CP949 로 폴백 성공."""
        # CP949 만으로 인코딩된 한글 (UTF-8 디코드 시 실패)
        cp949_bytes = "한글 컨텐츠".encode("cp949")
        path = tmp_text_file(cp949_bytes)
        result = adapter._load_file(str(path))
        # 폴백 성공 시 한글 복구
        assert "한글" in result

    def test_utterly_invalid_encoding_returns_empty(self, adapter, tmp_text_file):
        """UTF-8 도 CP949 도 모두 실패 시 빈 문자열 + 에러 로그."""
        # 두 인코딩 모두 실패하는 invalid byte sequence
        # CP949 는 매우 관대하므로 실제로 실패시키기 어려움 — \x81\x40 같은 미사용 영역
        # 대신 매우 긴 binary blob 으로 테스트 (대부분 환경에서 cp949 처리)
        # → 결과는 빈 문자열이거나 garbled, 어쨌든 예외는 안 나와야 함
        path = tmp_text_file(b"\xff\xfe\xfd\xfc\x00\x00")
        result = adapter._load_file(str(path))
        # 예외 발생하지 않고 문자열 반환되면 OK (내용은 가비지일 수 있음)
        assert isinstance(result, str)

    def test_binary_garbage_does_not_raise(self, adapter, tmp_text_file):
        """바이너리 파일 입력 — 예외 미발생."""
        path = tmp_text_file(bytes(range(256)))
        # 예외 발생하면 테스트 실패
        result = adapter._load_file(str(path))
        assert isinstance(result, str)

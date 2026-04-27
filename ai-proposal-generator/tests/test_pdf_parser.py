"""F P0-3 — PDFParser 암호화 차단 + 메모리 중복 제거 검증."""

import io
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.parsers.pdf_parser import PDFParser, EncryptedPDFError


class TestEncryptedPdfDetection:
    """암호화된 PDF는 명시적 ``EncryptedPDFError`` 발생."""

    @patch("src.parsers.pdf_parser.pypdf.PdfReader")
    def test_encrypted_pdf_raises(self, mock_reader_cls):
        reader = MagicMock()
        reader.is_encrypted = True
        reader.decrypt.return_value = 0  # 빈 비밀번호 실패
        mock_reader_cls.return_value = reader

        parser = PDFParser()
        with pytest.raises(EncryptedPDFError, match="비밀번호로 보호"):
            parser._verify_not_encrypted(Path("dummy.pdf"))

    @patch("src.parsers.pdf_parser.pypdf.PdfReader")
    def test_unencrypted_pdf_passes(self, mock_reader_cls):
        reader = MagicMock()
        reader.is_encrypted = False
        mock_reader_cls.return_value = reader

        parser = PDFParser()
        parser._verify_not_encrypted(Path("dummy.pdf"))  # no exception

    @patch("src.parsers.pdf_parser.pypdf.PdfReader")
    def test_corrupted_pdf_raises_value_error(self, mock_reader_cls):
        mock_reader_cls.side_effect = Exception("malformed header")

        parser = PDFParser()
        with pytest.raises(ValueError, match="PDF 헤더 파싱 실패"):
            parser._verify_not_encrypted(Path("dummy.pdf"))

    @patch("src.parsers.pdf_parser.pypdf.PdfReader")
    def test_empty_password_decrypt_succeeds(self, mock_reader_cls):
        """빈 비밀번호로 복호화 성공 시 (decrypt() != 0) 통과."""
        reader = MagicMock()
        reader.is_encrypted = True
        reader.decrypt.return_value = 1  # 성공
        mock_reader_cls.return_value = reader

        parser = PDFParser()
        parser._verify_not_encrypted(Path("dummy.pdf"))  # no exception


class TestExtractTablesNoRawData:
    """``raw_data`` 필드 제거로 메모리 중복 방지."""

    @patch("src.parsers.pdf_parser.pdfplumber.open")
    def test_tables_have_no_raw_data_field(self, mock_open):
        """``raw_data`` 키가 출력 dict 에 포함되지 않는지."""
        # Mock pdfplumber: 1 page, 1 table with header + 2 rows
        page = MagicMock()
        page.extract_tables.return_value = [
            [["Col1", "Col2"], ["a", "b"], ["c", "d"]]
        ]
        pdf = MagicMock()
        pdf.pages = [page]
        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=pdf)
        ctx.__exit__ = MagicMock(return_value=False)
        mock_open.return_value = ctx

        tables = PDFParser().extract_tables(Path("dummy.pdf"))
        assert len(tables) == 1
        assert "raw_data" not in tables[0]
        assert tables[0]["headers"] == ["Col1", "Col2"]
        assert tables[0]["rows"] == [["a", "b"], ["c", "d"]]

    @patch("src.parsers.pdf_parser.pdfplumber.open")
    def test_empty_table_skipped(self, mock_open):
        page = MagicMock()
        page.extract_tables.return_value = [None, [["only_header"]]]  # 너무 짧음
        pdf = MagicMock()
        pdf.pages = [page]
        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=pdf)
        ctx.__exit__ = MagicMock(return_value=False)
        mock_open.return_value = ctx

        tables = PDFParser().extract_tables(Path("dummy.pdf"))
        assert tables == []  # 모두 필터링됨


class TestExtractSectionsFromText:
    """텍스트 1회 추출 후 섹션 파싱 — I/O 중복 제거."""

    def test_empty_text_returns_empty_list(self):
        result = PDFParser()._extract_sections_from_text("")
        assert result == []

    def test_korean_section_headers_detected(self):
        text = """제1장 개요
이것은 첫 번째 섹션 본문입니다.

제2장 분석
두 번째 섹션입니다."""
        sections = PDFParser()._extract_sections_from_text(text)
        titles = [s["title"] for s in sections]
        assert any("제1장" in t for t in titles)
        assert any("제2장" in t for t in titles)

    def test_legacy_extract_sections_still_works(self):
        """``_extract_sections(file_path)`` 폴백 호환성 (deprecated)."""
        with patch.object(PDFParser, "extract_text", return_value="제1장 hello\n본문"):
            result = PDFParser()._extract_sections(Path("dummy.pdf"))
            assert len(result) >= 1

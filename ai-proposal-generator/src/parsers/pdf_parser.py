"""PDF 문서 파서"""

from pathlib import Path
from typing import Any, Dict, List, Optional

import pypdf
import pdfplumber

from .base_parser import BaseParser
from ..utils.logger import get_logger

logger = get_logger("pdf_parser")


class EncryptedPDFError(ValueError):
    """암호화된 PDF — 사용자 비밀번호 없이는 파싱 불가."""


class PDFParser(BaseParser):
    """PDF 문서 파서"""

    @property
    def supported_extensions(self) -> List[str]:
        return [".pdf"]

    def parse(self, file_path: Path) -> Dict[str, Any]:
        """
        PDF를 파싱하여 구조화된 데이터 반환.

        암호화된 PDF는 ``EncryptedPDFError`` 를 발생시켜 호출자에게 명시적으로 통보한다.
        텍스트는 1회만 추출(``_extract_sections`` 에서 재사용) 하여 I/O 중복을 막는다.

        Args:
            file_path: PDF 파일 경로

        Returns:
            파싱된 데이터 딕셔너리
        """
        logger.info(f"PDF 파싱 시작: {Path(file_path).name}")

        # 1) 암호화 체크 (DoS 차단) — 미리 예외 처리하여 후속 단계 노이즈 방지
        self._verify_not_encrypted(file_path)

        # 2) 텍스트 1회 추출 → 섹션에서 재사용 (이전: 섹션 추출 시 중복 호출)
        raw_text = self.extract_text(file_path)

        result = {
            "raw_text": raw_text,
            "tables": self.extract_tables(file_path),
            "page_count": self._get_page_count(file_path),
            "metadata": self._extract_metadata(file_path),
            "sections": self._extract_sections_from_text(raw_text),
        }

        logger.info(
            f"PDF 파싱 완료: {len(result['raw_text'])} 문자, "
            f"{len(result['tables'])} 테이블"
        )

        return result

    @staticmethod
    def _verify_not_encrypted(file_path: Path) -> None:
        """암호화된 PDF 사전 차단 — 일관된 ``EncryptedPDFError`` 발생.

        ``pypdf`` 는 암호화 PDF 처리 일관성이 낮아(조용히 빈 텍스트 반환 또는
        ``PdfReadError`` 발생) 명시적으로 검사하고 차단한다.
        """
        try:
            reader = pypdf.PdfReader(file_path)
        except Exception as e:
            # 손상된 PDF 자체 — 호출자에게 명확한 컨텍스트 제공
            raise ValueError(f"PDF 헤더 파싱 실패 (손상 가능): {e}") from e

        if reader.is_encrypted:
            # 빈 비밀번호 시도 (일부 PDF는 빈 키로 보호됨)
            try:
                if reader.decrypt("") == 0:
                    raise EncryptedPDFError(
                        f"PDF '{Path(file_path).name}' 가 비밀번호로 보호되어 있습니다. "
                        f"사전 복호화 후 다시 시도하세요."
                    )
            except Exception as e:
                raise EncryptedPDFError(
                    f"PDF '{Path(file_path).name}' 복호화 실패: {e}"
                ) from e

    def extract_text(self, file_path: Path) -> str:
        """pypdf를 사용한 텍스트 추출"""
        try:
            reader = pypdf.PdfReader(file_path)
            text_parts = []

            for i, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(f"--- 페이지 {i + 1} ---\n{page_text}")

            return "\n\n".join(text_parts)
        except Exception as e:
            logger.error(f"텍스트 추출 실패: {e}")
            return ""

    def extract_tables(self, file_path: Path) -> List[Dict[str, Any]]:
        """pdfplumber를 사용한 테이블 추출.

        메모리 효율: 이전엔 ``raw_data`` (전체 테이블) + ``headers`` + ``rows`` 를
        모두 저장해 같은 데이터가 2배로 메모리에 적재됐다.
        ``raw_data`` 는 제거하고 ``headers``/``rows`` 만 보존한다 — 후속 단계에서
        둘만으로 충분히 재구성 가능하다.
        """
        tables = []

        try:
            with pdfplumber.open(file_path) as pdf:
                for i, page in enumerate(pdf.pages):
                    page_tables = page.extract_tables()

                    for j, table in enumerate(page_tables):
                        if table and len(table) > 1:
                            # 첫 번째 행을 헤더로 처리
                            headers = [
                                str(cell).strip() if cell else ""
                                for cell in table[0]
                            ]
                            rows = [
                                [str(cell).strip() if cell else "" for cell in row]
                                for row in table[1:]
                            ]

                            tables.append(
                                {
                                    "page": i + 1,
                                    "table_index": j,
                                    "headers": headers,
                                    "rows": rows,
                                    # raw_data 제거 — headers/rows 와 중복 (메모리 2배)
                                }
                            )
        except Exception as e:
            logger.error(f"테이블 추출 실패: {e}")

        return tables

    def _get_page_count(self, file_path: Path) -> int:
        """페이지 수 반환"""
        try:
            reader = pypdf.PdfReader(file_path)
            return len(reader.pages)
        except Exception:
            return 0

    def _extract_metadata(self, file_path: Path) -> Dict[str, Any]:
        """메타데이터 추출"""
        try:
            reader = pypdf.PdfReader(file_path)
            if reader.metadata:
                return {
                    "title": reader.metadata.get("/Title", ""),
                    "author": reader.metadata.get("/Author", ""),
                    "subject": reader.metadata.get("/Subject", ""),
                    "creator": reader.metadata.get("/Creator", ""),
                    "creation_date": str(reader.metadata.get("/CreationDate", "")),
                }
        except Exception as e:
            logger.warning(f"메타데이터 추출 실패: {e}")

        return {}

    def _extract_sections(self, file_path: Path) -> List[Dict[str, Any]]:
        """[deprecated] 외부 호환성을 위해 유지 — 내부적으로 텍스트 재추출.

        새 코드는 ``_extract_sections_from_text(text)`` 사용 권장 (I/O 절약).
        """
        return self._extract_sections_from_text(self.extract_text(file_path))

    def _extract_sections_from_text(self, text: str) -> List[Dict[str, Any]]:
        """이미 추출된 텍스트에서 섹션 구조 휴리스틱 분석."""
        sections: List[Dict[str, Any]] = []

        if not text:
            return sections

        lines = text.split("\n")
        current_section = {"title": "시작", "content": [], "level": 0}

        section_patterns = [
            "제1장",
            "제2장",
            "제3장",
            "제4장",
            "제5장",
            "1.",
            "2.",
            "3.",
            "4.",
            "5.",
            "I.",
            "II.",
            "III.",
            "IV.",
            "V.",
            "가.",
            "나.",
            "다.",
            "라.",
            "1)",
            "2)",
            "3)",
        ]

        for line in lines:
            line = line.strip()
            if not line:
                continue

            is_section_header = False
            for pattern in section_patterns:
                if line.startswith(pattern) and len(line) < 100:
                    is_section_header = True
                    break

            if is_section_header:
                if current_section["content"]:
                    sections.append(current_section)
                current_section = {"title": line, "content": [], "level": 1}
            else:
                current_section["content"].append(line)

        if current_section["content"]:
            sections.append(current_section)

        return sections

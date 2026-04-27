"""Claude 기반 에이전트 추상 클래스"""

import json
import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Callable, Dict, Optional

import anthropic

from ..utils.logger import get_logger
from config.settings import get_settings

# 모듈 레벨 폴백 logger (인스턴스 생성 전 import-time 사용)
logger = get_logger("agent")


class BaseAgent(ABC):
    """Claude 기반 에이전트 추상 클래스"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ):
        settings = get_settings()
        self.api_key = (api_key or settings.anthropic_api_key or "").strip()
        if not self.api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY 가 설정되지 않았습니다. "
                "환경변수 ANTHROPIC_API_KEY 를 설정하거나 BaseAgent(api_key=...) 로 전달하세요."
            )
        self.model = model or settings.claude_model
        self.settings = settings
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.prompts_dir = settings.prompts_dir
        self.project_root = settings.base_dir
        # 인스턴스별 logger — 서브클래스 호출 추적 가능 (예: AnalysisAgent → "analysis_agent")
        self.logger = get_logger(self.__class__.__name__)

    @abstractmethod
    async def execute(
        self,
        input_data: Dict[str, Any],
        progress_callback: Optional[Callable] = None,
    ) -> Any:
        """에이전트 실행"""
        pass

    def _call_claude(
        self,
        system_prompt: str,
        user_message: str,
        max_tokens: int = 4096,
    ) -> str:
        """
        Claude API 호출

        Args:
            system_prompt: 시스템 프롬프트
            user_message: 사용자 메시지
            max_tokens: 최대 토큰 수

        Returns:
            Claude 응답 텍스트
        """
        self.logger.debug(f"Claude API 호출 (model: {self.model})")

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}],
            )
            return message.content[0].text
        except Exception as e:
            self.logger.error(f"Claude API 호출 실패: {e}")
            raise

    def _load_prompt(self, prompt_name: str) -> str:
        """
        프롬프트 템플릿 로드

        Args:
            prompt_name: 프롬프트 파일명 (확장자 제외)

        Returns:
            프롬프트 텍스트
        """
        prompt_path = self.prompts_dir / f"{prompt_name}.txt"

        if not prompt_path.exists():
            self.logger.warning(f"프롬프트 파일 없음: {prompt_path}")
            return ""

        return prompt_path.read_text(encoding="utf-8")

    def _load_prompt_with_domain(
        self,
        prompt_name: str,
        proposal_type: Optional[Any] = None,
        public_domain: Optional[Any] = None,
        include_bidding_cards: bool = True,
    ) -> str:
        """공공입찰 분기 프롬프트 + 도메인 카드 + 평가기준 카드 통합 로드

        - ``proposal_type=PUBLIC`` 이면 ``{prompt_name}_public.txt`` 우선,
          없으면 ``{prompt_name}.txt`` 폴백.
        - ``public_domain`` 이 주어지면 해당 도메인 카드(``config/domains/*.md``)를 부록 합류.
          **PUBLIC 이 아니어도 도메인 카드는 합류** (예: IT_SYSTEM + force_domain="ai").
        - 평가기준·컴플라이언스 카드(``include_bidding_cards``)는 **PUBLIC 분기에서만** 합류.
        - 모든 부록은 응답 마지막에 ``## 부록`` 으로 추가.

        Args:
            prompt_name: 프롬프트 파일 베이스명 (예: "phase4_action").
                ``phase{N}_{name}`` 형식이면 PUBLIC 분기에서 ``phase{N}_{name}_public`` 로 라우팅.
            proposal_type: ProposalType enum (옵션)
            public_domain: PublicDomain enum (옵션) — 비-PUBLIC 에서도 도메인 카드만 합류
            include_bidding_cards: 평가기준+컴플라이언스 카드 합류 여부 (PUBLIC 한정)

        Returns:
            합쳐진 system prompt 문자열
        """
        from config.proposal_types import (
            ProposalType,
            get_prompt_file,
            get_domain_card_paths,
        )

        # 1) Phase 프롬프트 본체 로드 (PUBLIC 분기는 prompt_name이 phase{N}_{name} 형식일 때만)
        base_text = ""
        public_prompt_attempted = False
        if proposal_type == ProposalType.PUBLIC and prompt_name.startswith("phase"):
            try:
                phase_num = int(prompt_name[5:].split("_", 1)[0])
                public_prompt_attempted = True
                relative = get_prompt_file(phase_num, ProposalType.PUBLIC)
                base_path = Path(relative)
                if not base_path.is_absolute():
                    base_path = self.project_root / relative
                if base_path.exists():
                    base_text = base_path.read_text(encoding="utf-8")
                    self.logger.debug(f"공공입찰 프롬프트 로드: {base_path.name}")
                else:
                    self.logger.warning(
                        f"공공입찰 프롬프트 부재 → 마케팅 폴백: "
                        f"expected={base_path}, fallback={prompt_name}.txt"
                    )
            except (ValueError, IndexError) as e:
                self.logger.warning(f"phase 번호 추출 실패({prompt_name}): {e} — 마케팅 폴백")

        if not base_text:
            base_text = self._load_prompt(prompt_name)
            if proposal_type == ProposalType.PUBLIC and public_prompt_attempted and base_text:
                self.logger.info(f"PUBLIC 분기에서 마케팅 프롬프트로 폴백: {prompt_name}.txt")

        if not base_text:
            self.logger.error(f"프롬프트 로드 실패: {prompt_name} (PUBLIC 분기={proposal_type==ProposalType.PUBLIC})")
            return ""

        # 2) 부록 카드 합류
        # - 평가기준·컴플라이언스 카드: PUBLIC 분기에서만 합류
        # - 도메인 카드: PUBLIC 외에도 public_domain 이 명시되면 합류
        is_public = proposal_type == ProposalType.PUBLIC
        merge_bidding_cards = is_public and include_bidding_cards
        if not merge_bidding_cards and public_domain is None:
            return base_text

        card_paths = get_domain_card_paths(
            public_domain,
            include_bidding_cards=merge_bidding_cards,
        )
        if not card_paths:
            return base_text

        appendix_header = (
            "# 부록 (자동 합류)" if is_public else "# 부록 (도메인 컨텍스트 — 비-공공)"
        )
        appendix_parts = ["", "", "---", "", appendix_header]
        for rel in card_paths:
            card_path = self.project_root / rel
            if not card_path.exists():
                self.logger.warning(f"도메인 카드 누락: {card_path}")
                continue
            content = card_path.read_text(encoding="utf-8")
            appendix_parts.append("")
            appendix_parts.append(f"## [부록: {rel}]")
            appendix_parts.append("")
            appendix_parts.append(content)

        return base_text + "\n".join(appendix_parts)

    def _extract_json(self, text: str) -> Dict[str, Any]:
        """
        텍스트에서 JSON 추출

        Args:
            text: JSON을 포함한 텍스트

        Returns:
            파싱된 JSON 딕셔너리
        """
        # JSON 블록 찾기 (```json ... ``` 또는 { ... })
        patterns = [
            r"```json\s*([\s\S]*?)\s*```",  # 코드 블록
            r"```\s*([\s\S]*?)\s*```",  # 일반 코드 블록
            r"(\{[\s\S]*\})",  # 중괄호 매칭
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                json_str = match.group(1)
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    continue

        self.logger.error("JSON 추출 실패")
        return {}

    def _truncate_text(self, text: str, max_chars: Optional[int] = None) -> str:
        """텍스트 길이 제한 (None이면 settings.max_text_chars 사용)"""
        limit = max_chars if max_chars is not None else self.settings.max_text_chars
        if len(text) <= limit:
            return text
        return text[:limit] + "\n\n... (텍스트가 잘렸습니다)"

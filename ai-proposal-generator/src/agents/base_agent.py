"""Claude 기반 에이전트 추상 클래스"""

import json
import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Callable, Dict, Optional

import anthropic

from ..utils.logger import get_logger
from config.settings import get_settings

logger = get_logger("agent")


class BaseAgent(ABC):
    """Claude 기반 에이전트 추상 클래스"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ):
        settings = get_settings()
        self.api_key = api_key or settings.anthropic_api_key
        self.model = model or settings.claude_model
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.prompts_dir = settings.prompts_dir

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
        logger.debug(f"Claude API 호출 (model: {self.model})")

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}],
            )
            return message.content[0].text
        except Exception as e:
            logger.error(f"Claude API 호출 실패: {e}")
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
            logger.warning(f"프롬프트 파일 없음: {prompt_path}")
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

        - proposal_type=PUBLIC이면 ``{prompt_name}_public.txt``를 우선,
          없으면 ``{prompt_name}.txt``로 폴백.
        - public_domain이 주어지면 해당 도메인 카드(``config/domains/*.md``)를 부록 합류.
        - include_bidding_cards=True이면 평가기준+컴플라이언스 카드를 항상 합류.
        - 모든 부록은 응답 마지막에 ``## 부록``으로 추가.

        Args:
            prompt_name: 프롬프트 파일 베이스명 (예: "phase4_action").
                ``phase{N}_{name}`` 형식이면 PUBLIC 분기에서 ``phase{N}_{name}_public``로 라우팅.
            proposal_type: ProposalType enum (옵션)
            public_domain: PublicDomain enum (옵션, PUBLIC일 때만 의미 있음)
            include_bidding_cards: 평가기준+컴플라이언스 카드 합류 여부

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
        if proposal_type == ProposalType.PUBLIC and prompt_name.startswith("phase"):
            try:
                phase_num = int(prompt_name[5:].split("_", 1)[0])
                relative = get_prompt_file(phase_num, ProposalType.PUBLIC)
                base_path = Path(relative)
                if not base_path.is_absolute():
                    base_path = self.prompts_dir.parent.parent / relative
                if base_path.exists():
                    base_text = base_path.read_text(encoding="utf-8")
            except (ValueError, IndexError):
                pass

        if not base_text:
            base_text = self._load_prompt(prompt_name)

        if not base_text:
            return ""

        # 2) 부록 카드 합류 (PUBLIC 분기에만 적용)
        if proposal_type != ProposalType.PUBLIC:
            return base_text

        card_paths = get_domain_card_paths(public_domain, include_bidding_cards)
        if not card_paths:
            return base_text

        appendix_parts = ["", "", "---", "", "# 부록 (자동 합류)"]
        project_root = self.prompts_dir.parent.parent
        for rel in card_paths:
            card_path = project_root / rel
            if not card_path.exists():
                logger.warning(f"도메인 카드 누락: {card_path}")
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

        logger.error("JSON 추출 실패")
        return {}

    def _truncate_text(self, text: str, max_chars: int = 30000) -> str:
        """텍스트 길이 제한"""
        if len(text) <= max_chars:
            return text
        return text[:max_chars] + "\n\n... (텍스트가 잘렸습니다)"

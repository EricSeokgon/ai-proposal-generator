"""
분석 에이전트 (Stage 1)

RFP 또는 기획안 문서를 분석하여 구조화된 정보 추출.
공공입찰(나라장터) RFP면 도메인 자동 감지 + 평가기준 정량/정성 분리 + 보안·인증 추출.
"""

import json
from typing import Any, Callable, Dict, Optional

from .base_agent import BaseAgent
from ..schemas.rfp_schema import RFPAnalysis
from ..utils.logger import get_logger

logger = get_logger("analysis_agent")


class AnalysisAgent(BaseAgent):
    """문서 분석 에이전트 — RFP / 기획안 / 공공입찰 RFP 모두 지원"""

    async def execute(
        self,
        input_data: Dict[str, Any],
        progress_callback: Optional[Callable] = None,
    ) -> RFPAnalysis:
        """
        RFP / 기획안 / 공공입찰 RFP 문서 분석

        Args:
            input_data: {
                "raw_text": str,
                "tables": List[Dict],
                "sections": List[Dict],
                "document_type": "rfp" | "plan" (optional, default: "rfp"),
                "force_public": bool (optional, 공공입찰 강제 분기),
                "force_domain": str (optional, "cctv" 등 도메인 강제 지정),
            }

        Returns:
            RFPAnalysis: 분석된 문서 정보 (공공이면 도메인·정량/정성·보안 필드 포함)
        """
        document_type = input_data.get("document_type", "rfp")
        raw_text_full = input_data.get("raw_text", "")

        if progress_callback:
            progress_callback({
                "stage": "analysis",
                "step": 1,
                "total": 4,
                "message": f"{'RFP' if document_type == 'rfp' else '기획안'} 텍스트 준비 중...",
            })

        # ── Step 1: 공공입찰 여부 + 도메인 자동 감지 ──
        is_public, public_domain = self._detect_public_bidding(
            raw_text_full,
            force_public=input_data.get("force_public", False),
            force_domain=input_data.get("force_domain"),
        )

        if is_public:
            logger.info(
                f"공공입찰 분기 활성화: domain={public_domain.value if public_domain else 'unknown'}"
            )

        # ── Step 2: 시스템 프롬프트 로드 (PUBLIC이면 도메인 카드+평가기준 합류) ──
        if progress_callback:
            progress_callback({
                "stage": "analysis",
                "step": 2,
                "total": 4,
                "message": "분석 프롬프트 로드 중...",
            })

        system_prompt = self._build_system_prompt(is_public, public_domain, document_type)

        # ── Step 3: Claude 호출 ──
        if progress_callback:
            progress_callback({
                "stage": "analysis",
                "step": 3,
                "total": 4,
                "message": "Claude 분석 수행 중...",
            })

        raw_text = self._truncate_text(raw_text_full, 25000)
        tables_json = json.dumps(
            input_data.get("tables", [])[:10], ensure_ascii=False, indent=2
        )[:5000]

        user_message = self._build_user_message(
            raw_text, tables_json, is_public, public_domain, document_type
        )

        response = self._call_claude(system_prompt, user_message, max_tokens=10240)

        # ── Step 4: 결과 정리 ──
        if progress_callback:
            progress_callback({
                "stage": "analysis",
                "step": 4,
                "total": 4,
                "message": "분석 결과 정리 중...",
            })

        analysis_data = self._extract_json(response)
        analysis_data.setdefault("project_name", "프로젝트명 미확인")
        analysis_data.setdefault("client_name", "발주처 미확인")
        analysis_data.setdefault("project_overview", "")

        if is_public:
            analysis_data["project_type"] = "public"
            if public_domain and not analysis_data.get("public_domain"):
                analysis_data["public_domain"] = public_domain.value

        logger.info(
            f"문서 분석 완료: {analysis_data.get('project_name')} "
            f"(type={analysis_data.get('project_type')}, "
            f"domain={analysis_data.get('public_domain')})"
        )

        return RFPAnalysis(**analysis_data)

    # ────────────────────────────────────────────────
    # 공공입찰 감지·분기 헬퍼
    # ────────────────────────────────────────────────

    def _detect_public_bidding(
        self,
        text: str,
        force_public: bool = False,
        force_domain: Optional[str] = None,
    ):
        """공공입찰 여부 + 도메인 자동 감지"""
        from config.proposal_types import PublicDomain, detect_public_domain

        # 강제 도메인 우선
        if force_domain:
            try:
                return True, PublicDomain(force_domain)
            except ValueError:
                logger.warning(f"force_domain 값 오류: {force_domain}")

        # 강제 공공 분기
        if force_public:
            return True, detect_public_domain(text)

        # 자동 감지 — 공공입찰 신호어
        public_signals = [
            "나라장터", "조달청", "공공기관", "지방자치단체", "지자체",
            "정부", "행정안전부", "행안부", "과기정통부", "기획재정부",
            "협상에 의한 계약", "적격심사", "기술능력평가", "가격평가",
            "평가기준표", "배점", "추정가격", "예정가격",
            "공고번호", "용역", "입찰공고",
            "기술제안서", "정량평가", "정성평가",
            "ISMS-P", "CSAP", "CC인증", "GS인증", "KCMVP",
            "유사실적", "수행실적",
        ]
        text_lower = text.lower() if text else ""
        public_score = sum(1 for sig in public_signals if sig.lower() in text_lower)

        if public_score >= 3:
            return True, detect_public_domain(text)

        return False, None

    def _build_system_prompt(
        self,
        is_public: bool,
        public_domain,
        document_type: str,
    ) -> str:
        """공공입찰이면 도메인 카드+평가기준 합류, 아니면 기본 프롬프트"""
        if is_public:
            base = self._load_prompt("rfp_analysis") or self._load_prompt("analysis")
            if not base:
                base = self._get_default_system_prompt("rfp", is_public=True)

            # 도메인 카드 + 평가기준 + 컴플라이언스 합류
            from config.proposal_types import get_domain_card_paths
            from pathlib import Path

            project_root = self.prompts_dir.parent.parent
            appendix_parts = [base, "", "", "---", "", "# 부록 (자동 합류 — 공공입찰 분기)"]
            for rel in get_domain_card_paths(public_domain, include_bidding_cards=True):
                card_path = project_root / rel
                if card_path.exists():
                    appendix_parts.append("")
                    appendix_parts.append(f"## [부록: {rel}]")
                    appendix_parts.append("")
                    appendix_parts.append(card_path.read_text(encoding="utf-8"))
                else:
                    logger.warning(f"카드 누락: {card_path}")

            return "\n".join(appendix_parts)

        # 일반(마케팅/이벤트/컨설팅 등) 분기
        base = self._load_prompt("analysis")
        if not base:
            base = self._get_default_system_prompt(document_type, is_public=False)
        return base

    def _build_user_message(
        self,
        raw_text: str,
        tables_json: str,
        is_public: bool,
        public_domain,
        document_type: str,
    ) -> str:
        """공공입찰이면 정량/정성·보안·인증 필드 추가 추출 요청"""
        doc_label = "공공입찰 RFP(제안요청서)" if is_public else (
            "RFP(제안요청서)" if document_type == "rfp" else "기획안"
        )

        common_fields = """
        "project_name": "프로젝트명",
        "client_name": "발주처명 (정확히)",
        "project_overview": "프로젝트 개요 (2-3문장)",
        "project_type": "marketing_pr / event / it_system / public / consulting / general 중 택1",
        "key_requirements": [{"category": "기능/비기능/기술/관리", "requirement": "...", "priority": "필수/선택"}],
        "technical_requirements": [{"category": "기술", "requirement": "...", "priority": "필수/선택"}],
        "evaluation_criteria": [{"category": "분야", "item": "평가 항목", "weight": 배점숫자}],
        "deliverables": [{"name": "산출물명", "phase": "단계", "description": "..."}],
        "timeline": {"total_duration": "...", "phases": [{"name": "...", "duration": "..."}]},
        "budget": {"total_budget": "...", "notes": "..."},
        "key_success_factors": ["..."],
        "potential_risks": ["..."],
        "winning_strategy": "...",
        "differentiation_points": ["..."],
        "pain_points": ["발주처 핵심 고민 1", "..."],
        "hidden_needs": ["..."],
        "evaluation_strategy": {
            "high_weight_items": [{"item": "...", "weight": 30, "proposal_emphasis": "..."}],
            "emphasis_mapping": {"Phase 2 (INSIGHT)": "...", "Phase 4 (ACTION)": "...", "Phase 6 (WHY US)": "..."}
        },
        "win_theme_candidates": [{"name": "...", "rationale": "...", "rfp_alignment": "..."}],
        "competitive_landscape": "..."
"""

        public_fields = ""
        domain_hint = ""
        if is_public:
            domain_hint = (
                f"\n도메인 자동 감지 결과: **{public_domain.value if public_domain else '미확인'}**"
                "\n해당 도메인 카드(부록 참조)의 정책·아키텍처·KPI·인증 정보를 적극 활용해 분석을 보강하세요.\n"
            )
            public_fields = """,
        "public_domain": "bigdata_build/bigdata_maintenance/bigdata_analytics/bigdata_modernization/ai/infra/cctv/data_governance 중 택1",
        "bidding_method": "협상에 의한 계약 / 적격심사 / 일반경쟁 / 수의계약 / 제한경쟁 중 택1",
        "quantitative_criteria": [{"category": "가격/수행기간/인력", "item": "...", "weight": 배점}],
        "qualitative_criteria": [{"category": "기술/실적/보안/관리", "item": "...", "weight": 배점}],
        "security_requirements": ["망분리 (행망/일반망 물리)", "ISMS-P 보유", "KCMVP 검증 암호 모듈", "..."],
        "required_certifications": ["ISMS-P", "CSAP 中급+", "CMMI Lvl.3+", "GS인증", "..."],
        "eligibility_requirements": ["소프트웨어 사업자 신고증", "정보통신공사업 N등급+", "신용평가 BB+ 이상", "유사실적 5건+"],
        "similar_performance_requirements": {
            "period_years": 5,
            "min_contract_amount": "5억",
            "min_count": 3,
            "domain_match": "동일/유사 도메인"
        },
        "estimated_price": "추정가격 (RFP 명시 — 예: '15억(부가세 포함)')",
        "contract_period": "계약 기간 (예: '12개월' 또는 '36개월 (운영)')"
"""

        return f"""다음 {doc_label} 문서를 분석해주세요.{domain_hint}

## 문서 텍스트
{raw_text}

## 테이블 데이터
{tables_json}

위 내용을 분석하여 다음 JSON 형식으로 응답해주세요:

```json
{{{common_fields}{public_fields}
}}
```
"""

    def _get_default_system_prompt(self, document_type: str = "rfp", is_public: bool = False) -> str:
        """기본 시스템 프롬프트"""
        doc_label = "RFP" if document_type == "rfp" else "기획안"

        if is_public:
            return f"""당신은 공공입찰(나라장터) 제안서 수주 컨설턴트입니다.
{doc_label}을 심층 분석하여 수주에 필요한 핵심 정보를 추출합니다.

## 공공입찰 분석 영역 (★특화)

### 기본 분석
1. 프로젝트 기본 정보 (이름·발주처·개요·기간·예산)
2. 요구사항 (기능/비기능/기술)
3. 산출물 목록·일정

### 평가 기준 — 정량/정성 분리 ★
4. **정량 평가**: 가격·수행기간·인력·실적 (수치 기반)
5. **정성 평가**: 기술 적합성·수행 방법·보안·관리 (전문가 평가)
6. 배점 분포 → 제안서 강조 포인트 변환

### 공공 특수 항목 ★
7. **입찰 방식**: 협상·적격심사·일반경쟁·수의·제한
8. **추정가격**: 가격 평가 기준
9. **계약 기간**: 단기/장기 (운영 사업 구분)
10. **보안 요구**: 망분리·암호화·ISMS-P·CSAP
11. **필수 인증**: GS·CMMI·CSAP·CC·KCMVP
12. **입찰 자격**: SW사업자·정통공사업·재무·유사실적
13. **유사 실적 요구**: 기간·금액·건수·도메인

### 전략 분석
14. **도메인 분류**: bigdata_*/ai/infra/cctv/data_governance
15. **Pain Point**: 발주처 행간 고민 3~5개
16. **Win Theme**: 정책 부합 + 검증된 운영 + 위험 최소화 3축
17. **숨겨진 니즈**: RFP에 명시되지 않은 발주처 기대

## Pain Point 추출 원칙
- "배경/목적/필요성" 섹션에서 발주처 토로 문제 추출
- 평가 배점이 높은 항목 = 발주처가 가장 중시
- "~해야 한다", "~이 필요하다" 표현에서 추출
- **공공 특화**: 노후 시스템·인력 부족·법제 미준수·표준 미흡·정책 부합

## Win Theme 후보 도출 원칙 (공공 특화)
3개 후보를 다음 축으로 분산:
- 축 1: **정책 부합성** — 국정과제·법제·표준 준수
- 축 2: **검증된 운영** — 유사 실적·SLA·인증·인력
- 축 3: **위험 최소화** — 보안·DR·롤백·단계적 도입

부록의 도메인 카드와 공공입찰 평가기준·컴플라이언스 가이드를 적극 참조하세요.
응답은 반드시 유효한 JSON 형식으로 제공해주세요."""

        return f"""당신은 경쟁 입찰에서 승리하는 제안서를 위한 {doc_label} 분석 전문가입니다.
단순 정보 추출을 넘어, 수주를 위한 전략적 분석을 수행합니다.

## 분석 영역

### 기본 정보
1. 프로젝트 기본 (이름·발주처·개요)
2. 요구사항 (기능/비기능/기술)
3. 평가 기준 및 배점
4. 산출물 / 일정 / 예산

### 전략 분석 (★핵심)
5. **프로젝트 유형 분류**: marketing_pr, event, it_system, public, consulting, general
6. **Pain Point**: 발주처 핵심 고민 3~5개
7. **평가 기준 전략화**: 배점 → 제안서 강조 포인트
8. **Win Theme 후보**: 핵심 수주 메시지 3개
9. **숨겨진 니즈**: 명시되지 않은 발주처 기대

## Win Theme 후보 도출 원칙
3개를 서로 다른 축으로 분산:
- 축 1: 데이터/분석/기술 역량
- 축 2: 실행력/전문성/실적
- 축 3: 통합/시너지/혁신

응답은 반드시 유효한 JSON 형식으로 제공해주세요."""

"""
기획 에이전트 (Stage 3) — 조율자

4개 서브 에이전트를 순차/병렬 실행하여 ProposalPlan 생성
"""

import asyncio
from typing import Any, Callable, Dict, Optional

from .base_agent import BaseAgent
from .planning.structure_planner import StructurePlanner
from .planning.script_planner import ScriptPlanner
from .planning.layout_planner import LayoutPlanner
from .planning.design_planner import DesignPlanner
from ..schemas.planning_schema import ProposalPlan
from ..utils.logger import get_logger

logger = get_logger("planning_agent")


# RFP 유형 추정 실패 시 사용하는 폴백 슬라이드 수 (PROPOSAL_TYPE_CONFIGS 평균치 근사)
_DEFAULT_SLIDE_ESTIMATE = 70


class PlanningAgent(BaseAgent):
    """기획 에이전트 — 4개 서브 에이전트 조율"""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        super().__init__(api_key=api_key, model=model)
        self.structure_planner = StructurePlanner(api_key=api_key, model=model)
        self.script_planner = ScriptPlanner(api_key=api_key, model=model)
        self.layout_planner = LayoutPlanner(api_key=api_key, model=model)
        self.design_planner = DesignPlanner(api_key=api_key, model=model)

    async def execute(
        self,
        input_data: Dict[str, Any],
        progress_callback: Optional[Callable] = None,
    ) -> ProposalPlan:
        """
        제안서 기획 전체 워크플로우

        Args:
            input_data: {
                "rfp_analysis": dict,
                "research": dict (optional),
                "company_data": dict (optional),
                "reference_design": dict (optional),
                "proposal_format": str (optional, ProposalFormat value),
            }
        """
        rfp = input_data.get("rfp_analysis", {})
        research = input_data.get("research", {})
        reference_design = input_data.get("reference_design")
        proposal_format = input_data.get("proposal_format")

        if progress_callback:
            progress_callback({
                "stage": "planning",
                "step": 1,
                "total": 4,
                "message": "구조 기획 시작...",
            })

        # Step 1: 구조 기획 + 디자인 기획 (병렬 실행)
        # design_planner는 structure_planner 결과를 기다리지 않으므로
        # 추정 슬라이드 수를 임시로 전달한다.
        # 우선순위: proposal_format > RFP project_type
        estimated_slides = self._estimate_slide_count(rfp, proposal_format)
        logger.debug(
            f"design_planner 임시 추정 슬라이드 수: {estimated_slides} "
            f"(format={proposal_format}, project_type={rfp.get('project_type')})"
        )

        structure_task = self.structure_planner.execute({
            "rfp_analysis": rfp,
            "research": research,
            "proposal_format": proposal_format,
        }, progress_callback)

        design_task = self.design_planner.execute({
            "rfp_analysis": rfp,
            "structure": {
                "total_slides": estimated_slides,
                "win_themes": rfp.get("win_theme_candidates", []),
            },
            "reference_design": reference_design,
        }, progress_callback)

        structure, design = await asyncio.gather(structure_task, design_task)

        structure_dict = structure.model_dump()
        design_dict = design.model_dump()

        if progress_callback:
            progress_callback({
                "stage": "planning",
                "step": 2,
                "total": 4,
                "message": "스크립트 기획 시작...",
            })

        # Step 2: 스크립트 기획 (구조 기획 결과 필요)
        scripts = await self.script_planner.execute({
            "structure": structure_dict,
            "rfp_analysis": rfp,
            "research": research,
        }, progress_callback)

        scripts_dict = scripts.model_dump()

        if progress_callback:
            progress_callback({
                "stage": "planning",
                "step": 3,
                "total": 4,
                "message": "레이아웃 기획 시작...",
            })

        # Step 3: 레이아웃 기획 (스크립트 결과 필요)
        layouts = await self.layout_planner.execute({
            "scripts": scripts_dict,
            "structure": structure_dict,
        }, progress_callback)

        if progress_callback:
            progress_callback({
                "stage": "planning",
                "step": 4,
                "total": 4,
                "message": "기획 완료",
            })

        logger.info(
            f"기획 완료: {structure.total_slides}슬라이드, "
            f"{scripts.total_scripts}스크립트, "
            f"테마 '{design.theme_name}'"
        )

        return ProposalPlan(
            structure=structure,
            scripts=scripts,
            layouts=layouts,
            design=design,
            rfp_analysis=rfp,
            research=research,
        )

    @staticmethod
    def _estimate_slide_count(
        rfp: Dict[str, Any],
        proposal_format: Optional[str] = None,
    ) -> int:
        """페이지 추정값 — format 우선, RFP project_type 폴백.

        우선순위:
        1. ``proposal_format`` 명시 시: ``PROPOSAL_FORMAT_SPECS[fmt].slide_count_range`` 평균
           (예: delivery_a4_portrait → (70+150)//2 = 110, presentation_a4_landscape → (30+50)//2 = 40)
        2. format 미지정 시: ``PROPOSAL_TYPE_CONFIGS[type].total_pages_range`` 평균 (기존 로직)
        3. 모두 실패: ``_DEFAULT_SLIDE_ESTIMATE`` (70)
        """
        # 1) Format 우선 처리
        if proposal_format:
            try:
                from config.proposal_types import get_format_spec
                spec = get_format_spec(proposal_format)
                lo, hi = spec["slide_count_range"]
                return max(1, (lo + hi) // 2)
            except Exception as e:
                logger.warning(f"format 기반 슬라이드 추정 실패: {e} — project_type 폴백")

        # 2) RFP project_type 폴백
        try:
            from config.proposal_types import ProposalType, get_config
            raw_type = (rfp.get("project_type") or "general").strip().lower()
            try:
                ptype = ProposalType(raw_type)
            except ValueError:
                ptype = ProposalType.GENERAL
            cfg = get_config(ptype)
            lo, hi = cfg.total_pages_range
            return max(1, (lo + hi) // 2)
        except Exception as e:
            logger.warning(f"슬라이드 수 추정 실패, 폴백 사용: {e}")
            return _DEFAULT_SLIDE_ESTIMATE

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
            }
        """
        rfp = input_data.get("rfp_analysis", {})
        research = input_data.get("research", {})
        reference_design = input_data.get("reference_design")

        if progress_callback:
            progress_callback({
                "stage": "planning",
                "step": 1,
                "total": 4,
                "message": "구조 기획 시작...",
            })

        # Step 1: 구조 기획 + 디자인 기획 (병렬 실행 가능)
        structure_task = self.structure_planner.execute({
            "rfp_analysis": rfp,
            "research": research,
        }, progress_callback)

        design_task = self.design_planner.execute({
            "rfp_analysis": rfp,
            "structure": {"total_slides": 80, "win_themes": rfp.get("win_theme_candidates", [])},
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

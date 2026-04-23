"""
5단계 파이프라인 오케스트레이터

분석 → 리서치 → 기획 → 제작(+검수) → 변환
"""

import json
import os
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from ..agents.analysis_agent import AnalysisAgent
from ..agents.research_agent import ResearchAgent
from ..agents.planning_agent import PlanningAgent
from ..agents.production_agent import ProductionAgent
from ..agents.qa_agent import QAAgent
from ..agents.conversion_agent import ConversionAgent
from ..parsers.pdf_parser import PDFParser
from ..parsers.docx_parser import DOCXParser
from ..utils.logger import get_logger
from config.settings import get_settings

logger = get_logger("pipeline_orchestrator")


class PipelineResult:
    """파이프라인 실행 결과"""

    def __init__(self, **kwargs):
        self.analysis = kwargs.get("analysis")
        self.research = kwargs.get("research")
        self.plan = kwargs.get("plan")
        self.production = kwargs.get("production")
        self.qa_report = kwargs.get("qa_report")
        self.conversion = kwargs.get("conversion")
        self.artifacts = kwargs.get("artifacts", {})

    def summary(self) -> Dict[str, Any]:
        return {
            "analysis": bool(self.analysis),
            "research": bool(self.research),
            "plan": bool(self.plan),
            "production": self.production.success if self.production else False,
            "qa_passed": self.qa_report.passed if self.qa_report else None,
            "conversion": self.conversion.success if self.conversion else None,
            "pptx_path": self.production.pptx_path if self.production else None,
            "html_dir": self.conversion.html_output_dir if self.conversion else None,
            "artifacts": self.artifacts,
        }


class PipelineOrchestrator:
    """5단계 제안서 생성 파이프라인"""

    STAGES = ["analysis", "research", "planning", "production", "conversion"]

    def __init__(
        self,
        api_key: Optional[str] = None,
        gemini_api_key: Optional[str] = None,
    ):
        settings = get_settings()
        self.api_key = api_key or settings.anthropic_api_key

        # 에이전트 초기화
        self.analysis_agent = AnalysisAgent(api_key=self.api_key)
        self.research_agent = ResearchAgent(api_key=self.api_key)
        self.planning_agent = PlanningAgent(api_key=self.api_key)
        self.production_agent = ProductionAgent(api_key=self.api_key)
        self.qa_agent = QAAgent(api_key=self.api_key)
        self.conversion_agent = ConversionAgent(
            api_key=self.api_key,
            gemini_api_key=gemini_api_key or os.getenv("GEMINI_API_KEY", ""),
        )

        # 파서
        self.pdf_parser = PDFParser()
        self.docx_parser = DOCXParser()

    async def execute(
        self,
        rfp_path: Path,
        output_dir: Path,
        company_data_path: Optional[Path] = None,
        design_reference_path: Optional[Path] = None,
        design_note: Optional[str] = None,
        skip_stages: Optional[List[str]] = None,
        max_qa_retries: int = 2,
        progress_callback: Optional[Callable] = None,
    ) -> PipelineResult:
        """
        전체 파이프라인 실행

        Args:
            rfp_path: RFP/기획안 문서 경로
            output_dir: 출력 디렉토리
            company_data_path: 회사 정보 JSON
            design_reference_path: 디자인 레퍼런스 경로
            design_note: 디자인 노트
            skip_stages: 건너뛸 단계 ["research", "conversion"]
            max_qa_retries: QA 실패 시 최대 재시도 횟수
            progress_callback: 진행 상황 콜백
        """
        skip_stages = skip_stages or []
        os.makedirs(output_dir, exist_ok=True)
        artifacts = {}

        # ━━━ Stage 1: 분석 ━━━
        if progress_callback:
            progress_callback({
                "pipeline_stage": "analysis",
                "pipeline_step": 1,
                "pipeline_total": 5,
                "message": "Stage 1: 문서 분석 시작",
            })

        parsed = self._parse_document(rfp_path)
        analysis = await self.analysis_agent.execute(parsed, progress_callback)
        analysis_dict = analysis.model_dump()

        artifacts["01_analysis.json"] = self._save_artifact(
            output_dir / "01_analysis.json", analysis_dict
        )

        logger.info(f"Stage 1 완료: {analysis.project_name}")

        # ━━━ Stage 2: 리서치 ━━━
        research_dict = {}
        if "research" not in skip_stages:
            if progress_callback:
                progress_callback({
                    "pipeline_stage": "research",
                    "pipeline_step": 2,
                    "pipeline_total": 5,
                    "message": "Stage 2: 리서치 시작",
                })

            research = await self.research_agent.execute(
                {"rfp_analysis": analysis_dict}, progress_callback
            )
            research_dict = research.model_dump()

            artifacts["02_research.json"] = self._save_artifact(
                output_dir / "02_research.json", research_dict
            )

            logger.info("Stage 2 완료: 리서치")
        else:
            logger.info("Stage 2 스킵: 리서치")

        # ━━━ Stage 3: 기획 ━━━
        if progress_callback:
            progress_callback({
                "pipeline_stage": "planning",
                "pipeline_step": 3,
                "pipeline_total": 5,
                "message": "Stage 3: 기획 시작",
            })

        # 디자인 레퍼런스 분석
        reference_design = None
        if design_reference_path and os.path.exists(design_reference_path):
            try:
                from ..utils.reference_analyzer import ReferenceAnalyzer
                analyzer = ReferenceAnalyzer()
                analyzer.analyze(str(design_reference_path))
                reference_design = analyzer.to_design_profile()
            except Exception as e:
                logger.warning(f"레퍼런스 분석 실패: {e}")

        plan = await self.planning_agent.execute({
            "rfp_analysis": analysis_dict,
            "research": research_dict,
            "company_data": self._load_company_data(company_data_path),
            "reference_design": reference_design,
        }, progress_callback)
        plan_dict = plan.model_dump()

        artifacts["03_plan.json"] = self._save_artifact(
            output_dir / "03_plan.json", plan_dict
        )

        logger.info("Stage 3 완료: 기획")

        # ━━━ Stage 4: 제작 + 검수 ━━━
        if progress_callback:
            progress_callback({
                "pipeline_stage": "production",
                "pipeline_step": 4,
                "pipeline_total": 5,
                "message": "Stage 4: 제작 시작",
            })

        production = await self.production_agent.execute({
            "plan": plan_dict,
            "output_dir": str(output_dir),
        }, progress_callback)

        qa_report = None
        if production.success:
            for attempt in range(max_qa_retries + 1):
                qa_report = await self.qa_agent.execute({
                    "pptx_path": production.pptx_path,
                    "plan": plan_dict,
                }, progress_callback)

                if qa_report.passed:
                    break

                if attempt < max_qa_retries:
                    logger.info(f"QA 미통과, 재제작 시도 {attempt + 1}/{max_qa_retries}")
                    production = await self.production_agent.execute({
                        "plan": plan_dict,
                        "output_dir": str(output_dir),
                        "qa_feedback": qa_report.model_dump(),
                    }, progress_callback)

            artifacts["04_qa_report.json"] = self._save_artifact(
                output_dir / "04_qa_report.json",
                qa_report.model_dump() if qa_report else {},
            )

        logger.info(
            f"Stage 4 완료: 제작 {'성공' if production.success else '실패'}, "
            f"QA {'통과' if qa_report and qa_report.passed else '미통과'}"
        )

        # ━━━ Stage 5: 변환 ━━━
        conversion = None
        if "conversion" not in skip_stages and production.success:
            if progress_callback:
                progress_callback({
                    "pipeline_stage": "conversion",
                    "pipeline_step": 5,
                    "pipeline_total": 5,
                    "message": "Stage 5: 변환 시작",
                })

            conversion = await self.conversion_agent.execute({
                "pptx_path": production.pptx_path,
                "output_dir": str(output_dir / "05_conversion"),
                "design_reference": str(design_reference_path) if design_reference_path else None,
                "design_note": design_note or "",
            }, progress_callback)

            logger.info(f"Stage 5 완료: 변환 {'성공' if conversion.success else '실패'}")
        else:
            logger.info("Stage 5 스킵: 변환")

        return PipelineResult(
            analysis=analysis,
            research=research_dict if research_dict else None,
            plan=plan,
            production=production,
            qa_report=qa_report,
            conversion=conversion,
            artifacts=artifacts,
        )

    def _parse_document(self, file_path: Path) -> Dict[str, Any]:
        """문서 파싱 (PDF/DOCX)"""
        suffix = file_path.suffix.lower()

        if suffix == ".pdf":
            return self.pdf_parser.parse(file_path)
        elif suffix in (".docx", ".doc"):
            return self.docx_parser.parse(file_path)
        else:
            text = file_path.read_text(encoding="utf-8")
            return {"raw_text": text, "tables": [], "sections": []}

    def _load_company_data(self, path: Optional[Path]) -> Dict:
        """회사 데이터 로드"""
        if not path or not path.exists():
            return {}
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _save_artifact(self, path: Path, data: Dict) -> str:
        """아티팩트 JSON 저장"""
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        return str(path)

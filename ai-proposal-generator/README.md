# Proposal Agent — AI 제안서 자동 생성 에이전트 (v4.0)

RFP/기획안을 입력하면 PPTX 제안서(70~140장) + Figma 임포트용 고품질 HTML을 자동 생성하는 멀티 에이전트 시스템.

## 핵심 특징

- **5-Stage 멀티 에이전트 파이프라인**: 분석 → 리서치 → 기획(4개 서브) → 제작+QA → 디자인(HTML)
- **Single-LLM (Claude) 통합 구조**: Stage 5 디자인까지 모두 Claude로 일원화 (Sonnet 4.6 HTML 자동 생성)
- **Impact-8 Framework**: 수주 성공 제안서 기반 8-Phase 구조 + Win Theme + Action Title
- **slide_kit.py 엔진**: 30종 레이아웃 × 6종 테마 PPTX 렌더링 엔진
- **Figma 임포트**: HTML → Puppeteer → JSON → Figma 플러그인으로 네이티브 프레임 변환

## 사전 준비

| 항목 | 설명 |
|------|------|
| **Claude 요금제** | Claude Pro 이상 (Pro / Max / Team) |
| **Claude Code** | `npm install -g @anthropic-ai/claude-code` |
| **Anthropic API 키** | [console.anthropic.com](https://console.anthropic.com)에서 발급 후 `ANTHROPIC_API_KEY` 환경변수에 설정 |
| **Python 3.9+** | `pip install -r requirements.txt` |
| **Node.js + Puppeteer** | Stage 5 Figma JSON 변환용 (`cd figma-plugin && npm install`) |
| **Figma 데스크톱 앱** | HTML→Figma 플러그인 임포트용 |

## 5단계 파이프라인

```
제안요청서/*.pdf 또는 *.docx                ← RFP 입력
    │
    ▼  STEP 1  AnalysisAgent
    │  RFP 분석 (타겟/채널/예산/평가기준)
    │
    ▼  STEP 2  ResearchAgent (스킵 가능)
    │  시장/경쟁/KPI 벤치마크
    │
    ▼  STEP 3  PlanningAgent (4개 서브에이전트)
    │  Structure → Script(Action Title) → Layout(30종) → Design(6 테마)
    │
    ▼  STEP 4  ProductionAgent + QAAgent
    │  slide_kit Python 코드 자동 생성 → PPTX 렌더링 → 자동 검수
    │
    ▼  STEP 5  DesignAgent (Claude Sonnet 4.6)
    │  슬라이드별 HTML 자동 생성 (병렬) → Puppeteer JSON → Figma 플러그인
    │
output/[프로젝트]/                          ← 결과물
  ├─ 제안서.pptx                             (납품용)
  ├─ 03_plan.json                            (기획)
  ├─ 04_qa_report.json                       (검수)
  └─ 05_design/
      ├─ html/presentation.html              (전체 미리보기)
      ├─ html/slide_NNN.html                 (슬라이드별 HTML)
      └─ html/presentation.figma.json        (Figma 임포트 입력)
```

## 빠른 시작

### 1. 설치

```bash
git clone <repo-url> proposal-agent
cd proposal-agent
pip install -r requirements.txt
export ANTHROPIC_API_KEY=your-anthropic-api-key

# Stage 5 Figma 변환을 사용할 경우만 추가
cd figma-plugin && npm install && cd ..
```

### 2. Claude Code에서 시작

```bash
# 프로젝트 루트에서
claude
```

Claude Code 세션에서:

```
/start
```

`/start` 가이드가 제안서 유형(마케팅/입찰/기타) → 디자인 테마 → RFP 경로를 차례로 묻고
5단계 파이프라인을 자동 실행합니다.

### 3. 프로그램적으로 실행 (Python)

```python
from pathlib import Path
import asyncio
from src.orchestrators import PipelineOrchestrator

async def main():
    orchestrator = PipelineOrchestrator()
    result = await orchestrator.execute(
        rfp_path=Path("제안요청서/sample.pdf"),
        output_dir=Path("output/테스트 01"),
        design_reference_path=Path("input/reference.pptx"),  # 선택
        theme="warm_minimal",                                  # 6종 중 선택
        design_concurrency=4,                                  # Stage 5 병렬도
        skip_stages=[],                                        # ["research"] 또는 ["design"]
    )
    print(result.summary())

asyncio.run(main())
```

## 에이전트 구조

| Stage | 에이전트 | 파일 | 역할 |
|-------|---------|------|------|
| 1 | AnalysisAgent | `src/agents/analysis_agent.py` | RFP/기획안 분석 |
| 2 | ResearchAgent | `src/agents/research_agent.py` | 시장/경쟁/트렌드 조사 |
| 3 | PlanningAgent | `src/agents/planning_agent.py` | 4개 서브에이전트 조율 |
| 3-1 | StructurePlanner | `src/agents/planning/structure_planner.py` | Phase별 구조 |
| 3-2 | ScriptPlanner | `src/agents/planning/script_planner.py` | Action Title + 콘텐츠 |
| 3-3 | LayoutPlanner | `src/agents/planning/layout_planner.py` | 30종 레이아웃 배정 |
| 3-4 | DesignPlanner | `src/agents/planning/design_planner.py` | 테마 + 디자인 시스템 |
| 4 | ProductionAgent | `src/agents/production_agent.py` | slide_kit 코드 생성 + PPTX |
| 4 | QAAgent | `src/agents/qa_agent.py` | 겹침/폰트/컬러/플레이스홀더 검수 |
| 5 | DesignAgent | `src/agents/design_agent.py` | Claude로 슬라이드별 HTML 자동 생성 |
| - | BriefAdapter | `src/agents/brief_adapter.py` | 브레인스토밍 → 제안서 연계 |

오케스트레이터: `src/orchestrators/pipeline_orchestrator.py`

## Impact-8 Framework

| Phase | 이름 | 비중 | 설명 |
|-------|------|------|------|
| 0 | HOOK | 5% | 임팩트 있는 오프닝 |
| 1 | EXECUTIVE SUMMARY | 5% | 의사결정자용 요약 + Win Theme |
| 2 | INSIGHT | 10% | 시장 환경 + Pain Point |
| 3 | CONCEPT & STRATEGY | 12% | 핵심 컨셉 + 차별화 전략 |
| 4 | ACTION PLAN | **40%** | 상세 실행 계획 (핵심) |
| 5 | MANAGEMENT | 10% | 조직 + 운영 + 품질관리 |
| 6 | WHY US | 12% | 수행 역량 + 실적 |
| 7 | INVESTMENT & ROI | 6% | 비용 + 기대효과 |

## 디자인 시스템

### 테마 (6종)
`warm_minimal` · `classic_blue` · `forest` · `corporate` · `mono_black` · `soft_purple`

### 레이아웃 (30종)
기본(2) + 컬럼(3) + 비교/데이터(5) + 프로세스(2) + 구조(3) + 이미지(3) + 조직/일정(3) + 스페셜/리스트/그리드/카드(9)

상세: [.claude/rules/layout-design.md](.claude/rules/layout-design.md), [.claude/rules/slide-kit-api.md](.claude/rules/slide-kit-api.md)

## 디렉토리 구조

```
├── CLAUDE.md                         # Claude Code 워크플로우 규칙
├── .claude/
│   ├── commands/start.md             # /start 가이드
│   ├── rules/                        # 경로별 자동 로드 규칙
│   └── skills/pptx/                  # PPTX 스킬 (Anthropic 공식)
├── src/
│   ├── agents/                       # 에이전트 (9개)
│   ├── orchestrators/                # 파이프라인 오케스트레이터
│   ├── generators/slide_kit.py       # PPTX 렌더링 엔진 (30 레이아웃, 6 테마)
│   ├── schemas/                      # Pydantic 스키마
│   ├── parsers/                      # PDF, DOCX 파싱
│   └── utils/                        # 레퍼런스 분석, 로거
├── config/
│   ├── settings.py                   # 환경 설정
│   └── prompts/                      # 프롬프트 템플릿
├── input/                            # 디자인 레퍼런스 (선택)
├── 제안요청서/                        # RFP 입력
├── output/                           # 생성 결과물
└── figma-plugin/                     # HTML→Figma 변환 플러그인
    ├── manifest.json
    ├── render.js                     # Puppeteer HTML→JSON 렌더러
    └── src/                          # 플러그인 소스
```

## 기술 스택

| 카테고리 | 기술 |
|---------|------|
| 기획·제작·디자인 AI | Claude API (Opus 4.7 기획 / Sonnet 4.6 디자인 HTML) |
| Claude Code 진입 | `/start`, `/brainstorm` 슬래시 커맨드 |
| PPTX 렌더링 | python-pptx + slide_kit.py (자체 엔진) |
| HTML → Figma | Puppeteer (`figma-plugin/render.js`) + Figma Plugin |
| 문서 파싱 | pypdf, pdfplumber, python-docx |

## 가이드 문서

- [CLAUDE.md](CLAUDE.md) — 프로젝트 전반 규칙 (Claude Code 자동 로드)
- [.claude/commands/start.md](.claude/commands/start.md) — `/start` 인터랙티브 가이드
- [.claude/rules/slide-kit-api.md](.claude/rules/slide-kit-api.md) — slide_kit API 사용 규칙
- [.claude/rules/layout-design.md](.claude/rules/layout-design.md) — 레이아웃 30종 + 디자인 규칙
- [.claude/rules/impact8-framework.md](.claude/rules/impact8-framework.md) — Impact-8 콘텐츠 규칙

## 버전

- **v4.0** (현재): 5-Stage 멀티 에이전트 + Stage 5 Claude HTML 자동 생성 + Figma 임포트
- v3.6: Win Theme 전달 체인 + Action Title + C-E-I 설득 구조 + KPIWithBasis
- v3.5: VStack 자동 배치 + 네이티브 차트 + 테마 시스템 + 20가지 레이아웃

# Proposal Agent — AI 제안서 자동 생성 에이전트 (v4.0)

[![Tests](https://github.com/EricSeokgon/ai-proposal-generator/actions/workflows/test.yml/badge.svg)](https://github.com/EricSeokgon/ai-proposal-generator/actions/workflows/test.yml)
[![Python](https://img.shields.io/badge/python-3.9~3.12-blue.svg)](https://www.python.org)
[![Tests](https://img.shields.io/badge/tests-172%20passed-brightgreen.svg)](#테스트)

RFP/기획안을 입력하면 PPTX 제안서(70~140장) + Figma 임포트용 고품질 HTML을 자동 생성하는 멀티 에이전트 시스템.

## 핵심 특징

- **5-Stage 멀티 에이전트 파이프라인**: 분석 → 리서치 → 기획(4개 서브) → 제작+QA → 디자인(HTML)
- **공공입찰(나라장터) 특화** ⭐: 8개 도메인 자동 분기 + 평가기준·컴플라이언스 카드 자동 합류
- **Single-LLM (Claude) 통합 구조**: Stage 5 디자인까지 모두 Claude로 일원화 (Sonnet 4.6 HTML 자동 생성)
- **Impact-8 Framework**: 수주 성공 제안서 기반 8-Phase 구조 + Win Theme + Action Title
- **slide_kit.py 엔진**: 30종 레이아웃 × 6종 테마 PPTX 렌더링 엔진
- **Figma 임포트**: HTML → Puppeteer → JSON → Figma 플러그인으로 네이티브 프레임 변환
- **보안·검증**: 생성 코드 AST 정적 분석, 레이아웃 화이트리스트, 경로 traversal 차단, 172 unit tests

## 사전 준비

| 항목 | 설명 |
|------|------|
| **Claude 요금제** | Claude Pro 이상 (Pro / Max / Team) |
| **Claude Code** | `npm install -g @anthropic-ai/claude-code` |
| **Anthropic API 키** | [console.anthropic.com](https://console.anthropic.com)에서 발급 후 `ANTHROPIC_API_KEY` 환경변수에 설정 |
| **Python 3.9+** | `pip install -r requirements.txt` (Pydantic v2, pytest 포함) |
| **Node.js + Puppeteer** | Stage 5 Figma JSON 변환용 (`cd figma-plugin && npm install`) |
| **Figma 데스크톱 앱** | HTML→Figma 플러그인 임포트용 |

## 5단계 파이프라인

```
제안요청서/*.pdf 또는 *.docx                ← RFP 입력
    │
    ▼  STEP 1  AnalysisAgent
    │  RFP 분석 (타겟/채널/예산/평가기준)
    │  공공입찰 자동 감지 + 8 도메인 분기 (가중치 알고리즘)
    │
    ▼  STEP 2  ResearchAgent (스킵 가능)
    │  시장/경쟁/KPI 벤치마크
    │
    ▼  STEP 3  PlanningAgent (4개 서브에이전트)
    │  Structure → Script(Action Title) → Layout(30종) → Design(6 테마)
    │
    ▼  STEP 4  ProductionAgent + QAAgent
    │  slide_kit Python 코드 자동 생성 → AST 보안 검증 → PPTX 렌더링 → 자동 검수
    │
    ▼  STEP 5  DesignAgent (Claude Sonnet 4.6)
    │  슬라이드별 HTML 자동 생성 (병렬, 글로벌 타임아웃 적용) → Puppeteer JSON → Figma 플러그인
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
git clone https://github.com/EricSeokgon/ai-proposal-generator.git proposal-agent
cd proposal-agent/ai-proposal-generator
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
        design_concurrency=4,                                  # Stage 5 병렬도 (1~8)
        skip_stages=[],                                        # ["research"] 또는 ["design"]
    )
    print(result.summary())

asyncio.run(main())
```

## 환경 변수

런타임 동작은 환경변수로 오버라이드 가능합니다 (`config/settings.py`).

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `ANTHROPIC_API_KEY` | — | **필수**. Anthropic API 키 (빈 값이면 `BaseAgent` 인스턴스화 시 `ValueError`) |
| `CLAUDE_MODEL` | `claude-sonnet-4-6` | 전 단계 공통 기본 모델 |
| `CLAUDE_MODEL_HEAVY` | `claude-opus-4-7` | 고난도 분석/기획 옵션 모델 |
| `CLAUDE_MODEL_FAST` | `claude-haiku-4-5` | 빠른 보조 작업 옵션 모델 |
| `CLAUDE_MODEL_DESIGN` | `claude-sonnet-4-6` | Stage 5 HTML 생성 전용 모델 |
| `MAX_TEXT_CHARS` | `30000` | Claude 입력 텍스트 절단 임계 |
| `MAX_RFP_TEXT_CHARS` | `25000` | RFP 분석 시 절단 임계 |
| `MAX_TABLES_CHARS` | `5000` | 테이블 JSON 절단 임계 |
| `DESIGN_GLOBAL_TIMEOUT_SECONDS` | `1800` | Stage 5 전체 HTML 생성 타임아웃 (초) |

`.env` 파일 또는 셸 export 모두 지원 (python-dotenv).

## 공공입찰 (나라장터) 특화 ⭐

이 시스템은 한국 공공입찰(나라장터·조달청) 제안서 작성에 최적화되어 있습니다.

### 8대 도메인 자동 분기

| 도메인 | 카드 파일 | 핵심 |
|--------|---------|------|
| 빅데이터 신규 구축 | [config/domains/bigdata.md](config/domains/bigdata.md) | Hadoop·Spark·Lakehouse |
| 빅데이터 유지보수 | [config/domains/bigdata_maintenance.md](config/domains/bigdata_maintenance.md) | SLA·ITIL·24/7 NOC |
| 빅데이터 분석 | [config/domains/bigdata_analytics.md](config/domains/bigdata_analytics.md) | CRISP-DM·정책 분석·BI |
| 빅데이터 고도화 | [config/domains/bigdata_modernization.md](config/domains/bigdata_modernization.md) | 6단계 무중단 전환·CDC |
| AI / ML / LLM | [config/domains/ai.md](config/domains/ai.md) | KMMLU·MLOps·신뢰성 |
| 인프라 / 클라우드 | [config/domains/infra.md](config/domains/infra.md) | K-Cloud·CSAP·이중화·DR |
| CCTV / 스마트시티 | [config/domains/cctv.md](config/domains/cctv.md) | 5대 안전망·VMS·LPR |
| 데이터 거버넌스 | [config/domains/data_governance.md](config/domains/data_governance.md) | 데이터3법·가명결합·KCMVP |

각 카드는 정책·법제·아키텍처·KPI 벤치마크·인증·핵심 인력·유사 사업 레퍼런스를 포함.

### 자동 분기 규칙

`AnalysisAgent` 가 RFP 텍스트에서 공공입찰 신호어를 가중치 합산(strong=3 / medium=2 / weak=1)
하여 임계값 ≥ 5 시 자동 활성화. 도메인 매칭은 키워드 길이 가중치(1~3점)
+ 임계값 ≥ 3.

### Phase 프롬프트 자동 라우팅

| Phase | 마케팅 | 공공입찰 |
|-------|--------|---------|
| 2 INSIGHT | `phase2_insight.txt` | `phase2_insight_public.txt` (정책 연계 + RTM 매트릭스) |
| 4 ACTION | `phase4_action.txt` | `phase4_action_public.txt` (WBS·아키·ISMS-P·M/M) |
| 5 MANAGEMENT | `phase5_management.txt` | `phase5_management_public.txt` (PMO·CMMI Lvl.3·위험 5×5) |
| 6 WHY US | `phase6_whyus.txt` | `phase6_whyus_public.txt` (실적·인력·인증 3축) |
| 7 INVESTMENT | `phase7_investment.txt` | `phase7_investment_public.txt` (노임단가·정책·시민 효익) |

### 강제 분기

```python
# 공공입찰 강제 + CCTV 도메인 강제
result = await orchestrator.execute(
    rfp_path=Path("..."),
    output_dir=Path("..."),
    # AnalysisAgent input_data 에 force_public, force_domain 전달 가능
)
```

## 테스트

172 unit tests + Python 3.9~3.12 매트릭스 CI.

```bash
# 의존성 (pytest, pytest-asyncio 포함)
pip install -r requirements.txt

# 전체 실행
pytest -v

# 특정 모듈
pytest tests/test_layout_planner.py -v

# Pydantic deprecation 0건 검증
pytest --tb=no -q | grep PydanticDeprecated && echo "FAIL" || echo "OK"
```

테스트 슈트 구성:

| 영역 | 파일 | 검증 |
|------|------|------|
| 설정 | `test_settings.py` | 모델 ID + 환경변수 동적 평가 |
| 도메인 매칭 | `test_proposal_types.py` | 가중치 알고리즘, 화이트리스트 |
| 신호어 감지 | `test_analysis_agent.py` | 가중치 점수, 단어 경계, force_* |
| BaseAgent | `test_base_agent.py` | API 키 검증, 도메인 카드 합류 |
| 보안 (AST) | `test_production_agent.py` | RCE 차단, QA 정렬 |
| Plan/Layout | `test_planning_*.py`, `test_layout_planner.py` | Field 제약, 30종 화이트리스트 |
| 파서 | `test_pdf_parser.py` | 암호화 차단, 메모리 중복 제거 |
| Stage 5 | `test_design_agent.py` | 경로 traversal 차단 |
| 그 외 | `test_brief_adapter.py`, `test_research_agent.py`, `test_script_planner.py` | 폴백, 인코딩, 투명성 |

## 에이전트 구조

| Stage | 에이전트 | 파일 | 역할 |
|-------|---------|------|------|
| 1 | AnalysisAgent | `src/agents/analysis_agent.py` | RFP/기획안 분석 + 공공 자동 감지 |
| 2 | ResearchAgent | `src/agents/research_agent.py` | 시장/경쟁/트렌드 조사 |
| 3 | PlanningAgent | `src/agents/planning_agent.py` | 4개 서브에이전트 조율 |
| 3-1 | StructurePlanner | `src/agents/planning/structure_planner.py` | Phase별 구조 + total_slides 클램핑 |
| 3-2 | ScriptPlanner | `src/agents/planning/script_planner.py` | Action Title + 콘텐츠 + 폴백 |
| 3-3 | LayoutPlanner | `src/agents/planning/layout_planner.py` | 30종 레이아웃 배정 + 화이트리스트 |
| 3-4 | DesignPlanner | `src/agents/planning/design_planner.py` | 테마 + 디자인 시스템 |
| 4 | ProductionAgent | `src/agents/production_agent.py` | slide_kit 코드 생성 + AST 보안 검증 + PPTX |
| 4 | QAAgent | `src/agents/qa_agent.py` | 겹침/폰트/컬러/플레이스홀더 검수 |
| 5 | DesignAgent | `src/agents/design_agent.py` | Claude HTML 자동 생성 + 글로벌 타임아웃 |
| - | BriefAdapter | `src/agents/brief_adapter.py` | 브레인스토밍 → 제안서 연계 (인코딩 폴백) |

총 **11개 에이전트** (메인 7 + 서브 4). 오케스트레이터: `src/orchestrators/pipeline_orchestrator.py`

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
│   ├── agents/                       # 에이전트 (11개: 메인 7 + 서브 4)
│   ├── orchestrators/                # 파이프라인 오케스트레이터
│   ├── generators/slide_kit.py       # PPTX 렌더링 엔진 (30 레이아웃, 6 테마)
│   ├── schemas/                      # Pydantic v2 스키마
│   ├── parsers/                      # PDF (암호화 차단), DOCX 파싱
│   └── utils/                        # 레퍼런스 분석, 로거
├── config/
│   ├── settings.py                   # 환경 설정 (Field default_factory)
│   ├── proposal_types.py             # 8 공공 도메인 + 매칭 가중치
│   ├── prompts/                      # Phase 프롬프트 (마케팅/공공 분기)
│   ├── domains/                      # 8 도메인 카드
│   └── public_bidding/               # 평가기준 + 컴플라이언스
├── tests/                            # 172 unit tests (13 파일)
├── docs/                             # 코드 리뷰 보고서, slide_kit 레퍼런스
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
| 검증/품질 | Pydantic v2, pytest, pytest-asyncio, GitHub Actions |
| 로깅 | loguru (인스턴스별 logger) |

## 가이드 문서

- [CLAUDE.md](CLAUDE.md) — 프로젝트 전반 규칙 (Claude Code 자동 로드)
- [.claude/commands/start.md](.claude/commands/start.md) — `/start` 인터랙티브 가이드
- [.claude/rules/slide-kit-api.md](.claude/rules/slide-kit-api.md) — slide_kit API 사용 규칙
- [.claude/rules/layout-design.md](.claude/rules/layout-design.md) — 레이아웃 30종 + 디자인 규칙
- [.claude/rules/impact8-framework.md](.claude/rules/impact8-framework.md) — Impact-8 콘텐츠 규칙
- [docs/code_review_2026-04-27.md](docs/code_review_2026-04-27.md) — 코드 리뷰 종합 보고서

## 버전

- **v4.0** (현재): 5-Stage 멀티 에이전트 + Stage 5 Claude HTML 자동 생성 + Figma 임포트
  + 보안·품질 강화 (AST 검증, 화이트리스트, 경로 traversal 차단, 172 tests, CI)
- v3.6: Win Theme 전달 체인 + Action Title + C-E-I 설득 구조 + KPIWithBasis
- v3.5: VStack 자동 배치 + 네이티브 차트 + 테마 시스템 + 20가지 레이아웃

## 라이선스 / 기여

이 프로젝트는 내부용으로 시작되었습니다. 외부 기여를 받기 전 보안·법무 검토가 필요합니다.

CI 가 PR 마다 자동 실행되며 다음을 검증합니다:
- Python 3.9 / 3.10 / 3.11 / 3.12 매트릭스에서 172 tests 통과
- Pydantic v1 deprecation warning 0건

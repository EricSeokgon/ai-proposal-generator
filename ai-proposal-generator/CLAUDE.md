# 제안서 자동 생성 에이전트 (v4.0 — 5-Stage Multi-Agent Pipeline)

RFP/기획안 문서를 입력받아 PPTX 제안서를 자동 생성하고, HTML 변환 후 Figma로 임포트하는 멀티 에이전트 시스템

## 시작: `/start`

`/start` 명령으로 제안서 제작 가이드를 시작합니다.

## 지원 제안서 유형

| 유형 | 설명 | 필수 자료 | 선택 자료 |
|------|------|----------|----------|
| **마케팅 제안서** | SNS 운영, 브랜드 캠페인, 홍보, PR | RFP/기획안 | 브랜드 가이드, 경쟁사 자료 |
| **입찰 제안서** | 공공입찰, IT, 컨설팅, 이벤트 | RFP(평가기준 포함) | 회사소개서, 유사실적 |
| **기타** | 사용자 정의 (질문을 통해 설정) | 기획안/브리프 | 자유 |

## 5단계 파이프라인

```
/start → 제안서 유형 선택 → 자료 준비 → 5단계 자동 실행

STEP 1 📄 분석    → [AnalysisAgent] → 01_analysis.json
STEP 2 🔍 리서치   → [ResearchAgent] → 02_research.json (스킵 가능)
STEP 3 📐 기획    → [PlanningAgent] (4개 서브에이전트)
  ├─ StructurePlanner (전체 구조)
  ├─ ScriptPlanner (장표 스크립트)
  ├─ LayoutPlanner (30종 레이아웃 배정)
  └─ DesignPlanner (6종 테마 + 디자인)
  → 03_plan.json
STEP 4 🎨 제작    → [ProductionAgent] + [QAAgent] → PPTX (납품용) + 04_qa_report.json
STEP 5 🎯 디자인  → [DesignAgent] Plan JSON → Gemini → HTML → Puppeteer → JSON → Figma 플러그인
```

## 필수 규칙: PPTX 생성 스크립트

모든 스크립트는 `src/generators/slide_kit.py`를 import해야 합니다.
상세 API 및 규칙:
- @.claude/rules/slide-kit-api.md
- @.claude/rules/layout-design.md
- @.claude/rules/impact8-framework.md

## 에이전트 구조

| Stage | 에이전트 | 파일 | 역할 |
|-------|---------|------|------|
| 1 | AnalysisAgent | `src/agents/analysis_agent.py` | RFP/기획안 분석 |
| 2 | ResearchAgent | `src/agents/research_agent.py` | 시장/경쟁/트렌드 조사 |
| 3 | PlanningAgent | `src/agents/planning_agent.py` | 4개 서브에이전트 조율 |
| 3-1 | StructurePlanner | `src/agents/planning/structure_planner.py` | Phase별 구조 기획 |
| 3-2 | ScriptPlanner | `src/agents/planning/script_planner.py` | Action Title + 콘텐츠 |
| 3-3 | LayoutPlanner | `src/agents/planning/layout_planner.py` | 30종 레이아웃 배정 |
| 3-4 | DesignPlanner | `src/agents/planning/design_planner.py` | 6종 테마 + 디자인 |
| 4 | ProductionAgent | `src/agents/production_agent.py` | slide_kit 코드 생성 + PPTX |
| 4 | QAAgent | `src/agents/qa_agent.py` | 겹침/폰트/컬러/플레이스홀더 검수 |
| 5 | DesignAgent | `src/agents/design_agent.py` | Plan→Gemini→HTML→Puppeteer→JSON→Figma 플러그인 |
| - | BriefAdapter | `src/agents/brief_adapter.py` | 브레인스토밍→제안서 연계 변환 |

오케스트레이터: `src/orchestrators/pipeline_orchestrator.py`

## 디자인 시스템

### 테마 (6종)
```python
apply_theme("warm_minimal")   # 기본 — 따뜻한 베이지
apply_theme("classic_blue")   # 클래식 네이비 블루
apply_theme("forest")         # 포레스트 그린 (자연/ESG)
apply_theme("corporate")      # 코퍼레이트 네이비 (금융/공공)
apply_theme("mono_black")     # 모노 블랙 (미니멀/IT)
apply_theme("soft_purple")    # 소프트 퍼플 (크리에이티브)
```

### 레이아웃 (30종)
기본(2) + 컬럼(3) + 비교/데이터(5) + 프로세스(2) + 구조(3) + 이미지(3) + 조직/일정(3) + 스페셜/리스트/그리드/카드(9)

## 디렉토리 구조

```
├── CLAUDE.md
├── .claude/
│   ├── commands/start.md          # /start 가이드
│   ├── rules/                     # 경로별 자동 로드 규칙 (3개)
│   └── skills/pptx/               # PPTX 스킬 (Anthropic 공식)
├── src/
│   ├── agents/                    # 에이전트 (11개)
│   ├── orchestrators/             # 파이프라인 오케스트레이터
│   ├── generators/slide_kit.py    # PPTX 렌더링 엔진 (30 레이아웃, 6 테마)
│   ├── schemas/                   # Pydantic 스키마 (8개)
│   ├── parsers/                   # PDF, DOCX 파싱
│   └── utils/                     # 레퍼런스 분석, 로거
├── config/prompts/                # 프롬프트 템플릿
├── input/                         # 디자인 레퍼런스
├── 제안요청서/                     # RFP 입력
├── output/                        # 생성 결과물
└── figma-plugin/                  # HTML→Figma 변환 플러그인
    ├── manifest.json              # Figma 플러그인 매니페스트
    ├── render.js                  # Puppeteer HTML→JSON 렌더러
    ├── src/                       # 플러그인 소스
    └── dist/                      # 빌드 결과
```

## 사전 준비
- **Claude Pro 이상** + Claude Code CLI
- **Gemini API 키** (Stage 5): `export GEMINI_API_KEY=your-key`
- **Python 3.9+**: `pip install -r requirements.txt`
- **Node.js + Puppeteer** (Stage 5 Figma 임포트): `cd figma-plugin && npm install`
- **Figma 데스크톱 앱**: Plugins > Import plugin from manifest > `figma-plugin/manifest.json`

# 제안서 자동 생성 에이전트 (v4.0 — 5-Stage Multi-Agent Pipeline)

RFP/기획안 문서를 입력받아 PPTX 제안서를 자동 생성하고, HTML 변환 후 Figma로 임포트하는 멀티 에이전트 시스템

## 시작: `/start`

`/start` 명령으로 제안서 제작 가이드를 시작합니다.

## 지원 제안서 유형

| 유형 | 설명 | 필수 자료 | 선택 자료 |
|------|------|----------|----------|
| **마케팅 제안서** | SNS 운영, 브랜드 캠페인, 홍보, PR | RFP/기획안 | 브랜드 가이드, 경쟁사 자료 |
| **공공입찰 제안서** ⭐ | 나라장터·조달청 (8개 도메인 자동 분기) | RFP(평가기준 포함) | 유사실적 5건+, 인증서, 핵심 인력 이력 |
| **기타** | 사용자 정의 (질문을 통해 설정) | 기획안/브리프 | 자유 |

## 공공입찰 (나라장터) 특화 시스템 ⭐

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

### 공공입찰 공통 카드 (모든 도메인에 자동 합류)
- [config/public_bidding/evaluation_criteria.md](config/public_bidding/evaluation_criteria.md) — 협상에 의한 계약·적격심사·평가표·RTM·노임단가
- [config/public_bidding/compliance.md](config/public_bidding/compliance.md) — ISMS-P·CSAP·CC·KCMVP·GS·CMMI·인력 자격

### 공공입찰 Phase 프롬프트 (자동 분기)

`AnalysisAgent`가 RFP에서 공공입찰 신호어 3개+ 감지 시 `phase{N}_*_public.txt`로 자동 라우팅:

| Phase | 공공입찰 프롬프트 | 핵심 차별점 |
|-------|----------------|-----------|
| 2. INSIGHT | [phase2_insight_public.txt](config/prompts/phase2_insight_public.txt) | 정책 연계 + As-Is 진단 + RTM 매트릭스 |
| 4. ACTION | [phase4_action_public.txt](config/prompts/phase4_action_public.txt) | WBS·아키텍처·산출물 50+·ISMS-P 보안 통제·M/M |
| 5. MGMT | [phase5_management_public.txt](config/prompts/phase5_management_public.txt) | PMO + ISMS-P + CMMI Lvl.3 + 위험 5×5 매트릭스 |
| 6. WHY US | [phase6_whyus_public.txt](config/prompts/phase6_whyus_public.txt) | 유사 실적·핵심 인력·인증 매트릭스 (3대 축) |
| 7. INVEST | [phase7_investment_public.txt](config/prompts/phase7_investment_public.txt) | 한국SW협회 노임단가·M/M·정책·시민 효익 |

### 자동 합류 규칙

`AnalysisAgent.execute()` 내부:
1. RFP 텍스트에서 공공입찰 신호어("나라장터·조달청·협상에 의한 계약·ISMS-P" 등) 3개+ 매칭 → 공공 분기 활성화
2. 도메인 키워드 사전(`PUBLIC_DOMAIN_KEYWORDS`)으로 매칭 점수 최고 도메인 자동 지정
3. system prompt에 도메인 카드 + 평가기준 + 컴플라이언스 카드를 부록으로 합류
4. 강제 지정: `input_data["force_public"]=True` 또는 `input_data["force_domain"]="cctv"` 등

`BaseAgent._load_prompt_with_domain()` 라우터를 다른 에이전트에서도 동일하게 사용 가능.

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
STEP 5 🎯 디자인  → [DesignAgent] Plan JSON → Claude(Sonnet 4.6) → HTML → Puppeteer → JSON → Figma 플러그인
```

## 필수 규칙: PPTX 생성 스크립트

모든 스크립트는 `src/generators/slide_kit.py`를 import해야 합니다.
상세 API 및 규칙:
- @.claude/rules/slide-kit-api.md
- @.claude/rules/layout-design.md
- @.claude/rules/impact8-framework.md

## 공공입찰 분기 자동화 규칙

- `project_type="public"` 또는 RFP 자동 감지 시 → `phase{N}_*_public.txt` 우선 사용 (없으면 마케팅 폴백)
- 도메인 카드 + `config/public_bidding/*.md`이 system prompt에 자동 합류
- 도메인 추가/수정 시 [config/proposal_types.py](config/proposal_types.py)의 `PublicDomain` enum + `PUBLIC_DOMAIN_CARDS` + `PUBLIC_DOMAIN_KEYWORDS` 3개 동시 업데이트 필수
- 새 phase 프롬프트는 반드시 `phase{N}_{name}_public.txt` 네이밍 규칙 준수 — `get_prompt_file()` 라우터가 이 패턴으로 탐색

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
| 5 | DesignAgent | `src/agents/design_agent.py` | Plan→Claude(HTML 자동 생성)→Puppeteer→JSON→Figma 플러그인 |
| - | BriefAdapter | `src/agents/brief_adapter.py` | 브레인스토밍→제안서 연계 변환 |

오케스트레이터: `src/orchestrators/pipeline_orchestrator.py`

## 디자인 시스템

### 테마 (10종)
```python
# 기존 6종
apply_theme("warm_minimal")   # 기본 — 따뜻한 베이지
apply_theme("classic_blue")   # 클래식 네이비 블루
apply_theme("forest")         # 포레스트 그린 (자연/ESG)
apply_theme("corporate")      # 코퍼레이트 네이비 (금융/공공)
apply_theme("mono_black")     # 모노 블랙 (미니멀/IT)
apply_theme("soft_purple")    # 소프트 퍼플 (크리에이티브)
# 신규 4종
apply_theme("sunset_orange")  # 따뜻한 오렌지 (마케팅/스타트업/F&B)
apply_theme("ocean_teal")     # 청록·민트 (헬스/테크/교육)
apply_theme("gold_luxury")    # 골드·블랙 (프리미엄/금융/럭셔리)
apply_theme("arctic_white")   # 화이트·실버 (의료/IT/미니멀)
```

### 레이아웃 (36종)
기본(2) + 컬럼(3) + 비교/데이터(5) + 프로세스(2) + 구조(3) + 이미지(3) + 조직/일정(3) + 스페셜/리스트/그리드/카드(9) + **신규(6)**

신규 6종:
- `VERTICAL_STEPS` — 세로 5단계 (A4 세로 친화)
- `TIMELINE_VERTICAL` — 세로 타임라인 (A4 세로 친화)
- `HEADLINE_NUMBER` — 대형 헤드라인 + 큰 숫자 (KPI 강조)
- `CARD_GRID_6` — 3열×2행 카드 6개
- `AGENDA_TWO_COL` — 2열 아젠다 10항목
- `PRICING_TABLE` — 3열 플랜/가격 비교

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
- **Anthropic API 키** (전 단계 공통): `export ANTHROPIC_API_KEY=your-key`
  - Stage 5는 기본 모델로 `claude-sonnet-4-6`를 사용 (HTML 자동 생성)
- **Python 3.9+**: `pip install -r requirements.txt`
- **Node.js + Puppeteer** (Stage 5 Figma 임포트): `cd figma-plugin && npm install`
- **Figma 데스크톱 앱**: Plugins > Import plugin from manifest > `figma-plugin/manifest.json`

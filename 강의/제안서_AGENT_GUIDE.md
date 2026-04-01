# 제안서 자동 생성 에이전트 - 구축 & 사용 가이드

---

## 1. 프롬프트 (사용자 요청)

```
RFP 분석부터 PPTX 제안서 자동 생성까지 해주는 에이전트를 만들어줘.
5단계 파이프라인으로 분석→리서치→기획→제작→디자인 변환을 자동화하고,
Impact-8 구조(HOOK~INVESTMENT)로 70~140장 제안서를 생성해야 해.
PPTX 납품용 + HTML→Figma 고퀄리티 디자인 듀얼 출력을 지원해야 해.
브레인스토밍 에이전트(3명 AI 전문가)와 연계도 지원해야 해.
```

---

## 2. 입력 데이터

### 2-1. RFP/기획안 (필수)

`제안요청서/` 폴더에 RFP 또는 기획안 파일을 넣어야 합니다.

| 형식 | 설명 |
|------|------|
| PDF | RFP 제안요청서 (평가기준표 포함 권장) |
| DOCX | 기획안/브리프 문서 |

### 2-2. 디자인 레퍼런스 (선택)

`input/` 폴더에 원하는 디자인 스타일의 파일을 넣으면 STEP 5에서 반영됩니다.

| 형식 | 설명 |
|------|------|
| PPTX | 레퍼런스 제안서 (원하는 스타일의 제안서) |
| 이미지 (PNG/JPG) | 디자인 무드보드, 스크린샷 |
| PDF | 브랜드 가이드 |

### 2-3. 회사 자료 (선택)

| 자료 | 용도 |
|------|------|
| 회사소개서 | WHY US 섹션에 반영 |
| 유사 수행실적 | 레퍼런스 사례로 활용 |
| 브랜드 가이드 | 디자인 시스템에 반영 |

---

## 3. 설치 및 실행

### 사전 준비

```bash
# Python 3.9 이상
python3 --version

# 프로젝트 폴더로 이동
cd "제안서 에이전트"

# Python 의존성 설치
pip install -r requirements.txt

# Node.js + Puppeteer (STEP 5 Figma 변환용)
cd figma-plugin && npm install && cd ..
```

### Figma 플러그인 설치 (최초 1회)

1. Figma 데스크톱 앱 열기
2. 좌측 상단 메뉴 > **Plugins** > **Development** > **Import plugin from manifest...**
3. `figma-plugin/manifest.json` 파일 선택
4. "Proposal HTML to Figma" 플러그인 등록 완료

### 실행 방법

```bash
# Claude Code에서 시작
/start

# 또는 자연어로도 동작
"제안서 만들어줘"
"RFP 분석 시작"
```

---

## 4. 사용 방법 (5단계 파이프라인)

### 시작하기

```
Claude Code에서 /start 입력
→ 진행 방식 선택 (A: 브레인스토밍 풀 코스 / B: 바로 제작)
→ 제안서 유형 선택 (마케팅/입찰/기타)
→ 디자인 테마 선택 (6종)
→ 5단계 자동 실행
```

### 전체 흐름

```
STEP 1. 📄 분석 — RFP/기획안 분석
  ↓
STEP 2. 🔍 리서치 — 시장/경쟁/KPI 조사 (스킵 가능)
  ↓
STEP 3. 📐 기획 — 구조 + 스크립트 + 레이아웃 + 디자인
  ↓
STEP 4. 🎨 제작 — PPTX 생성 + QA 검수
  ↓
STEP 5. 🎯 디자인 변환 — HTML → Figma (선택)
  ├─ 5-1: 디자인 레퍼런스 입력
  ├─ 5-2: Gemini 프롬프트 생성 (Claude 자동)
  ├─ 5-3: Gemini에서 HTML 디자인 (사용자)
  ├─ 5-4: Claude에서 워딩/구조 수정
  ├─ 5-5: Puppeteer JSON 변환 (자동)
  └─ 5-6: Figma 플러그인 임포트 (사용자)
```

### STEP 1: 분석

RFP/기획안을 자동 분석합니다.

| 분석 항목 | 설명 |
|----------|------|
| 프로젝트 개요 | 사업명, 발주처, 기간, 예산 |
| 평가기준 | 배점 분석 → 제안서 비중 결정 |
| 타겟 분석 | 대상 고객, 채널, 캠페인 목표 |
| Pain Point | 발주처의 진짜 고민 + 수주 전략 |
| Win Theme | 3대 핵심 수주 메시지 자동 도출 |

**출력**: `01_analysis.json`

### STEP 2: 리서치

시장 트렌드, 경쟁사 분석, KPI 벤치마크를 자동 조사합니다. 리서치 없이도 제안서 생성이 가능하므로 **스킵 가능**합니다.

| 조사 항목 | 설명 |
|----------|------|
| 시장 트렌드 | 업계 동향, 기술 트렌드 |
| 경쟁사 분석 | 경쟁 캠페인, 채널 전략 |
| KPI 벤치마크 | 업계 평균 성과 지표 |
| 데이터 출처 | 모든 수치에 출처 명시 |

**출력**: `02_research.json`

### STEP 3: 기획

4개의 서브에이전트가 순차적으로 제안서를 설계합니다.

```
StructurePlanner → Impact-8 Phase별 구조 + 장수 배분
  ↓
ScriptPlanner → 장표별 Action Title + 콘텐츠 스크립트
  ↓
LayoutPlanner → 30종 레이아웃 중 최적 배정 (연속 3장 동일 금지)
  ↓
DesignPlanner → 6종 테마 선택 + 디자인 상세 설정
```

**출력**: `03_plan.json`

### STEP 4: 제작 + QA 검수

`slide_kit.py` 엔진으로 PPTX를 자동 생성하고 QA 검수를 진행합니다.

```
ProductionAgent → 03_plan.json 기반 Python 코드 생성 → PPTX 렌더링
  ↓
QAAgent → 자동 검수 (겹침/폰트/컬러/플레이스홀더)
  → critical 이슈 발견 시 자동 재생성 (최대 2회)
```

| QA 항목 | 설명 |
|---------|------|
| 겹침 검수 | 요소 간 겹침 자동 감지 |
| 폰트 검수 | Pretendard 이외 폰트 사용 감지 |
| 컬러 검수 | 테마 외 하드코딩 컬러 감지 |
| 플레이스홀더 | [대괄호] 형식 미완성 콘텐츠 체크 |

**출력**: `PPTX 파일` + `04_qa_report.json`

### STEP 5: 디자인 변환 (선택)

PPTX 납품만 필요하면 STEP 4에서 완료. 디자인 퀄리티를 높이려면 STEP 5를 진행합니다.

#### STEP 5-1: 디자인 레퍼런스 입력

원하는 디자인 스타일의 파일을 `input/` 폴더에 넣습니다.
레퍼런스가 없어도 진행 가능합니다.

#### STEP 5-2: Gemini 디자인 프롬프트 생성

Claude가 PPTX 콘텐츠 + 디자인 레퍼런스를 분석하여 Gemini용 프롬프트를 자동 작성합니다.

**생성되는 파일:**
```
output/[프로젝트]/05_design/
├── DESIGN_GUIDE.md          ← 작업 가이드 (이것부터 읽으세요!)
├── design_system.json       ← 디자인 시스템 (컬러/폰트/스타일)
└── prompts/
    ├── slide_000.md         ← 슬라이드별 Gemini 프롬프트
    ├── slide_001.md
    └── ... (총 XX개)
```

#### STEP 5-3: Gemini에서 HTML 디자인 제작

1. gemini.google.com 접속 → Gemini 2.5 Pro 모델 선택
2. (선택) 디자인 레퍼런스 이미지를 Gemini에 첨부
3. `prompts/` 폴더의 프롬프트를 순서대로 복붙 → HTML 생성
4. 마음에 안 들면 "여기 수정해줘"로 대화하며 수정
5. 완성된 HTML을 `html/` 폴더에 저장

#### STEP 5-4: Claude에서 워딩/구조 수정

Gemini가 만든 HTML을 Claude Code에 붙여넣으면, 기획안(`03_plan.json`)과 대조하여 정밀 수정합니다.

| 수정 항목 | 설명 |
|----------|------|
| Action Title | 기획안 기준 인사이트 제목 적용 |
| KPI 수치 | 산출근거와 일치하는 정확한 수치 |
| Win Theme | 3대 수주 메시지 일관 반영 |
| 오탈자/문법 | 자동 교정 |

사용법:
```
"HTML 워딩 수정해줘"
"기획안 내용과 맞춰줘"
"3번 슬라이드 제목 바꿔줘"
```

#### STEP 5-5: Puppeteer JSON 변환

Claude가 자동으로 Puppeteer를 실행하여 HTML을 Figma JSON으로 변환합니다.

```bash
cd figma-plugin
node render.js ../projects/[프로젝트]/output/05_design/html/presentation.html
```

**원리:**
- Puppeteer가 Chrome 브라우저로 HTML을 실제 렌더링
- 모든 요소의 `getBoundingClientRect()` + `getComputedStyle()` 추출
- 부모 기준 상대 좌표로 JSON 저장 (Figma의 좌표 시스템과 동일)

**출력**: `presentation.figma.json`

#### STEP 5-6: Figma 플러그인 임포트

1. Figma에서 **Plugins > Development > "Proposal HTML to Figma"** 실행
2. `.figma.json` 파일을 플러그인 창에 드래그 앤 드롭
3. "Figma로 변환" 클릭
4. 슬라이드가 5장씩 행으로 자동 배치됨

**Figma에서 편집 가능한 항목:**
- 모든 텍스트 (네이티브 텍스트 노드)
- 도형/배경 (네이티브 프레임)
- 색상/그라디언트
- 이미지 placeholder → 실제 이미지 교체
- 간격/정렬 미세 조정

---

## 5. 브레인스토밍 에이전트 (풀 코스)

풀 코스(A) 선택 시 제안서 제작 전에 3명의 AI 전문가가 캠페인을 기획합니다.

### 3명의 AI 전문가

| 에이전트 | 파일 | 역할 |
|---------|------|------|
| 전략가 | `campaign-strategist.md` | 시장 분석, 타겟 세분화, Win Theme 도출 |
| 크리에이터 | `campaign-creator.md` | 크리에이티브 컨셉, 콘텐츠 전략, 채널 기획 |
| 데이터 분석가 | `campaign-data-analyst.md` | KPI 설계, 벤치마크 수집, ROI 산출 |

### 브레인스토밍 7단계

```
Step 1~2: 정보 수집
  → RFP/브리프 분석, 시장 환경 파악

Step 3: 3인 독립 기획
  → 각 전문가가 독립적으로 캠페인 기획안 작성
  → 전략가: 전략 프레임워크 중심
  → 크리에이터: 크리에이티브 컨셉 중심
  → 데이터 분석가: KPI/ROI 중심

Step 4: Agent Teams 토론
  → 3개 기획안의 장단점 교차 평가
  → 서로의 기획안에 대해 건설적 피드백

Step 5: 최적안 선택 + 구조화
  → 가장 강력한 기획안 선택 (또는 하이브리드)
  → campaign_brief.md 최종 확정

Step 6: 웹앱 시각화
  → 기획안을 웹앱으로 시각화 (선택)

Step 7: 제안서 연계
  → BriefAdapter가 campaign_brief.md를 제안서 형식으로 자동 변환
  → STEP 1~2 스킵, STEP 3(기획)부터 파이프라인 실행
```

---

## 6. 에이전트 구조

### 디렉토리 구조

```
제안서 에이전트/
├── CLAUDE.md                          # 프로젝트 아키텍처
├── main.py                           # 엔트리포인트
├── requirements.txt
│
├── src/
│   ├── orchestrators/
│   │   └── pipeline_orchestrator.py   # 5단계 파이프라인 오케스트레이터
│   ├── agents/                        # 에이전트 (11개)
│   │   ├── analysis_agent.py          # STEP 1: 분석
│   │   ├── research_agent.py          # STEP 2: 리서치
│   │   ├── planning_agent.py          # STEP 3: 기획 조율
│   │   │   └── planning/
│   │   │       ├── structure_planner.py
│   │   │       ├── script_planner.py
│   │   │       ├── layout_planner.py
│   │   │       └── design_planner.py
│   │   ├── production_agent.py        # STEP 4: PPTX 생성
│   │   ├── qa_agent.py               # STEP 4: QA 검수
│   │   ├── design_agent.py           # STEP 5: 디자인 변환
│   │   └── brief_adapter.py          # 브레인스토밍→제안서 연계
│   ├── generators/
│   │   └── slide_kit.py              # PPTX 렌더링 엔진 (30 레이아웃, 6 테마)
│   ├── schemas/                       # Pydantic 스키마
│   └── parsers/                       # PDF/DOCX 파서
│
├── .claude/
│   ├── commands/start.md              # /start 가이드
│   ├── rules/                         # 자동 로드 규칙 (3개)
│   └── agents/                        # 브레인스토밍 에이전트 (3명)
│
├── figma-plugin/                      # HTML→Figma 변환 플러그인
│   ├── manifest.json                  # Figma 플러그인 매니페스트
│   ├── render.js                      # Puppeteer HTML→JSON 렌더러
│   ├── src/code.ts                    # Figma 요소 생성 (절대 좌표)
│   ├── src/ui.ts                      # 플러그인 UI
│   └── dist/                          # 빌드 결과
│
├── config/prompts/                    # Phase별 프롬프트 템플릿
├── 제안요청서/                         # RFP 입력
├── input/                             # 디자인 레퍼런스
└── projects/                          # 프로젝트별 출력
```

### 에이전트 테이블

| Stage | 에이전트 | 파일 | 역할 |
|-------|---------|------|------|
| 1 | AnalysisAgent | `analysis_agent.py` | RFP/기획안 분석 |
| 2 | ResearchAgent | `research_agent.py` | 시장/경쟁/트렌드 조사 |
| 3 | PlanningAgent | `planning_agent.py` | 4개 서브에이전트 조율 |
| 3-1 | StructurePlanner | `structure_planner.py` | Phase별 구조 기획 |
| 3-2 | ScriptPlanner | `script_planner.py` | Action Title + 콘텐츠 |
| 3-3 | LayoutPlanner | `layout_planner.py` | 30종 레이아웃 배정 |
| 3-4 | DesignPlanner | `design_planner.py` | 6종 테마 + 디자인 |
| 4 | ProductionAgent | `production_agent.py` | slide_kit 코드 생성 + PPTX |
| 4 | QAAgent | `qa_agent.py` | 겹침/폰트/컬러 검수 |
| 5 | DesignAgent | `design_agent.py` | 프롬프트→HTML→Figma |
| - | BriefAdapter | `brief_adapter.py` | 브레인스토밍→제안서 연계 |

### 출력 구조

```
projects/[프로젝트명]/output/
├── 01_analysis.json           # RFP 분석 결과
├── 02_research.json           # 리서치 결과
├── 03_plan.json               # 기획 결과 (구조+스크립트+레이아웃+디자인)
├── 04_production/
│   ├── generate_제안서.py     # PPTX 생성 스크립트
│   ├── 제안서.pptx            # 납품용 PPTX
│   └── 04_qa_report.json     # QA 검수 결과
└── 05_design/
    ├── DESIGN_GUIDE.md        # 디자인 작업 가이드
    ├── design_system.json     # 디자인 시스템
    ├── prompts/               # Gemini 프롬프트
    │   ├── slide_000.md
    │   └── ...
    └── html/
        ├── presentation.html      # 완성 HTML
        └── presentation.figma.json # Figma 임포트용 JSON
```

---

## 7. 커스터마이징

### 테마 변경

```
"테마를 corporate(네이비)로 변경해줘"
```

| 테마 | 설명 | 용도 |
|------|------|------|
| warm_minimal | 따뜻한 베이지 (기본) | 범용 |
| classic_blue | 클래식 네이비 블루 | 전통적 기업 |
| forest | 포레스트 그린 | 자연/ESG/환경 |
| corporate | 코퍼레이트 네이비 | 금융/공공/대기업 |
| mono_black | 모노 블랙 | IT/테크/미니멀 |
| soft_purple | 소프트 퍼플 | 크리에이티브/뷰티 |

### 콘텐츠 수정

```
"Action Title을 더 임팩트 있게 바꿔줘"
"WHY US에 수행실적 3건을 추가해줘"
"KPI 목표를 팔로워 +30%에서 +50%로 변경해줘"
"전체를 100장에서 70장으로 줄여줘"
```

### 디자인 수정

```
"KPI 숫자를 72px로 크게 해줘"
"표지에 브랜드 로고를 넣어줘"
"CONCEPT 섹션에 다크 배경 슬라이드를 추가해줘"
```

---

## 8. 트러블슈팅

### /start가 안 될 때

| 원인 | 해결 |
|------|------|
| 작업 디렉토리 불일치 | 프로젝트 루트에서 Claude Code 실행 중인지 확인 |
| 대체 호출 | "제안서 만들어줘", "RFP 분석 시작" 등 자연어로도 동작 |

### PPTX 생성 오류

| 원인 | 해결 |
|------|------|
| 폰트 오류 | Pretendard 폰트 설치 확인 |
| 겹침 발생 | QA에서 자동 감지 → 재생성 (최대 2회) |
| 레이아웃 단조로움 | 연속 3장 동일 레이아웃 자동 방지 |

### Figma 변환 오류

| 원인 | 해결 |
|------|------|
| Puppeteer 미설치 | `cd figma-plugin && npm install` |
| 플러그인 미등록 | Figma > Plugins > Import plugin from manifest > `manifest.json` |
| JSON 파일 없음 | `node render.js [HTML경로]` 실행 확인 |
| 텍스트 누락 | JSON에 color 속성 포함 확인 (render.js v5.1+) |

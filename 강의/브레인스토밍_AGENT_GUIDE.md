# 브레인스토밍 에이전트 - 구축 & 사용 가이드

---

## 1. 프롬프트 (사용자 요청)

```
캠페인 기획을 3명의 AI 전문가(전략가, 크리에이터, 데이터 분석가)가
각자 독립적으로 브레인스토밍하고, 서로 토론해서 최적안을 도출하는
에이전트를 만들어줘.
기획안이 완성되면 자동으로 제안서 제작 파이프라인으로 연계되어야 해.
```

---

## 2. 입력 데이터

### 캠페인 정보 (Step 2에서 수집)

에이전트가 대화를 통해 아래 정보를 수집합니다:

| 항목 | 설명 | 예시 |
|------|------|------|
| 브랜드/제품 | 캠페인 대상 | "서울시 청년정책" |
| 캠페인 목표 | 달성하려는 것 | "SNS 채널 운영 + 청년 인지도 향상" |
| 타겟 오디언스 | 핵심 대상 | "서울 거주 20~30대 청년" |
| 예산 | 총 캠페인 예산 | "4억원" |
| 기간 | 캠페인 기간 | "12개월" |
| 참고 자료 | RFP, 브리프 등 | `제안요청서/` 폴더 파일 |

수집된 정보는 `campaign_input.md`로 저장됩니다.

---

## 3. 설치 및 실행

### 사전 준비

```bash
# 프로젝트 폴더로 이동
cd "제안서 에이전트"

# Python 의존성 설치
pip install -r requirements.txt
```

### 실행 방법

```bash
# Claude Code에서 시작
/start → A 선택 (브레인스토밍 풀 코스)

# 또는 브레인스토밍만 직접 실행
/brainstorm
```

---

## 4. 사용 방법 (7단계 워크플로우)

### 전체 흐름

```
Step 1. 인사 & 프로세스 소개
  ↓
Step 2. 캠페인 정보 수집 → campaign_input.md
  ↓
Step 3. 3인 에이전트 개별 브레인스토밍 (순차)
  ├─ 3-1. 전략가 → brainstorm_strategy.md
  ├─ 3-2. 크리에이터 → brainstorm_creative.md
  └─ 3-3. 데이터 분석가 → brainstorm_data.md
  ↓
Step 4. Agent Teams 토론 (3라운드) → debate_log.md
  ↓
Step 5. 기획안 구조화 → campaign_brief.md (9개 섹션)
  ↓
Step 6. 웹앱 시각화 → campaign_dashboard.html
  ↓
Step 7. 제안서 연계 → BriefAdapter → 제안서 STEP 3부터
```

### Step 1: 인사 & 프로세스 소개

에이전트가 전체 7단계 프로세스를 안내합니다.

### Step 2: 캠페인 정보 수집

에이전트가 대화를 통해 캠페인 정보를 수집하고 `campaign_input.md`로 저장합니다.

### Step 3: 3인 에이전트 개별 브레인스토밍

3명의 AI 전문가가 **순차적으로** 독립 기획안을 작성합니다:

#### 3-1. 전략가 (Campaign Strategist)

**관점**: "어떻게 이겨야 하는가?"

| 분석 항목 | 내용 |
|----------|------|
| PEST 분석 | 정치·경제·사회·기술 환경 → 캠페인 시사점 |
| 3C 분석 | 자사 강점 / 경쟁사 3~5개 벤치마크 / 고객 니즈 |
| 타겟 페르소나 | 이름, 나이, 직업, 일상, 미디어 소비 패턴 |
| 포지셔닝 기회 | 시장 공백 + 차별화 포인트 |
| 3개 전략 방향 | 각각 근거 + 강점 + 리스크 + 예상 ROI |

**입력**: `campaign_input.md`
**출력**: `brainstorm_strategy.md`

#### 3-2. 크리에이터 (Campaign Creator)

**관점**: "어떻게 보여줘야 하는가?"

| 산출물 | 내용 |
|--------|------|
| 3개 크리에이티브 컨셉 | Big Idea + 슬로건 + 비주얼 방향 + 레퍼런스 |
| 메시지 체계 | Key Message → Supporting → Proof Point |
| 채널 콘텐츠 플랜 | 채널별 역할 + 콘텐츠 유형 + 포맷 + 빈도 |
| 톤앤매너 가이드 | 보이스 성격 + 말투 + 금지 표현 + 비주얼 무드 |
| 캠페인 네이밍 | 3개 후보 + 의미 + 활용 방안 |

**입력**: `campaign_input.md` + `brainstorm_strategy.md`
**출력**: `brainstorm_creative.md`

#### 3-3. 데이터 분석가 (Campaign Data Analyst)

**관점**: "어떻게 증명해야 하는가?"

| 산출물 | 내용 |
|--------|------|
| 업계 벤치마크 | 채널별 CTR, VTR, CPC, CPM 평균치 |
| 경쟁사 디지털 성과 | 검색량, 팔로워, 반응률, 추정 광고비 |
| 전략별 데이터 평가 | 타겟 도달 / 예산 효율 / 경쟁 강도 / ROAS |
| 예산 배분 최적화 | 채널 믹스 + 시나리오 분석 (낙관/중립/비관) |
| KPI 프레임워크 | 핵심 KPI + 목표치 + 측정 방법 + 산출근거 |

**입력**: `campaign_input.md` + `brainstorm_strategy.md` + `brainstorm_creative.md`
**출력**: `brainstorm_data.md`

### Step 4: Agent Teams 토론

3개 기획안을 놓고 **3라운드 토론**을 진행합니다:

```
Round 1: 교차 리뷰
  → 3개 기획안의 공통점 vs 충돌점 식별

Round 2: 강제 반론 (contention)
  → 각 에이전트가 다른 기획안에 반드시 반론 제시
  → "이 전략의 약점은...", "이 컨셉의 리스크는..."
  → 반론을 통해 약점 발견 → 보완

Round 3: 통합 최적안 도출
  → 가장 강력한 전략 + 컨셉 + KPI 조합 합의
  → 또는 하이브리드 (각 기획안의 장점만 결합)
```

**출력**: `debate_log.md`

### Step 5: 기획안 구조화

토론 결과를 **9개 섹션**으로 구조화합니다:

| 섹션 | 내용 |
|------|------|
| 1. 프로젝트 개요 | 브랜드, 목표, 기간, 예산 |
| 2. 타겟 & 인사이트 | 페르소나 + 핵심 인사이트 3개 (출처 포함) |
| 3. 캠페인 전략 | 포지셔닝 + **Win Theme 3개** (필수) |
| 4. 크리에이티브 컨셉 | Big Idea + 슬로건 + 메시지 체계 + 톤앤매너 |
| 5. 채널 & 콘텐츠 플랜 | 채널별 역할 + 콘텐츠 유형 + 핵심 KPI + 예산 비중 |
| 6. KPI & 성과 목표 | KPI + 목표치 + 벤치마크 + 측정 방법 + 산출근거 |
| 7. 예산 배분 | 항목별 비율 + 금액 (합계 = 총 예산) |
| 8. 실행 타임라인 | 주차별 활동 + 채널 + 산출물 |
| 9. 리스크 & 대응 | 리스크 + 확률 + 영향도 + 대응 방안 |

**출력**: `campaign_brief.md` (Single Source of Truth)

### Step 6: 웹앱 시각화

기획안을 인터랙티브 HTML 대시보드로 시각화합니다.

**출력**: `campaign_dashboard.html`

### Step 7: 제안서 연계

`BriefAdapter`가 기획안을 제안서 파이프라인 입력 형식으로 자동 변환합니다:

```
campaign_brief.md
  ↓ BriefAdapter
  ├─ RFPAnalysis JSON (제안서 분석 결과 형식)
  └─ ResearchResult JSON (리서치 결과 형식)
  ↓
제안서 STEP 3 (기획) 부터 자동 실행
  → STEP 1(분석), STEP 2(리서치) 스킵
```

### 스마트 재개

작업 중간에 끊겨도 파일 존재 여부로 자동 재개합니다:

| 존재하는 파일 | 재개 지점 |
|-------------|---------|
| `campaign_brief.md` | Step 6 (웹앱) |
| `brainstorm_data.md` | Step 5 (구조화) |
| `brainstorm_creative.md` | Step 4 (토론) |
| `brainstorm_strategy.md` | Step 3-2 (크리에이터) |
| `campaign_input.md` | Step 3-1 (전략가) |

---

## 5. 에이전트 구조

### 파일 구조

```
제안서 에이전트/
├── .claude/
│   ├── commands/brainstorm.md         # /brainstorm 커맨드 정의
│   └── agents/                        # 3명의 AI 전문가 정의
│       ├── campaign-strategist.md     # 전략가
│       ├── campaign-creator.md        # 크리에이터
│       └── campaign-data-analyst.md   # 데이터 분석가
│
├── src/agents/
│   └── brief_adapter.py              # 기획안→제안서 연계 변환
│
└── output/[프로젝트명]/               # 산출물
    ├── campaign_input.md              # Step 2: 수집된 캠페인 정보
    ├── brainstorm_strategy.md         # Step 3-1: 전략가 기획안
    ├── brainstorm_creative.md         # Step 3-2: 크리에이터 기획안
    ├── brainstorm_data.md             # Step 3-3: 데이터 분석가 기획안
    ├── debate_log.md                  # Step 4: 토론 기록
    ├── campaign_brief.md              # Step 5: 최종 기획안 (9개 섹션)
    └── campaign_dashboard.html        # Step 6: 웹앱 대시보드
```

---

## 6. 커스터마이징

### 에이전트 관점 수정

```
"전략가에 ESG/지속가능성 관점을 추가해줘"
"크리에이터에 MZ세대 트렌드 분석 역할을 추가해줘"
"데이터 분석가에 소셜 리스닝 분석을 추가해줘"
```

### 토론 구조 수정

```
"토론을 4라운드로 늘려줘 — 최종 라운드에서 예산 시뮬레이션까지"
"각 에이전트가 자기 기획안을 3분 프레젠테이션하는 라운드 추가해줘"
```

### 기획안 섹션 수정

```
"campaign_brief에 '기대효과' 섹션을 추가해줘"
"예산 배분에 월별 집행 계획을 추가해줘"
"타임라인을 주차가 아닌 월별로 변경해줘"
```

---

## 7. 트러블슈팅

| 문제 | 해결 |
|------|------|
| /brainstorm이 안 됨 | `/start` → A 선택으로 대체, 또는 "브레인스토밍 시작" 자연어 |
| 에이전트 기획이 피상적 | campaign_input.md에 더 구체적인 정보 입력 (경쟁사, 벤치마크 등) |
| 토론이 형식적 | contention 원칙 강화 — "반드시 약점을 2개 이상 지적해야 함" |
| 제안서 연계 실패 | campaign_brief.md 9개 섹션 + Win Theme 3개 완성 확인 |
| 중간에 끊김 | 자동 재개 — 기존 파일 감지하여 이어서 진행 |

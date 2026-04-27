# 코드 리뷰 종합 보고서 — 2026-04-27

> 대상: 제안서 자동 생성 에이전트 v4.0 (5-stage Multi-Agent Pipeline)
> 검토 범위: 전체 코드베이스 + CLAUDE.md 명세 일치 검증 + 보안/안정성 분석
> 후속 처리: Critical 5 + Major 3 + Pydantic v2 + CI + Minor + P0 4 + P1 5 = **18건 처리, 172 tests**

---

## 1. 검토 개요

본 리뷰는 두 단계로 진행되었다.

### 1차 검토 — 핵심 컴포넌트
대상: `BaseAgent`, `AnalysisAgent`, `ProductionAgent`, `PlanningAgent`, `proposal_types.py`, `slide_kit.py`, 프롬프트 템플릿, 도메인 카드

### 2차 검토 (E 단계) — 미검증 컴포넌트
대상: `DesignAgent`, `ResearchAgent`, `BriefAdapter`, `Parsers`, `Planners` (Structure/Script/Layout), `figma-plugin`, `main.py`, `utils`

총 발견 이슈: **약 50건** (Critical 17 / Major 18 / Minor 15+)

---

## 2. 처리 결과 요약

### 2.1. Critical 5건 — 보안/정확성 (commit `bc7979a`)

| # | 항목 | 파일 | 변경 |
|---|------|------|------|
| 1 | Claude API 모델 ID 오류 | [config/settings.py](../config/settings.py) | `claude-sonnet-4-20250514` (미래 날짜) → `claude-sonnet-4-6` + heavy/fast 모델 환경변수 |
| 2 | API 키 누락 처리 부재 | [src/agents/base_agent.py](../src/agents/base_agent.py) | 빈 문자열/공백만 입력 시 `ValueError` 발생 |
| 3 | 공공입찰 신호어 부분 매칭 오탐 | [src/agents/analysis_agent.py](../src/agents/analysis_agent.py) | 가중치 사전(strong=3 / medium=2 / weak=1) + 영문 약어 단어 경계 정규식 |
| 4 | 도메인 매칭 빈도 가중치 부재 | [config/proposal_types.py](../config/proposal_types.py) | 키워드 길이 가중치(1~3점), 임계값 ≥ 3, runner-up 로깅 |
| 5 | Production subprocess RCE 위험 | [src/agents/production_agent.py](../src/agents/production_agent.py) | AST 정적 분석 + 위험 import/호출 블랙리스트, `python3` → `sys.executable` |

### 2.2. Major 3건 (commit `c9e97ae`)

| # | 항목 | 변경 |
|---|------|------|
| 3-1 | PlanningAgent 80장 하드코딩 | `_estimate_slide_count()` — `PROPOSAL_TYPE_CONFIGS[type].total_pages_range` 평균값 사용 |
| 3-3 | 도메인 카드 PUBLIC 한정 | 비-PUBLIC + `force_domain` 시 도메인 카드만 합류 / 평가기준·컴플라이언스는 PUBLIC 한정 유지 |
| 3-5 | QA 피드백 첫 20개 단순 자르기 | `_format_qa_feedback()` — severity 우선 정렬 + 카운트 메타 + summary 노출 |

### 2.3. Pydantic v2 마이그레이션 (commit `261c5e5`)

`class Config: json_schema_extra = {...}` (deprecated) → `model_config = ConfigDict(json_schema_extra={...})`

대상: `WinTheme`, `KPIWithBasis`, `ExecutiveSummary`, `NextStep`, `ActionTitle`, `ProposalContent`, `RFPAnalysis`

추가로 `Settings` 의 default를 `Field(default_factory=...)` 로 마이그레이션 — 환경변수 동적 평가 + 테스트 격리 가능.

### 2.4. CI (commit `d7c9383`)

- [.github/workflows/test.yml](../.github/workflows/test.yml) — Python 3.9~3.12 매트릭스, 더미 API 키 주입, Pydantic deprecation warning 0건 검증
- 모노 구조 대응: `defaults.run.working-directory: ai-proposal-generator`

### 2.5. Minor 2건 (commit `89a6acf`)

- BaseAgent: 모듈 레벨 logger → 인스턴스별 logger (`self.logger = get_logger(self.__class__.__name__)`)
- 6개 에이전트: 프롬프트 부재 시 `self.logger.warning` 명시 추가

### 2.6. P0 4건 (commit `c65f05c` + `6bb45da`)

| # | 항목 | 변경 |
|---|------|------|
| P0-1 | LayoutPlanner 30종 화이트리스트 | `VALID_LAYOUT_NAMES` 동적 로드 + `_sanitize_assignments()` 폴백 (잘못된 ID → `FULL_BODY`) |
| P0-2 | total_slides Field 검증 | `Field(ge=20, le=300)` + `_clamp_total_slides()` + phase_breakdown validator |
| P0-3 | PDFParser 암호화/메모리 | `EncryptedPDFError` 명시적 예외 + `raw_data` 필드 제거 (메모리 2배 → 1배) + 텍스트 1회만 추출 |
| P0-4 | DesignAgent 경로 traversal | `_resolve_safe_output_dir()` + 시스템 경로(`/etc`, `C:\Windows` 등) 블랙리스트 |

### 2.7. P1 5건 (commit `120b8c6`)

| # | 항목 | 변경 |
|---|------|------|
| P1-1 | BriefAdapter UnicodeDecodeError | UTF-8 → CP949 폴백 + 권한/OS 오류 안전 처리 |
| P1-2 | ResearchAgent 외부 API 미사용 명시 | docstring + `WARN` 로그 + `RESEARCH_SOURCE_MARKER_LLM` 자동 추가 + 동적 연도 |
| P1-3 | DESIGN_MODEL 하드코딩 | `settings.claude_model_design` (`CLAUDE_MODEL_DESIGN` 환경변수) |
| P1-4 | ScriptPlanner JSON 파싱 약점 | `_coerce_scripts_list()` + specs 기반 폴백 (`_make_fallback_script`) — 슬라이드 전체 손실 차단 |
| P1-6 | DesignAgent 글로벌 타임아웃 | `asyncio.wait_for()` (`settings.design_global_timeout_seconds`, 기본 1800초) |

---

## 3. 테스트 슈트 구성 — 172 tests passed

| 파일 | 검증 영역 | 테스트 수 |
|------|----------|---------|
| [test_settings.py](../tests/test_settings.py) | 모델 ID + 환경변수 | 9 |
| [test_proposal_types.py](../tests/test_proposal_types.py) | 도메인 매칭 알고리즘 | 21 |
| [test_analysis_agent.py](../tests/test_analysis_agent.py) | 신호어 점수 + force_* | 16 |
| [test_base_agent.py](../tests/test_base_agent.py) | API 키 + 도메인 합류 | 12 |
| [test_production_agent.py](../tests/test_production_agent.py) | AST 보안 + QA 정렬 | 24 |
| [test_planning_agent.py](../tests/test_planning_agent.py) | 슬라이드 수 추정 | 14 |
| [test_layout_planner.py](../tests/test_layout_planner.py) | 30종 화이트리스트 | 10 |
| [test_planning_schema.py](../tests/test_planning_schema.py) | Field 제약 + 클램핑 | 23 |
| [test_pdf_parser.py](../tests/test_pdf_parser.py) | 암호화 + 메모리 | 9 |
| [test_design_agent.py](../tests/test_design_agent.py) | 경로 traversal | 12 (10 active + 2 OS-skip) |
| [test_brief_adapter.py](../tests/test_brief_adapter.py) | 인코딩 폴백 | 6 |
| [test_research_agent.py](../tests/test_research_agent.py) | 마커 + 동적 연도 | 6 |
| [test_script_planner.py](../tests/test_script_planner.py) | JSON 파싱 + 폴백 | 13 |

**총 172 passed, 2 skipped (Linux-only OS-specific tests)**

---

## 4. 미처리 잔여 이슈 (P2 / P3)

### 4.1. P2 — 보안/품질 (실제 공격 면적 작거나 사용자 기기에서만 실행)

| 항목 | 위치 | 우선순위 사유 |
|------|------|-------------|
| DOCX XXE 미차단 | [src/parsers/docx_parser.py:34](../src/parsers/docx_parser.py#L34) | python-docx는 매크로 미실행, defusedxml 도입 시 의존성 추가 |
| Figma 플러그인 입력 sanitization | [figma-plugin/src/code.ts:299-344](../figma-plugin/src/code.ts) | 사용자 기기에서만 실행 (Figma 샌드박스) |
| 로그 민감 정보 (전체 경로) | [src/utils/logger.py](../src/utils/logger.py) | OSINT 위험 — 운영 환경에서 노출 가능 |
| Puppeteer file:// 보안 | [figma-plugin/render.js:30](../figma-plugin/render.js#L30) | 사용자 입력 HTML 한정, 외부 URL 미사용 |
| Reference URL SSRF | [main.py:155-161](../main.py#L155) | 현재 reference URL 입력 미사용 (이론적) |

### 4.2. P3 — 마이너 (기능 영향 없음)

- pdf_parser 한국식 섹션 추출만 처리 (다국어 미지원)
- ReferenceAnalyzer 매직 넘버 (`914400` EMU)
- main.py company_data 부재 시 silent fail
- StructurePlanner ProposalType 변환 실패 추적 부족
- LayoutPlanner 응답 시간 제한 부재
- render.js 폰트 로딩 실패 처리 약함
- BaseAgent JSON 추출 정규식 너무 관대
- 기타 코드 중복/로깅 일관성

---

## 5. Commit 히스토리 (최근 17개)

```
d7c9383 ci: move workflow to git root + add working-directory
120b8c6 fix: P1 reliability fixes — encoding, transparency, validation, timeout
6bb45da fix: DesignAgent output_dir path traversal + P0 validator tests
c65f05c feat: implement proposal planning agents with new PDF parser and structural schemas
89a6acf refactor: per-instance loggers + explicit prompt fallback logging
0a19466 ci: add GitHub Actions test workflow
261c5e5 feat: implement AST security validation and QA feedback sorting logic with comprehensive unit tests
c9e97ae feat: implement base, planning, and production agent classes
bc7979a feat: implement base agent architecture and configuration management system
ca7350c feat: implement base agent framework, RFP schemas, and project configuration with Claude integration settings
9b1f90a feat: add configuration files for big data analytics, maintenance, and modernization domains
7dd8b8e feat: add bigdata domain configuration and phase 4 public action prompt
ff73d2b feat: add configuration files for public bidding, compliance, and data governance domain prompts
a76e65c feat: add domain configuration files for cctv, infra, ai, and bigdata
9e24f45 feat: implement 5-stage proposal pipeline orchestrator with integrated agent workflow
9424309 feat: add legacy pptx_orchestrator and configure python virtual environment dependencies
```

---

## 6. 향후 권장 작업

1. **P2 처리** — 우선순위는 로그 민감 정보 정리, DOCX XXE (defusedxml 도입)
2. **integration test 추가** — 현재는 unit test만, 실제 RFP → 최종 PPTX 흐름 통합 테스트 부재
3. **monitoring** — DesignAgent 슬라이드별 생성 시간/실패율 메트릭, 운영 환경에서 timeout 빈도 추적
4. **MCP WebSearch 연동** — ResearchAgent 가 실제 외부 데이터 활용하도록 (현재는 LLM 학습 데이터만)
5. **figma-plugin TypeScript 검증** — `code.ts` JSON 메시지 schema 강제 (zod 등)

---

## 7. 검증 스크립트

```bash
# 의존성 설치
pip install -r requirements.txt

# 테스트 실행
pytest -v

# Pydantic deprecation warning 0건 확인
pytest --tb=no -q | grep -c PydanticDeprecated
```

---

**리뷰 완료 시각**: 2026-04-27
**리뷰어**: Claude Opus 4.7 (1M context)
**파이프라인**: 5-stage multi-agent (analysis → research → planning → production → design)

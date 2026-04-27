---
paths:
  - "output/**/*.py"
  - "src/generators/**/*.py"
---

# 레이아웃 및 디자인 규칙

## 레이아웃 36종 선택 가이드

### 기본
| 콘텐츠 유형 | 권장 레이아웃 | slide_kit 함수 |
|------------|-------------|---------------|
| 텍스트 중심/차트 | `FULL_BODY` | Zone 직접 |
| 핵심 인사이트 | `HIGHLIGHT_BODY` | `HIGHLIGHT()` + `MT()` |

### 컬럼
| 콘텐츠 유형 | 권장 레이아웃 | slide_kit 함수 |
|------------|-------------|---------------|
| 좌우 비교/병렬 | `TWO_COL` | Zone 직접 |
| 3개 카테고리 | `THREE_COL` | `COLS()` |
| 4개 포인트 | `FOUR_COL` | `ICON_CARDS()` |

### 비교/데이터
| 콘텐츠 유형 | 권장 레이아웃 | slide_kit 함수 |
|------------|-------------|---------------|
| AS-IS / TO-BE | `COMPARE_LR` | `COMPARE()` |
| 강조 + 3카드 | `HIGHLIGHT_THREE_CARD` | `HIGHLIGHT()` + `COLS()` |
| KPI/성과 목표 | `KPI_GRID` | `KPIS()` |
| 가로 통계 바 | `STAT_ROW` | `STAT_ROW()` |
| 테이블 + 인사이트 | `TABLE_INSIGHT` | `TABLE()` |

### 프로세스
| 콘텐츠 유형 | 권장 레이아웃 | slide_kit 함수 |
|------------|-------------|---------------|
| 실행 프로세스 | `PROCESS_DESC` | `FLOW()` |
| 일정/로드맵 | `TIMELINE_DESC` | `TIMELINE()` |

### 구조
| 콘텐츠 유형 | 권장 레이아웃 | slide_kit 함수 |
|------------|-------------|---------------|
| 전략 프레임워크 | `PYRAMID_DESC` | `PYRAMID()` |
| 우선순위 분석 | `MATRIX_DESC` | `MATRIX()` |
| 사이드바 + 콘텐츠 | `SIDEBAR_CONTENT` | Zone 직접 |

### 이미지+텍스트
| 콘텐츠 유형 | 권장 레이아웃 | slide_kit 함수 |
|------------|-------------|---------------|
| 좌 이미지 + 우 텍스트 | `KEY_VISUAL` | `IMG()` + Zone |
| 좌 텍스트 + 우 이미지 | `LEFT_TEXT_RIGHT_IMG` | Zone 직접 |
| 상 이미지 + 하 텍스트 | `TOP_IMG_BOTTOM_TEXT` | Zone 직접 |

### 조직/일정
| 콘텐츠 유형 | 권장 레이아웃 | slide_kit 함수 |
|------------|-------------|---------------|
| 조직도 | `ORG_CHART` | `ORG()` |
| 리스크 관리 | `RISK_CARD` | Zone 직접 |
| 간트 차트 | `GANTT` | `GANTT_CHART()` |

### 스페셜/리스트/그리드/카드
| 콘텐츠 유형 | 권장 레이아웃 | slide_kit 함수 |
|------------|-------------|---------------|
| 다크/라이트 분할 | `SPLIT_DARK_LIGHT` | `R()` + Zone |
| 중앙 인용문 | `QUOTE_CENTER` | `QUOTE()` |
| 대형 숫자 강조 | `METRIC_HIGHLIGHT` | `METRIC_CARD()` |
| 체크리스트 | `CHECKLIST` | `MT()` (bul=True) |
| 번호 단계 설명 | `NUMBERED_STEPS` | `NUMBERED_LIST()` |
| 2×3 그리드 | `TWO_ROW_THREE_COL` | `GRID()` |
| 도넛 + 통계 | `DONUT_STATS` | `PIE_CHART()` + Zone |
| 아젠다 리스트 | `AGENDA_LIST` | Zone 직접 |
| 아이콘 4단 카드 | `ICON_CARD_4` | `ICON_CARDS()` |

### 신규 6종 (A4 세로 친화 + 패턴 확장)
| 콘텐츠 유형 | 권장 레이아웃 | slide_kit 함수 | 권장 포맷 |
|------------|-------------|---------------|---------|
| 세로 5단계 | `VERTICAL_STEPS` | Zone 직접 (좌측 번호 + 우측 본문) | A4 세로 |
| 세로 타임라인 | `TIMELINE_VERTICAL` | Zone 직접 (좌측 시점 + 우측 이벤트) | A4 세로 |
| 핵심 KPI 1개 강조 | `HEADLINE_NUMBER` | `METRIC_CARD()` + `T()` | 모든 포맷 |
| 카드 6개 (사례·서비스) | `CARD_GRID_6` | `GRID()` 또는 `CARD()` | 모든 포맷 |
| 긴 목차 (10항목) | `AGENDA_TWO_COL` | Zone 직접 (좌5 + 우5) | 모든 포맷 |
| 가격/플랜 비교 (3) | `PRICING_TABLE` | Zone 직접 (3 헤더+가격+기능) | 모든 포맷 |

## 겹침/공백 방지 규칙

### 요소 간 최소 간격 (인치)
- HIGHLIGHT -> 다음 요소: 0.75"
- COLS -> 다음 요소: 0.30"
- METRIC_CARD -> 다음 요소: 0.15"
- MT(불릿) -> 다음 요소: 0.20"

### 레이아웃 배정 원칙
- 연속 3장 같은 레이아웃 금지 (시각 단조로움 방지)
- Phase별로 다양한 레이아웃 배분
- 데이터 많은 슬라이드: TABLE_INSIGHT, STAT_ROW
- 메시지 중심: HIGHLIGHT_BODY, QUOTE_CENTER, METRIC_HIGHLIGHT

### 한글 텍스트 너비 추정
- 44pt: 0.61"/자 -> CW 내 최대 ~18자
- 36pt: 0.50"/자 -> CW 내 최대 ~23자
- 44pt 제목이 18자 초과 시 반드시 2줄 분리

## 디자인 테마 (10종)

### 기존 6종
| 테마 | 여백 | 표지 크기 | 용도 |
|------|------|----------|------|
| `warm_minimal` (기본) | 1.2" | 48pt | 범용, 미니멀 |
| `classic_blue` | 0.8" | 60pt | 전통적 기업 제안서 |
| `forest` | 1.0" | 52pt | 자연/ESG/환경 |
| `corporate` | 0.9" | 54pt | 금융/공공/대기업 |
| `mono_black` | 1.0" | 52pt | IT/테크/미니멀 |
| `soft_purple` | 1.0" | 50pt | 크리에이티브/뷰티 |

### 신규 4종
| 테마 | 여백 | 표지 크기 | 용도 |
|------|------|----------|------|
| `sunset_orange` | 1.0" | 56pt | 마케팅/스타트업/F&B (따뜻한 오렌지) |
| `ocean_teal` | 1.0" | 52pt | 헬스/테크/교육 (청록·민트) |
| `gold_luxury` | 0.9" | 58pt | 프리미엄/금융/럭셔리 (골드·블랙) |
| `arctic_white` | 1.1" | 50pt | 의료/IT/미니멀 (화이트·실버·블루) |

## Phase 3 필수 컨셉 장표 (3종)
1. **Concept Reveal** - 다크 배경, 60pt 대형 컨셉 키워드, 4단계 순환 카드
2. **Strategy Synergy Map** - 3대 Win Theme 연결 구조, 순환 흐름도
3. **Big Idea Reveal** - 36pt 중앙 컨셉 + 3-Step 카드

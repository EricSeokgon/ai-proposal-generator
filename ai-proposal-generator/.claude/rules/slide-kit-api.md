---
paths:
  - "output/**/*.py"
  - "src/generators/**/*.py"
---

# slide_kit API 사용 규칙

## 필수 import 패턴

모든 제안서 생성 스크립트는 반드시 `src/generators/slide_kit.py`를 import해야 합니다.

```python
import sys, os
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, PROJECT_ROOT)
from src.generators.slide_kit import *
```

## 경로 규칙
- 생성 스크립트: `output/테스트 XX/generate_제안서.py`
- `../..`로 프로젝트 루트까지 올라가서 import
- 절대경로 하드코딩 금지 -> `__file__` 기준 상대경로 사용

## 절대 하지 말 것
- 헬퍼 함수를 스크립트 내에 다시 정의하지 말 것
- RGBColor를 직접 하드코딩하지 말 것 -> `C["primary"]` 사용
- 폰트명을 직접 쓰지 말 것 -> `FONT` 상수 사용
- "맑은 고딕" 등 다른 폰트 사용 금지 -> Pretendard만 사용

## slide_kit 함수 목록 (v3.6)

| 카테고리 | 함수 | 설명 |
|---------|------|------|
| **상수** | `C`, `SW`, `SH`, `ML`, `CW`, `SZ`, `FONT` | 컬러(21색), 크기, 폰트 |
| **상수 (v3.6)** | `FONT_W`, `SHADOW`, `GRAD` | 폰트 웨이트, 그림자 프리셋, 그라디언트 프리셋 |
| **컬러 유틸** | `darken()`, `lighten()` | RGBColor 밝기 조절 |
| **Zone** | `Z`, `GAP`, `CGAP`, `CW_IN`, `ML_IN` | 표준 영역, 간격 |
| **레이아웃** | `LAYOUTS`, `get_zones()`, `zone_to_inches()`, `list_layouts()` | 20가지 프리셋 |
| **도형** | `R()`, `BOX()`, `OBOX()`, `RBOX()`, `ORBOX()`, `CARD()` | 사각형, 텍스트 박스, 라운드, 카드 |
| **텍스트** | `T(fn=)`, `RT()`, `MT()` | 단일/리치/멀티라인 |
| **이펙트** | `gradient_bg()`, `bg()`, `set_char_spacing()`, `gradient_shape()`, `add_shadow(preset=)`, `OVERLAY()` | 배경, 그래디언트, 그림자 |
| **구분/악센트** | `DIVIDER()`, `ACCENT_LINE()` | 구분선, 좌측 악센트 |
| **컴포넌트** | `IMG()`, `PN()`, `TB()`, `SRC()`, `WB()` | 이미지홀더, 페이지번호, 타이틀바, 출처, Win Theme |
| **텍스트 블록** | `QUOTE()`, `NUMBERED_LIST()` | 인용문, 번호 리스트 |
| **도식화** | `FLOW()`, `COLS()`, `PYRAMID()`, `MATRIX()`, `TABLE()`, `HIGHLIGHT()`, `KPIS()`, `COMPARE()`, `TIMELINE()` | 기본 도식 |
| **도식화 확장** | `GRID()`, `STAT_ROW()`, `GANTT_CHART()`, `ORG()`, `ICON_CARDS()` | 그리드, 통계, 간트, 조직도 |
| **차트** | `BAR_CHART()`, `PIE_CHART()`, `LINE_CHART(smooth=)` | 바, 파이/도넛, 라인 |
| **시각화 헬퍼** | `IMG_PH()`, `PROGRESS_BAR()`, `METRIC_CARD()`, `STEP_ARROW()`, `DONUT_LABEL()` | 보조 시각요소 |
| **슬라이드** | `slide_cover()`, `slide_section_divider()`, `slide_toc()`, `slide_exec_summary()`, `slide_next_step()`, `slide_closing()` | 표지, 구분자, 목차, 요약, CTA, 마지막 |
| **자동 배치** | `VStack` | 자동 Y좌표 계산, 겹침 방지 |
| **테마** | `THEMES`, `apply_theme()`, `reset_theme()`, `list_themes()` | 5가지 테마 |
| **검증** | `validate_sequence()` | 레이아웃 시퀀스 검증 |
| **유틸** | `new_presentation()`, `new_presentation_from_template()`, `new_slide()`, `save_pptx()`, `_cols()` | 생성, 템플릿, 저장 |

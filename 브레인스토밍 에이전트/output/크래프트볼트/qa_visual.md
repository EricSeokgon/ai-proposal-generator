# QA Visual Report — 크래프트볼트 proposal.html
검수 일시: 2026-03-27

---

## 요약

| 카테고리 | 🔴 Critical | 🟡 Warning | 🟢 Minor |
|---|---|---|---|
| 레이아웃 | 1 | 3 | 2 |
| 도형 | 0 | 2 | 3 |
| 타이포 | 2 | 4 | 2 |
| **합계** | **3** | **9** | **7** |

---

## 1. 레이아웃 검수

### 🔴 L-01 · 슬라이드 ID/번호 불일치 (전체)
**슬라이드 31번** 이후 HTML ID와 `slide-number` 표시가 1씩 어긋납니다.

| slide-number | HTML id | 실제 섹션 |
|---|---|---|
| `31 / 38` | `slide-32` | KPI 대시보드 |
| `32 / 38` | `slide-33` | 매출 시나리오 |
| … | … | … |
| `38 / 38` | `slide-39` | 투자 효과 |
| `39 / 38` | `slide-40` | 킥오프 (번호 초과) |
| `40 / 38` | `slide-41` | 클로징 (번호 초과) |

총 슬라이드 수도 38이 아닌 40개입니다. `slide-31` ID가 존재하지 않고, `slide-number`가 `39 / 38`, `40 / 38`으로 표시됩니다.

```css
/* 수정: 총 슬라이드 수 상수를 40으로 통일 */
/* slide-number 텍스트 및 slideNames 배열(JS)을 40개로 맞춰야 함 */
/* JS에서 const TOTAL = 40; 으로 수정 후 모든 "XX / 38" → "XX / 40" */
```

---

### 🟡 L-02 · 연속 동일 테마 7연속 (슬라이드 13~18: dark)
슬라이드 13→14→15→16→17→18이 모두 `dark` 테마로 6연속 이어집니다. 권장 3연속 상한을 초과하여 시각적 단조로움이 발생합니다.

```css
/* 권장 조치: 슬라이드 16 또는 17을 light 테마로 전환 */
/* slide-16 (W2 국내 A/S) 또는 slide-17 (1.2kg hero_stat)이 light로도 자연스러움 */
<section class="slide-container light" id="slide-16"> /* 변경 예시 */
```

---

### 🟡 L-03 · 연속 동일 테마 12연속 (슬라이드 19~30: light)
슬라이드 19~30이 모두 `light` 테마로 12연속 이어집니다. 권장 3연속 상한을 크게 초과합니다.

```css
/* 권장 조치: 슬라이드 25(3종 세트), 28(리뷰 확보 플랜) 등을 dark 테마로 전환 */
<section class="slide-container dark" id="slide-25">
<section class="slide-container dark" id="slide-28">
```

---

### 🟡 L-04 · 슬라이드 29 타임라인 그리드 셀 gap 미달
슬라이드 29(12주 통합 타임라인)에서 `grid-template-columns: 100px repeat(4,1fr) 20px ...` 구조의 gap이 `4px`로 설정되어 있습니다. 카드 간 gap 24px 이상 권장 기준 미달입니다. 이 슬라이드는 정보 밀도 때문에 불가피하지만 행 간 구분이 시각적으로 취약합니다.

```css
/* 행 구분 강화: 각 row 사이에 margin-top 추가 */
.tl-grid-row { margin-top: 8px; }
/* 또는 row wrapper에 border-top 적용 */
```

---

### 🟡 L-05 · 슬라이드 14 포지셔닝 삼각형 절대위치 요소
슬라이드 14(3각 포지셔닝)에서 W2/W3 카드가 `position:absolute; bottom:40px; left/right:20px`으로 배치되어 있습니다. `left:20px`은 슬라이드 내부 기준이 아닌 컨테이너 800px 기준이므로, 1920px 캔버스에서 실제 여백이 20px에 불과합니다. 56px+ 권장 기준 미달입니다.

```css
/* 수정: left/right 값을 확대 */
/* W2 bottom-left */
position:absolute; bottom:40px; left:60px; ...
/* W3 bottom-right */
position:absolute; bottom:40px; right:60px; ...
```

---

### 🟢 L-06 · 슬라이드 10 퍼널 가로 너비 가변 (380~740px)
퍼널 단계 박스가 380px→500px→620px→740px으로 하드코딩되어 있습니다. `max-width` 없이 고정값이므로 뷰포트 축소 시 잘림 가능성이 있습니다. 1920px 고정이므로 현재는 괜찮으나, 퍼널 최대 너비가 740px로 좌우 여백이 약 590px씩 남아 공간 낭비가 있습니다.

```css
/* 권장 조치: max-width를 슬라이드 너비의 50~60%로 확장 */
/* 퍼널 최대 1000px까지 확대 가능 */
```

---

### 🟢 L-07 · 슬라이드 6 인라인 stats 박스 gap 20px
슬라이드 06의 하단 3개 통계 박스 `gap:20px`으로, 카드 간 gap 24px 기준에서 4px 미달입니다.

```css
/* 수정 */
<div style="display:flex;gap:24px;"> /* 20px → 24px */
```

---

## 2. 도형 검수

### 🟡 S-01 · border-radius 혼재 (8px / 10px / 12px / 14px / 16px)
전체 파일에서 다음의 border-radius 값이 혼재합니다:
- `8px` — 카드 내 작은 info 박스 (L.1000, 1009, 1018, 1027 등)
- `10px` — 카드 내 bottom summary (L.581, 601, 645, 672 등)
- `12px` — 대부분의 info/stat 박스 (매우 다수)
- `14px` — 슬라이드 35 선순환 다이어그램 step 박스 (L.1996, 2001, 2006, 2011)
- `16px` — `.card`, `.kpi-card`, 주요 컨테이너

규칙: `.card`는 16px로 통일되어 있으나, 카드 내부 서브 요소들이 8/10/12/14px으로 파편화되어 있습니다.

```css
/* 권장: 카드 내부 서브 요소를 12px로 통일 */
/* 8px → 12px, 10px → 12px, 14px → 12px */
/* 예시 (L.1000): border-radius:8px → border-radius:12px */
.card [style*="border-radius:8px"] → border-radius:12px;
.card [style*="border-radius:10px"] → border-radius:12px;
```

---

### 🟡 S-02 · 프로세스 화살표 크기 불일치
슬라이드별 화살표(`&#10132;`) 폰트 크기가 통일되지 않았습니다:

| 슬라이드 | 화살표 크기 | 위치 |
|---|---|---|
| 13, 28 | `font-size:32px` (`.flow-arrow` CSS 클래스) | 전략 플로우 |
| 19, 24, 27, 39 | `font-size:24px` (인라인) | 주간 실행 플로우 |
| 39 (킥오프) | `font-size:20px` (인라인) | 킥오프 스텝 |

```css
/* 권장: 인라인 화살표를 .flow-arrow 클래스 통일 또는 별도 변수로 관리 */
/* 슬라이드 내 주 플로우: 32px */
/* 슬라이드 내 서브 플로우: 24px */
/* 최소 20px 미만 사용 금지 */
.flow-arrow-sm { font-size:24px; color:var(--main); font-weight:900; display:flex; align-items:center; justify-content:center; }
```

---

### 🟢 S-03 · accent-card 상단 스트라이프 색상 미적용
`.accent-card .card-stripe { background:var(--accent); }` 규칙이 CSS에 정의되어 있으나, 슬라이드 08의 PERSONA B 카드에서 스트라이프가 `background:var(--accent)`로 인라인 재정의(L.586)되어 있습니다. 이는 의도적이지만 CSS 규칙과 중복됩니다.

```css
/* 정리: 인라인 스타일 제거하고 .accent-card 클래스만 사용 */
/* <div class="card-stripe" style="background:var(--accent);"> */
/* → <div class="card-stripe"> (accent-card 클래스가 자동 처리) */
```

---

### 🟢 S-04 · box-shadow 슬라이드 컨테이너에만 적용
`.slide-container`에는 `box-shadow:0 8px 32px rgba(0,0,0,0.12)` 1종만 있습니다. 카드에는 box-shadow가 없어 일관성 측면에서 양호합니다. 단, KPI 대시보드(슬라이드 31)의 kpi-card에 shadow 없음은 의도된 플랫 디자인으로 적절합니다.

---

### 🟢 S-05 · 타임라인 연결선 미구현 (슬라이드 29)
슬라이드 29 타임라인은 `.tl-step` / `.tl-marker` / `.tl-connector` CSS 클래스가 정의되어 있으나, 실제 슬라이드 29(12주 통합 타임라인)는 이 클래스를 사용하지 않고 인라인 grid로 구현했습니다. 타임라인 연결선 클래스가 전혀 활용되지 않고 있습니다.

```css
/* 참고: .tl-connector CSS가 정의되어 있으나 사용처 없음 */
/* 향후 타임라인 슬라이드 추가 시 이 클래스를 활용할 것 */
```

---

## 3. 타이포그래피 검수

### 🔴 T-01 · 본문 최소 폰트 미달 (11px, 12px) — 다수 슬라이드
본문 최소 폰트 기준 20px를 크게 하회하는 텍스트가 다수 존재합니다.

**11px 사용 위치 (슬라이드 29 — 12주 타임라인):**
- L.1723~1736: 타임라인 셀 텍스트 `font-size:11px` — 총 12+개 요소

**12px 사용 위치:**
- 슬라이드 23(상세페이지 9단계) L.1354~1394: 9개 서브 설명 텍스트 `font-size:12px`
- 슬라이드 29 W1~W12 헤더 L.1696~1709: `font-size:12px`
- 슬라이드 39(킥오프) L.2247~2280: 서브 설명 `font-size:12px`

```css
/* 수정: 최소 font-size를 16px로 상향 */
/* 슬라이드 29 타임라인 셀 */
/* font-size:11px → font-size:13px (정보 밀도 고려 최소값) */
/* 슬라이드 23 서브 설명 */
/* font-size:12px → font-size:14px */

/* 단, 슬라이드 29는 정보 밀도가 매우 높아 13px이 실질적 최솟값 */
```

---

### 🔴 T-02 · action-title 폰트 기준 미달 (38px/800)
CSS 정의: `.slide-header .action-title { font-size:38px; font-weight:800; }`

기준 위계: Action Title은 36~42px/800으로 `38px`은 범위 내에 있습니다. 다만, 일부 슬라이드에서 action-title 텍스트가 1줄을 초과할 경우 `line-height:1.3`으로 설정되어 있어 2줄 title이 약 99px를 차지합니다. 슬라이드 헤더 영역이 충분히 확보되어 있으나, 특히 긴 제목을 가진 슬라이드(슬라이드 34: "리뷰 선순환 -- 리뷰 100개가 CVR을 2배로 만드는 메커니즘입니다")에서 헤더가 body 공간을 압박할 수 있습니다.

```css
/* 현재 정의: font-size:38px; line-height:1.3 → 유지 (기준 적합) */
/* 개선 권장: 긴 제목 슬라이드에서 font-size를 34px로 낮추거나 */
/* max-height를 설정하여 overflow를 방지 */
.slide-header .action-title {
  font-size:38px; font-weight:800; line-height:1.3;
  max-height:104px; /* 2줄 = 38*1.3*2 = 98.8px */
  overflow:hidden;
}
```

---

### 🟡 T-03 · hero 숫자 위계 혼재 (64px ~ 140px)
히어로 숫자 기준 64px+ 요건은 충족하나, 슬라이드별 크기가 일관성 없이 사용됩니다:

| 슬라이드 | 숫자 | 폰트 크기 |
|---|---|---|
| 02 | 1조원+ | 120px |
| 02 (카드 내 stat) | 18%, 4~5월, 0 | **48px** |
| 07 | 23% | 110px |
| 17 | 1.2kg | **140px** |
| 33 | 467% | 120px |
| 05 (card-value) | 3,000만원 등 | **52px** |

카드 내 숫자(48px, 52px)가 히어로 64px 기준 미달입니다. 슬라이드 02의 3-stat 카드 내 `48px`은 hero_stat으로 분류되므로 64px 이상으로 상향이 필요합니다.

```css
/* 수정: 슬라이드 02 stat 카드 내 숫자 */
/* <div style="font-size:48px;font-weight:900;color:#fff;">18%</div> */
/* → font-size:64px */

/* 슬라이드 05 card-value 오버라이드 */
/* <div class="card-value" style="font-size:52px;">3,000만원</div> */
/* → font-size:64px */
```

---

### 🟡 T-04 · 본문 서브 텍스트 13~17px 다수 존재
기준: 본문 최소 20px. 아래 CSS 클래스 및 인라인 스타일이 기준 미달입니다:

| 요소 | 크기 | 위치 |
|---|---|---|
| `.card .card-sub` | 16px | 전역 CSS |
| `.card .card-desc` | 16px | 전역 CSS |
| `.kpi-card .kpi-sub` | 14px | 전역 CSS |
| `.kpi-card .kpi-label` | 13px | 전역 CSS |
| `.card .card-label` | 13px | 전역 CSS |
| `.feature-item .fi-desc` | 15px | 전역 CSS |
| `카드 내 label 텍스트` | 13~14px | 다수 인라인 |

슬라이드 프레젠테이션이 1920px 전체 화면 또는 프로젝터 출력 용도임을 고려할 때, 13~16px은 가독성이 매우 취약합니다.

```css
/* 권장 수정: 전역 CSS 상향 */
.card .card-sub { font-size:18px; } /* 16 → 18 */
.card .card-desc { font-size:18px; line-height:1.6; } /* 16 → 18 */
.card .card-label { font-size:15px; } /* 13 → 15 */
.kpi-card .kpi-label { font-size:15px; } /* 13 → 15 */
.kpi-card .kpi-sub { font-size:16px; } /* 14 → 16 */
.feature-item .fi-desc { font-size:17px; line-height:1.5; } /* 15 → 17 */
```

---

### 🟡 T-05 · quote-text 인라인 오버라이드 폰트 기준 미달
CSS 정의: `.quote-text { font-size:28px; }` — 기준 충족

그러나 슬라이드 03에서 quote-text를 `font-size:24px`로 인라인 오버라이드하고 있습니다 (L.348, 354).

```css
/* 수정: 인라인 오버라이드 제거 */
/* <div class="quote-text" style="font-size:24px;"> → <div class="quote-text"> */
/* CSS 클래스의 28px 적용 */
```

---

### 🟡 T-06 · 슬라이드 07 히어로 서브 텍스트 18px
슬라이드 07에서 `"전 연령 평균 12% 대비 약 2배"` 텍스트가 `font-size:18px`입니다. 히어로 숫자(110px) 바로 아래 보조 텍스트이므로 최소 20px 기준 미달입니다.

```css
/* 수정 */
/* <div style="font-size:18px;color:var(--muted);margin-top:8px;"> */
/* → font-size:20px */
```

---

### 🟢 T-07 · part-tag line-height 미설정
`.slide-header .part-tag { font-size:14px; font-weight:800; ... }`에 `line-height`가 명시되지 않았습니다. 브라우저 기본값 약 1.2가 적용되어, 기준(1.5+) 미달입니다. 단, `part-tag`는 단일 단어 레이블이므로 시각적 문제는 없습니다.

```css
/* 수정: 명시적 line-height 추가 */
.slide-header .part-tag {
  font-size:14px; font-weight:800; letter-spacing:3px;
  text-transform:uppercase; color:var(--main);
  margin-bottom:8px; line-height:1.5; /* 추가 */
}
```

---

### 🟢 T-08 · 슬라이드 01 커버 하단 메타 텍스트 15px
슬라이드 01 커버의 하단 메타 정보 `"2026.04 ~ 06 | 총 예산 3,000만원 | 목표 매출 2.75억원"`이 `font-size:15px`으로 설정되어 있습니다. 커버에서의 메타 정보는 부차적이므로 허용 가능하나, 기준(20px)에는 미달합니다.

```css
/* 수정 */
/* <span style="font-size:15px;color:rgba(255,255,255,0.35);">... */
/* → font-size:18px */
```

---

## 우선순위 수정 목록

| 우선순위 | 이슈 ID | 위치 | 내용 |
|---|---|---|---|
| 1 | 🔴 L-01 | 전체 | 슬라이드 번호 표시 오류 (39/38, 40/38) + ID 누락(slide-31) |
| 2 | 🔴 T-01 | 슬라이드 29, 23, 39 | 11px/12px 본문 텍스트 — 프레젠테이션 출력 시 판독 불가 |
| 3 | 🔴 T-02 | 슬라이드 02, 05 | hero 숫자/card-value 48px/52px — 64px 기준 미달 |
| 4 | 🟡 T-04 | 전역 CSS | card-sub, card-desc, kpi 레이블 16px 이하 |
| 5 | 🟡 L-02/L-03 | 슬라이드 13~18, 19~30 | 연속 동일 테마 초과 |
| 6 | 🟡 S-01 | 전역 인라인 | border-radius 8/10/14px 파편화 |
| 7 | 🟡 S-02 | 슬라이드 39 등 | flow-arrow 크기 불일치 |
| 8 | 🟡 T-03 | 슬라이드 03 | quote-text 24px 인라인 오버라이드 |

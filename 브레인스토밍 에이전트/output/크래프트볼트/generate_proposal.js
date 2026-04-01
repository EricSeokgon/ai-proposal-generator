'use strict';
/**
 * 크래프트볼트 2026 봄 정원 캠페인 — 제안서 PPTX 생성
 * PptxGenJS 4.x
 */

const PptxGenJS = require('pptxgenjs');
const path = require('path');

// ─── 디자인 시스템 ─────────────────────────────────────────────
const C = {
  orange:    'EF7B00',
  black:     '1A1A1A',
  white:     'FFFFFF',
  gray:      'F0F0F0',
  grayMid:   'AAAAAA',
  grayDark:  '555555',
  blue:      '3B82F6',
  green:     '22C55E',
  purple:    'A855F7',
  darkCard:  '2A2A2A',
  darkCard2: '333333',
};

const CHART_DIR = path.resolve(__dirname, 'charts');
const OUT_FILE  = path.resolve(__dirname, 'proposal.pptx');
const TOTAL     = 38;
let slideIndex  = 0;

const pres = new PptxGenJS();
pres.layout = 'LAYOUT_16x9';
pres.author = '안티그래비티';
pres.subject = '크래프트볼트 2026 봄 정원 캠페인 제안서';

// ─── 유틸 헬퍼 ────────────────────────────────────────────────
function makeShadow() {
  return { type: 'outer', color: '000000', opacity: 0.18, blur: 6, offset: 3, angle: 45 };
}

function slideNum(slide) {
  slideIndex++;
  slide.addText(`${slideIndex} / ${TOTAL}`, {
    x: 9.2, y: 5.35, w: 0.7, h: 0.2,
    fontSize: 8, color: C.grayMid, align: 'right',
  });
}

// 상단 액션 타이틀
function actionTitle(slide, text, isDark) {
  const color = isDark ? C.white : C.black;
  slide.addText(text, {
    x: 0.6, y: 0.22, w: 8.8, h: 0.7,
    fontSize: 22, bold: true, color,
    fontFace: 'Apple SD Gothic Neo',
    wrap: true,
  });
}

// 얇은 구분선
function divLine(slide, y, isDark) {
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.6, y, w: 8.8, h: 0.025,
    fill: { color: isDark ? '3A3A3A' : 'E0E0E0' },
    line: { color: isDark ? '3A3A3A' : 'E0E0E0', width: 0 },
  });
}

// 파트 레이블 배지 (상단 오른쪽)
function partBadge(slide, text) {
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 8.7, y: 0.18, w: 1.2, h: 0.3,
    fill: { color: C.orange },
    line: { color: C.orange, width: 0 },
  });
  slide.addText(text, {
    x: 8.7, y: 0.18, w: 1.2, h: 0.3,
    fontSize: 9, color: C.white, bold: true, align: 'center',
  });
}

// 카드 박스
function addCard(slide, x, y, w, h, bgColor, text, textColor, fontSize, opts = {}) {
  slide.addShape(pres.shapes.RECTANGLE, {
    x, y, w, h,
    fill: { color: bgColor },
    line: { color: opts.borderColor || bgColor, width: opts.borderWidth || 0 },
    shadow: opts.shadow ? makeShadow() : undefined,
  });
  if (text) {
    slide.addText(text, {
      x: x + 0.15, y, w: w - 0.3, h,
      fontSize, color: textColor, bold: opts.bold || false,
      align: opts.align || 'left',
      valign: opts.valign || 'middle',
      wrap: true,
    });
  }
}

// ─── COVER 패턴 ───────────────────────────────────────────────
function makeCover(title, sub, period, isClosing) {
  const slide = pres.addSlide();
  // 배경 전체 검정
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 5.625,
    fill: { color: C.black },
    line: { color: C.black, width: 0 },
  });
  // 오렌지 왼쪽 accent 수직 바
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 0.18, h: 5.625,
    fill: { color: C.orange },
    line: { color: C.orange, width: 0 },
  });
  // 오렌지 상단 수평 바
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 0.06,
    fill: { color: C.orange },
    line: { color: C.orange, width: 0 },
  });
  // 큰 제목
  slide.addText(title, {
    x: 0.6, y: 1.5, w: 9.0, h: 1.6,
    fontSize: isClosing ? 30 : 34, bold: true, color: C.white,
    fontFace: 'Apple SD Gothic Neo',
    align: 'center', valign: 'middle', wrap: true,
  });
  // 오렌지 서브라인
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 3.5, y: 3.3, w: 3, h: 0.05,
    fill: { color: C.orange },
    line: { color: C.orange, width: 0 },
  });
  // 서브텍스트
  slide.addText(sub, {
    x: 0.6, y: 3.45, w: 9.0, h: 0.6,
    fontSize: 15, color: C.grayMid,
    align: 'center', wrap: true,
  });
  // 하단 우측 기간/발표사
  slide.addText(period, {
    x: 6.5, y: 4.8, w: 3.3, h: 0.6,
    fontSize: 11, color: C.grayMid, align: 'right',
  });
  slideNum(slide);
}

// ─── HERO STAT 패턴 ───────────────────────────────────────────
function makeHeroStat(titleText, mainVal, mainSub, stats, isDark, partLabel) {
  const slide = pres.addSlide();
  const bg = isDark ? C.black : C.white;
  const fg = isDark ? C.white : C.black;
  slide.background = { color: bg };

  if (partLabel) partBadge(slide, partLabel);
  actionTitle(slide, titleText, isDark);
  divLine(slide, 0.98, isDark);

  // 중앙 히어로 숫자
  slide.addText(mainVal, {
    x: 0.6, y: 1.1, w: 8.8, h: 1.4,
    fontSize: 72, bold: true, color: C.orange,
    align: 'center', fontFace: 'Apple SD Gothic Neo',
  });
  slide.addText(mainSub, {
    x: 0.6, y: 2.5, w: 8.8, h: 0.5,
    fontSize: 16, color: isDark ? C.grayMid : C.grayDark,
    align: 'center',
  });

  // 하단 스탯 카드들
  const cardW = stats.length > 0 ? (8.8 / stats.length) - 0.15 : 2.5;
  stats.forEach((s, i) => {
    const cx = 0.6 + i * (cardW + 0.15);
    const cardBg = isDark ? C.darkCard : C.gray;
    addCard(slide, cx, 3.15, cardW, 1.9, cardBg, '', '', 0, { shadow: true });
    slide.addText(s.value, {
      x: cx, y: 3.2, w: cardW, h: 0.85,
      fontSize: 28, bold: true, color: s.color || C.orange,
      align: 'center', fontFace: 'Apple SD Gothic Neo',
    });
    slide.addText(s.label, {
      x: cx + 0.1, y: 4.1, w: cardW - 0.2, h: 0.8,
      fontSize: 11, color: isDark ? C.grayMid : C.grayDark,
      align: 'center', wrap: true,
    });
  });
  slideNum(slide);
}

// ─── QUOTE HIGHLIGHT 패턴 ─────────────────────────────────────
function makeQuoteHighlight(titleText, quote, quoteSource, point, isDark, partLabel) {
  const slide = pres.addSlide();
  const bg = isDark ? C.black : C.white;
  const fg = isDark ? C.white : C.black;
  slide.background = { color: bg };

  if (partLabel) partBadge(slide, partLabel);
  actionTitle(slide, titleText, isDark);
  divLine(slide, 0.98, isDark);

  // 큰따옴표 장식
  slide.addText('\u201C', {
    x: 0.4, y: 1.0, w: 1.2, h: 1.2,
    fontSize: 96, bold: true, color: C.orange,
    fontFace: 'Georgia', align: 'left',
  });

  // 인용문 박스
  const quoteBg = isDark ? C.darkCard : 'F5F5F5';
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.6, y: 1.3, w: 8.8, h: 2.0,
    fill: { color: quoteBg },
    line: { color: C.orange, width: 3 },
  });
  slide.addText(quote, {
    x: 0.9, y: 1.35, w: 8.2, h: 1.9,
    fontSize: 16, color: fg, italic: true,
    valign: 'middle', wrap: true,
    fontFace: 'Apple SD Gothic Neo',
  });

  // 출처
  slide.addText(quoteSource, {
    x: 0.6, y: 3.38, w: 8.8, h: 0.35,
    fontSize: 11, color: C.grayMid, italic: true,
  });

  // Point 박스
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.6, y: 3.85, w: 8.8, h: 1.45,
    fill: { color: C.orange },
    line: { color: C.orange, width: 0 },
  });
  slide.addText(point, {
    x: 0.8, y: 3.9, w: 8.4, h: 1.35,
    fontSize: 14, color: C.white, bold: true,
    valign: 'middle', wrap: true,
  });
  slideNum(slide);
}

// ─── COMPARISON (2열) 패턴 ────────────────────────────────────
function makeComparison(titleText, leftTitle, leftItems, rightTitle, rightItems, isDark, chartPath, partLabel) {
  const slide = pres.addSlide();
  const bg = isDark ? C.black : C.white;
  slide.background = { color: bg };

  if (partLabel) partBadge(slide, partLabel);
  actionTitle(slide, titleText, isDark);
  divLine(slide, 0.98, isDark);

  const colW = 4.1;
  const colH = chartPath ? 2.2 : 4.1;
  const colY = 1.1;

  // 왼쪽 열
  const leftBg = isDark ? C.darkCard : C.gray;
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.6, y: colY, w: colW, h: colH,
    fill: { color: leftBg },
    line: { color: isDark ? '3A3A3A' : 'D0D0D0', width: 1 },
  });
  slide.addText(leftTitle, {
    x: 0.6, y: colY + 0.1, w: colW, h: 0.45,
    fontSize: 14, bold: true, color: C.orange, align: 'center',
  });
  leftItems.forEach((item, i) => {
    slide.addText(`• ${item}`, {
      x: 0.75, y: colY + 0.65 + i * 0.42, w: colW - 0.3, h: 0.4,
      fontSize: 12, color: isDark ? C.white : C.black, wrap: true,
    });
  });

  // 가운데 VS 배지
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 4.78, y: colY + colH / 2 - 0.3, w: 0.44, h: 0.6,
    fill: { color: C.orange },
    line: { color: C.orange, width: 0 },
  });
  slide.addText('VS', {
    x: 4.78, y: colY + colH / 2 - 0.3, w: 0.44, h: 0.6,
    fontSize: 13, bold: true, color: C.white, align: 'center', valign: 'middle',
  });

  // 오른쪽 열
  const rightBg = isDark ? '2D2D2D' : 'FFFAF5';
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 5.3, y: colY, w: colW, h: colH,
    fill: { color: rightBg },
    line: { color: C.orange, width: 2 },
  });
  slide.addText(rightTitle, {
    x: 5.3, y: colY + 0.1, w: colW, h: 0.45,
    fontSize: 14, bold: true, color: C.orange, align: 'center',
  });
  rightItems.forEach((item, i) => {
    slide.addText(`• ${item}`, {
      x: 5.45, y: colY + 0.65 + i * 0.42, w: colW - 0.3, h: 0.4,
      fontSize: 12, color: isDark ? C.white : C.black, wrap: true,
    });
  });

  if (chartPath) {
    slide.addImage({ path: chartPath, x: 0.6, y: 3.42, w: 8.8, h: 2.0 });
  }
  slideNum(slide);
}

// ─── CARD GRID 패턴 ───────────────────────────────────────────
function makeCardGrid(titleText, cards, isDark, partLabel) {
  // cards: [{label, value, sub, accent}] 최대 4개
  const slide = pres.addSlide();
  const bg = isDark ? C.black : C.white;
  slide.background = { color: bg };

  if (partLabel) partBadge(slide, partLabel);
  actionTitle(slide, titleText, isDark);
  divLine(slide, 0.98, isDark);

  const is2col = cards.length <= 2;
  const cols   = is2col ? 2 : 2;
  const rows   = is2col ? 1 : 2;
  const cardW  = 4.15;
  const cardH  = is2col ? 3.5 : 1.8;
  const gapX   = 0.15;
  const gapY   = 0.15;
  const startX = 0.6;
  const startY = 1.1;

  cards.forEach((card, i) => {
    const col = i % cols;
    const row = Math.floor(i / cols);
    const cx  = startX + col * (cardW + gapX);
    const cy  = startY + row * (cardH + gapY);
    const cardBg = isDark ? C.darkCard : C.gray;
    const borderColor = card.accent ? C.orange : (isDark ? '3A3A3A' : 'D0D0D0');

    slide.addShape(pres.shapes.RECTANGLE, {
      x: cx, y: cy, w: cardW, h: cardH,
      fill: { color: cardBg },
      line: { color: borderColor, width: card.accent ? 3 : 1 },
      shadow: makeShadow(),
    });
    // 상단 컬러 바
    slide.addShape(pres.shapes.RECTANGLE, {
      x: cx, y: cy, w: cardW, h: 0.07,
      fill: { color: card.accent ? C.orange : (isDark ? '3A3A3A' : 'CCCCCC') },
      line: { color: card.accent ? C.orange : (isDark ? '3A3A3A' : 'CCCCCC'), width: 0 },
    });
    slide.addText(card.label, {
      x: cx + 0.15, y: cy + 0.12, w: cardW - 0.3, h: 0.4,
      fontSize: 11, color: C.grayMid, bold: false,
    });
    slide.addText(card.value, {
      x: cx + 0.1, y: cy + 0.5, w: cardW - 0.2, h: is2col ? 1.4 : 0.75,
      fontSize: is2col ? 36 : 22, bold: true,
      color: card.accent ? C.orange : (isDark ? C.white : C.black),
      align: 'center', valign: 'middle', fontFace: 'Apple SD Gothic Neo',
    });
    if (card.sub) {
      slide.addText(card.sub, {
        x: cx + 0.1, y: cy + cardH - 0.65, w: cardW - 0.2, h: 0.55,
        fontSize: 11, color: isDark ? C.grayMid : C.grayDark,
        align: 'center', wrap: true,
      });
    }
  });
  slideNum(slide);
}

// ─── TIMELINE 패턴 ────────────────────────────────────────────
function makeTimeline(titleText, steps, isDark, chartPath, partLabel) {
  // steps: [{label, action}]
  const slide = pres.addSlide();
  const bg = isDark ? C.black : C.white;
  slide.background = { color: bg };

  if (partLabel) partBadge(slide, partLabel);
  actionTitle(slide, titleText, isDark);
  divLine(slide, 0.98, isDark);

  if (chartPath) {
    slide.addImage({ path: chartPath, x: 0.6, y: 1.1, w: 8.8, h: 4.3 });
    slideNum(slide);
    return;
  }

  const stW = steps.length > 0 ? (8.8 / steps.length) - 0.1 : 2;
  const lineY = 2.1;

  // 수평 타임라인 선
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.6, y: lineY, w: 8.8, h: 0.05,
    fill: { color: C.orange },
    line: { color: C.orange, width: 0 },
  });

  steps.forEach((step, i) => {
    const cx = 0.6 + i * (stW + 0.1) + stW / 2;
    // 원형 마커
    slide.addShape(pres.shapes.RECTANGLE, {
      x: cx - 0.18, y: lineY - 0.18, w: 0.36, h: 0.36,
      fill: { color: C.orange },
      line: { color: C.orange, width: 0 },
    });
    // 레이블 (번갈아 위아래)
    const isUp = i % 2 === 0;
    slide.addText(step.label, {
      x: 0.6 + i * (stW + 0.1), y: isUp ? 1.25 : lineY + 0.3, w: stW, h: 0.4,
      fontSize: 11, bold: true, color: C.orange, align: 'center',
    });
    const cardBg = isDark ? C.darkCard : C.gray;
    slide.addShape(pres.shapes.RECTANGLE, {
      x: 0.6 + i * (stW + 0.1), y: isUp ? lineY + 0.3 : 1.2, w: stW, h: 1.5,
      fill: { color: cardBg },
      line: { color: isDark ? '3A3A3A' : 'D0D0D0', width: 1 },
    });
    slide.addText(step.action, {
      x: 0.6 + i * (stW + 0.1) + 0.1, y: isUp ? lineY + 0.35 : 1.25, w: stW - 0.2, h: 1.4,
      fontSize: 10, color: isDark ? C.white : C.black, wrap: true, valign: 'middle',
    });
  });
  slideNum(slide);
}

// ─── PROCESS FLOW 패턴 ────────────────────────────────────────
function makeProcessFlow(titleText, steps, isDark, partLabel) {
  // steps: [{num, title, body}]
  const slide = pres.addSlide();
  const bg = isDark ? C.black : C.white;
  slide.background = { color: bg };

  if (partLabel) partBadge(slide, partLabel);
  actionTitle(slide, titleText, isDark);
  divLine(slide, 0.98, isDark);

  const stepW = steps.length > 0 ? (8.8 / steps.length) - 0.12 : 2.5;
  const stepY = 1.1;
  const stepH = 4.1;

  steps.forEach((step, i) => {
    const sx = 0.6 + i * (stepW + 0.12);
    const cardBg = isDark ? C.darkCard : C.gray;
    slide.addShape(pres.shapes.RECTANGLE, {
      x: sx, y: stepY, w: stepW, h: stepH,
      fill: { color: cardBg },
      line: { color: isDark ? '3A3A3A' : 'D0D0D0', width: 1 },
      shadow: makeShadow(),
    });
    // 번호 배지
    slide.addShape(pres.shapes.RECTANGLE, {
      x: sx, y: stepY, w: stepW, h: 0.55,
      fill: { color: C.orange },
      line: { color: C.orange, width: 0 },
    });
    slide.addText(step.num, {
      x: sx, y: stepY, w: stepW, h: 0.55,
      fontSize: 18, bold: true, color: C.white, align: 'center', valign: 'middle',
    });
    slide.addText(step.title, {
      x: sx + 0.1, y: stepY + 0.6, w: stepW - 0.2, h: 0.65,
      fontSize: 13, bold: true,
      color: isDark ? C.white : C.black, align: 'center', wrap: true,
    });
    slide.addText(step.body, {
      x: sx + 0.1, y: stepY + 1.35, w: stepW - 0.2, h: 2.7,
      fontSize: 11, color: isDark ? C.grayMid : C.grayDark,
      wrap: true, valign: 'top',
    });
    // 화살표 (마지막 제외)
    if (i < steps.length - 1) {
      slide.addText('>', {
        x: sx + stepW, y: stepY + stepH / 2 - 0.25, w: 0.12, h: 0.5,
        fontSize: 16, bold: true, color: C.orange, align: 'center',
      });
    }
  });
  slideNum(slide);
}

// ─── PYRAMID 패턴 ─────────────────────────────────────────────
function makePyramid(titleText, levels, isDark, partLabel) {
  // levels: [{label, sub, color}] 위→아래
  const slide = pres.addSlide();
  const bg = isDark ? C.black : C.white;
  slide.background = { color: bg };

  if (partLabel) partBadge(slide, partLabel);
  actionTitle(slide, titleText, isDark);
  divLine(slide, 0.98, isDark);

  const n = levels.length;
  const totalH = 4.0;
  const rowH = totalH / n;
  const centerX = 5.0;
  const startY = 1.1;
  const maxW = 8.8;

  levels.forEach((lv, i) => {
    const frac = (i + 1) / n;
    const w = maxW * frac;
    const x = centerX - w / 2;
    const y = startY + i * rowH;
    const lvColor = lv.color || (i === 0 ? C.orange : (isDark ? C.darkCard : C.gray));

    slide.addShape(pres.shapes.RECTANGLE, {
      x, y, w, h: rowH - 0.06,
      fill: { color: lvColor },
      line: { color: isDark ? '3A3A3A' : 'D0D0D0', width: 0 },
    });
    slide.addText(lv.label, {
      x: x + 0.1, y, w: w * 0.5, h: rowH - 0.06,
      fontSize: 13, bold: true,
      color: i === 0 ? C.white : (isDark ? C.white : C.black),
      valign: 'middle', wrap: true,
    });
    if (lv.sub) {
      slide.addText(lv.sub, {
        x: x + w * 0.52, y, w: w * 0.46, h: rowH - 0.06,
        fontSize: 11,
        color: i === 0 ? 'FFDDAA' : (isDark ? C.grayMid : C.grayDark),
        valign: 'middle', wrap: true, align: 'right',
      });
    }
  });
  slideNum(slide);
}

// ─── FUNNEL 패턴 ──────────────────────────────────────────────
function makeFunnel(titleText, stages, isDark, chartPath, partLabel) {
  // stages: [{label, value, highlight}]
  const slide = pres.addSlide();
  const bg = isDark ? C.black : C.white;
  slide.background = { color: bg };

  if (partLabel) partBadge(slide, partLabel);
  actionTitle(slide, titleText, isDark);
  divLine(slide, 0.98, isDark);

  if (chartPath) {
    slide.addImage({ path: chartPath, x: 0.6, y: 1.1, w: 8.8, h: 4.3 });
    slideNum(slide);
    return;
  }

  const totalH = 4.0;
  const rowH   = totalH / stages.length;
  const centerX = 5.0;
  const startY = 1.1;
  const maxW = 8.0;

  stages.forEach((st, i) => {
    const frac = 1 - i * (0.6 / stages.length);
    const w = maxW * frac;
    const x = centerX - w / 2;
    const y = startY + i * rowH;
    const stageBg = st.highlight ? C.orange : (isDark ? C.darkCard : C.gray);
    const textColor = st.highlight ? C.white : (isDark ? C.white : C.black);

    slide.addShape(pres.shapes.RECTANGLE, {
      x, y, w, h: rowH - 0.1,
      fill: { color: stageBg },
      line: { color: isDark ? '3A3A3A' : 'D0D0D0', width: 1 },
    });
    slide.addText(st.label, {
      x: x + 0.15, y, w: w * 0.6, h: rowH - 0.1,
      fontSize: 13, bold: st.highlight, color: textColor, valign: 'middle',
    });
    slide.addText(st.value, {
      x: x + w * 0.62, y, w: w * 0.35, h: rowH - 0.1,
      fontSize: 18, bold: true, color: st.highlight ? C.white : C.orange,
      align: 'right', valign: 'middle',
    });
  });
  slideNum(slide);
}

// ─── TABLE INSIGHT 패턴 ───────────────────────────────────────
function makeTableInsight(titleText, headers, rows, isDark, partLabel) {
  // rows: [{cells:[], highlight:bool}]
  const slide = pres.addSlide();
  const bg = isDark ? C.black : C.white;
  slide.background = { color: bg };

  if (partLabel) partBadge(slide, partLabel);
  actionTitle(slide, titleText, isDark);
  divLine(slide, 0.98, isDark);

  const tableY = 1.1;
  const tableH = 4.2;
  const colW = 8.8 / headers.length;
  const rowH = tableH / (rows.length + 1);

  // 헤더 행
  headers.forEach((h, ci) => {
    slide.addShape(pres.shapes.RECTANGLE, {
      x: 0.6 + ci * colW, y: tableY, w: colW - 0.02, h: rowH,
      fill: { color: C.orange },
      line: { color: C.orange, width: 0 },
    });
    slide.addText(h, {
      x: 0.6 + ci * colW + 0.08, y: tableY, w: colW - 0.18, h: rowH,
      fontSize: 11, bold: true, color: C.white, valign: 'middle', wrap: true,
    });
  });

  // 데이터 행
  rows.forEach((row, ri) => {
    const ry = tableY + (ri + 1) * rowH;
    const rowBg = row.highlight ? (isDark ? '3A2800' : 'FFF3E0')
                                : (ri % 2 === 0 ? (isDark ? C.darkCard : C.gray) : (isDark ? '252525' : C.white));
    row.cells.forEach((cell, ci) => {
      slide.addShape(pres.shapes.RECTANGLE, {
        x: 0.6 + ci * colW, y: ry, w: colW - 0.02, h: rowH,
        fill: { color: rowBg },
        line: { color: isDark ? '3A3A3A' : 'E0E0E0', width: 1 },
      });
      slide.addText(cell, {
        x: 0.6 + ci * colW + 0.08, y: ry, w: colW - 0.18, h: rowH,
        fontSize: 11, color: row.highlight ? C.orange : (isDark ? C.white : C.black),
        bold: row.highlight && ci === 0,
        valign: 'middle', wrap: true,
      });
    });
  });
  slideNum(slide);
}

// ─── KPI DASHBOARD 패턴 ───────────────────────────────────────
function makeKpiDashboard(titleText, months, kpis, chartPath, isDark) {
  // months: ['4월','5월','6월']
  // kpis: [{label, values:[v1,v2,v3], highlight:bool}]
  const slide = pres.addSlide();
  const bg = isDark ? C.black : C.white;
  slide.background = { color: bg };

  partBadge(slide, 'PROOF');
  actionTitle(slide, titleText, isDark);
  divLine(slide, 0.98, isDark);

  if (chartPath) {
    slide.addImage({ path: chartPath, x: 0.6, y: 1.1, w: 8.8, h: 4.3 });
    slideNum(slide);
    return;
  }

  const colW = 8.8 / (months.length + 1);
  const rowH  = 4.1 / (kpis.length + 1);
  const tY    = 1.1;

  // 월 헤더
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.6, y: tY, w: colW - 0.05, h: rowH,
    fill: { color: isDark ? C.darkCard : C.gray },
    line: { color: isDark ? '3A3A3A' : 'D0D0D0', width: 0 },
  });
  months.forEach((m, mi) => {
    slide.addShape(pres.shapes.RECTANGLE, {
      x: 0.6 + (mi + 1) * colW, y: tY, w: colW - 0.05, h: rowH,
      fill: { color: C.orange },
      line: { color: C.orange, width: 0 },
    });
    slide.addText(m, {
      x: 0.6 + (mi + 1) * colW, y: tY, w: colW - 0.05, h: rowH,
      fontSize: 14, bold: true, color: C.white, align: 'center', valign: 'middle',
    });
  });

  kpis.forEach((kpi, ki) => {
    const ry = tY + (ki + 1) * rowH;
    // 레이블 셀
    const lbg = kpi.highlight ? (isDark ? '3A2800' : 'FFF3E0') : (isDark ? C.darkCard : C.gray);
    slide.addShape(pres.shapes.RECTANGLE, {
      x: 0.6, y: ry, w: colW - 0.05, h: rowH,
      fill: { color: lbg },
      line: { color: isDark ? '3A3A3A' : 'E0E0E0', width: 1 },
    });
    slide.addText(kpi.label, {
      x: 0.65, y: ry, w: colW - 0.15, h: rowH,
      fontSize: 11, bold: kpi.highlight,
      color: kpi.highlight ? C.orange : (isDark ? C.white : C.black),
      valign: 'middle', wrap: true,
    });
    // 값 셀
    kpi.values.forEach((val, vi) => {
      const vbg = kpi.highlight ? (isDark ? '3A2800' : 'FFF3E0') : (ki % 2 === 0 ? (isDark ? '252525' : C.white) : (isDark ? C.darkCard : C.gray));
      slide.addShape(pres.shapes.RECTANGLE, {
        x: 0.6 + (vi + 1) * colW, y: ry, w: colW - 0.05, h: rowH,
        fill: { color: vbg },
        line: { color: isDark ? '3A3A3A' : 'E0E0E0', width: 1 },
      });
      slide.addText(val, {
        x: 0.6 + (vi + 1) * colW, y: ry, w: colW - 0.05, h: rowH,
        fontSize: 12, bold: kpi.highlight, color: kpi.highlight ? C.orange : (isDark ? C.white : C.black),
        align: 'center', valign: 'middle',
      });
    });
  });
  slideNum(slide);
}

// ─── PART DIVIDER 슬라이드 ────────────────────────────────────
function makePartDivider(partCode, partTitle, partSub) {
  const slide = pres.addSlide();
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 5.625,
    fill: { color: C.black },
    line: { color: C.black, width: 0 },
  });
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 0.06,
    fill: { color: C.orange },
    line: { color: C.orange, width: 0 },
  });
  slide.addText(partCode, {
    x: 0, y: 1.4, w: 10, h: 1.0,
    fontSize: 60, bold: true, color: C.orange,
    align: 'center', fontFace: 'Apple SD Gothic Neo',
  });
  slide.addText(partTitle, {
    x: 0, y: 2.55, w: 10, h: 0.7,
    fontSize: 28, bold: true, color: C.white,
    align: 'center',
  });
  slide.addText(partSub, {
    x: 0, y: 3.35, w: 10, h: 0.4,
    fontSize: 14, color: C.grayMid,
    align: 'center',
  });
  slideNum(slide);
}

// ════════════════════════════════════════════════════════════════
//  슬라이드 생성 시작
// ════════════════════════════════════════════════════════════════

// ── 1-01 커버 ──
makeCover(
  '크래프트볼트 2026 봄 정원 캠페인\n쿠팡 매출 증대 제안서',
  '"찾고 있던 그 공구, 이제 쿠팡에서 찾을 수 있습니다"',
  '캠페인 기간: 2026.04 ~ 2026.06\n제안사: 안티그래비티',
  false
);

// ── 1-02 hero_stat dark ──
makeHeroStat(
  '전동공구 국내 시장 1조원 돌파, 가정용 DIY 수요가 주도합니다',
  '1조원+',
  '국내 전동공구 시장 규모 (Mordor Intelligence, 2025)',
  [
    { value: '18%', label: '가정용 DIY 카테고리\n전년 대비 성장', color: C.orange },
    { value: '최고점', label: '쿠팡 원예·DIY 검색량\n봄(4~5월) 기록', color: C.blue },
    { value: '공백', label: '"디월트급+합리적가격+국내A/S"\n포지션 비어 있음', color: C.green },
  ],
  true,
  'SPARK'
);

// ── 1-03 quote_highlight dark ──
makeQuoteHighlight(
  '소비자의 딜레마 — "디월트는 비싸고, 중국산은 불안하다"',
  '"디월트 사고 싶은데 체인톱 하나에 30만원은 부담...\n중국산은 배터리 터질까 무섭고."\n\n"전동으로 바꾸고 싶은데 무거우면 못 쓸 것 같고, A/S는 되는 건지..."',
  '— 김도현(48세, 용인 단독주택) / 박순영(57세, 아산 전원주택)',
  '두 페르소나의 공통 Pain Point: 성능 불만족(가격 장벽) + 품질 불신(A/S 공백)\n이 두 가지를 동시에 해결하는 브랜드가 없습니다. 크래프트볼트가 그 빈자리입니다.',
  true,
  'SPARK'
);

// ── 1-04 comparison dark + chart ──
makeComparison(
  '프리미엄과 저가 사이, 시장 공백이 3년째 비어 있습니다',
  '현재 시장 구도',
  ['디월트·보쉬: 22~30만원', '중국산: 7~10만원', '가성비 국내 브랜드: 거의 없음', '크래프트볼트: 현재 페이지 2~3위권'],
  '크래프트볼트 기회 포지션',
  ['"디월트급 스펙" + 브러시리스 모터', '"합리적 가격" + 14만원 (디월트 대비 51% 절감)', '"국내 A/S" + 1년 무상 보증', '3가지 동시 충족 — 시장에 없는 포지션'],
  true,
  `${CHART_DIR}/chart_positioning.png`,
  'SPARK'
);

// ── 1-05 card_grid dark ──
makeCardGrid(
  '3개월, 3,000만원, 2.75억원 — 숫자로 증명하는 제안입니다',
  [
    { label: '총 투자 예산', value: '3,000만원', sub: '월 1,000만 × 3개월', accent: false },
    { label: '목표 매출 (기본)', value: '2.75억원', sub: 'ROAS 467%', accent: true },
    { label: '손익분기 매출', value: '8,750만원', sub: 'ROAS 292% 달성 시', accent: false },
    { label: '리뷰 목표 (누적)', value: '300개', sub: '4.5점 이상 유지', accent: false },
  ],
  true,
  'SPARK'
);

// ── Part 2 Divider ──
makePartDivider('PART 2', 'PROBLEM — 문제 정의', '시장·타겟·경쟁 구조 분석 7장');

// ── 2-06 timeline light ──
makeTimeline(
  '봄 시즌 정원관리 수요, 4~6월에 연간 최고점을 기록합니다',
  [
    { label: '1~3월', action: '기준선 100\n시즌 전 탐색' },
    { label: '4월', action: '검색량 지수 280\n시즌 시작' },
    { label: '5월', action: '검색량 지수 410\n연간 최고점' },
    { label: '6월', action: '검색량 지수 320\n시즌 지속' },
    { label: '7월', action: '검색량 지수 150\n시즌 종료' },
  ],
  false,
  null,
  'PROBLEM'
);

// ── 2-07 hero_stat light ──
makeHeroStat(
  '5060세대가 쿠팡의 새로운 큰손으로 부상했습니다',
  '23%',
  '5060세대 온라인 소비 증가율 (전 연령 평균 12% 대비 약 2배)',
  [
    { value: '61%', label: '50대 쿠팡 이용률', color: C.orange },
    { value: '48%', label: '60대 쿠팡 이용률', color: C.blue },
    { value: '높음', label: '5060 평균 구매 단가\n2030 대비 상회', color: C.green },
  ],
  false,
  'PROBLEM'
);

// ── 2-08 card_grid light (2열 페르소나) ──
makeCardGrid(
  '4050 남성은 유튜브로 알고, 5060 여성은 카톡으로 삽니다',
  [
    {
      label: '페르소나 A — 김도현 (48세)',
      value: '유튜브 → 쿠팡 검색 → 가격 비교 → 구매',
      sub: '핵심 기준: 성능+가격+리뷰 4.5+',
      accent: true,
    },
    {
      label: '페르소나 B — 박순영 (57세)',
      value: '카카오톡 추천 → 쿠팡 앱 → 리뷰 사진 → 구매',
      sub: '핵심 기준: 무게·편의·A/S·가족 추천',
      accent: false,
    },
  ],
  false,
  'PROBLEM'
);

// ── 2-09 comparison light ──
makeComparison(
  '검색 결과 첫 화면, 지금은 디월트와 중국산이 장악 중입니다',
  '현재 쿠팡 검색 상위 10개',
  ['프리미엄(디월트·보쉬): 4개 (22~30만원)', '중국산 저가: 5개 (7~10만원)', '가성비 국내 브랜드: 1개 미만', '크래프트볼트: 페이지 2~3위권'],
  '캠페인 후 목표 구성',
  ['"공백 포지션" 크래프트볼트 1페이지 진입', '검색광고 + 리스팅 최적화 집행', '전환율 급등 예상: CVR 2.5% → 7%+', 'W1+W2+W3 포지셔닝 전면 노출'],
  false,
  null,
  'PROBLEM'
);

// ── 2-10 funnel light + chart ──
makeFunnel(
  '리뷰 100개 미만 — CVR이 경쟁사 대비 40% 낮은 이유입니다',
  [
    { label: '리뷰 0~49개', value: 'CVR 2.5%', highlight: false },
    { label: '리뷰 50~99개', value: 'CVR 4.5%', highlight: false },
    { label: '리뷰 100~299개', value: 'CVR 7.0%', highlight: false },
    { label: '리뷰 300개 이상', value: 'CVR 10.0%', highlight: true },
  ],
  false,
  null,
  'PROBLEM'
);

// ── 2-11 pyramid light ──
makePyramid(
  '문제 구조 요약 — 3가지 Pain Point가 서로 연결되어 있습니다',
  [
    { label: '결과: 월 매출 목표 미달', sub: '', color: C.orange },
    { label: 'CVR 저조 (리뷰 부족)', sub: '목표: 리뷰 300개 조기 달성', color: '3A2800' },
    { label: '검색 노출 부족', sub: '목표: 키워드 50개 + 리스팅 최적화', color: '2A2D3A' },
    { label: '포지셔닝 불명확 → 가격 경쟁 노출', sub: '목표: W1+W2+W3 3각 포지셔닝', color: '2A3A2A' },
  ],
  false,
  'PROBLEM'
);

// ── 2-12 quote_highlight light ──
makeQuoteHighlight(
  '결론 — 지금 이 순간이 시장 공백을 선점할 마지막 기회입니다',
  '"2026년 봄 시즌이 공백 포지션을 선점할 수 있는 가장 유리한 시점입니다.\n지금 행동하지 않으면 이 기회는 사라집니다."',
  '— 전동공구 시장 공백 포지션 경쟁 진입 예상: 2026년 하반기~2027년 (업계 추정)',
  '쿠팡 리뷰 300개 상품이 상위 고착화까지 평균 6~9개월 소요.\n2026년 봄 시즌이 선점의 황금 타이밍입니다.',
  false,
  'PROBLEM'
);

// ── Part 3 Divider ──
makePartDivider('PART 3', 'APPROACH — 전략 방향', '포지셔닝·채널·Win Theme 전략 6장');

// ── 3-13 process_flow dark ──
makeProcessFlow(
  '3개월 캠페인 전략 — 검색 장악 → 번들 확장 → 리뷰 수확',
  [
    { num: '4월', title: '전략 A\n검색 장악', body: '"찾고 있던 그 공구"\n목표 ROAS 350%\nCVR 5%\n리뷰 50개\n월 매출 6,000만원' },
    { num: '5월', title: '전략 C\n번들 확장', body: '"마당이 있다면 이 세트면 끝"\n목표 ROAS 500%\nCVR 7%\n리뷰 150개\n월 매출 1억원' },
    { num: '6월', title: 'A+C 병행\n리뷰 수확', body: '"장마 전 마당정리"\n목표 ROAS 550%\nCVR 8%\n리뷰 300개\n월 매출 1.15억원' },
  ],
  true,
  'APPROACH'
);

// ── 3-14 pyramid dark ──
makePyramid(
  '포지셔닝 전략 — "디월트급 스펙 + 반값 + 국내 A/S"로 3각 독점합니다',
  [
    { label: 'W1 — 디월트급 성능', sub: '브러시리스 모터 동일 탑재\n가격 14만원 (디월트 대비 51% 절감)', color: C.orange },
    { label: 'W2 — 국내 A/S 안심', sub: '1년 무상 A/S + 배터리 수리\nKC 인증 완료', color: '3A2800' },
    { label: 'W3 — 누구나 쓸 수 있는 경량 설계', sub: '1.2kg 초경량 + 원핸드 그립\n여성·시니어 실사용 리뷰 증명', color: '2A3A2A' },
  ],
  true,
  'APPROACH'
);

// ── 3-15 comparison dark + 가격비교 chart ──
makeComparison(
  'Win Theme W1 — 브러시리스 모터, 디월트와 스펙이 같습니다',
  '크래프트볼트',
  ['가격: 14만원', '모터: 브러시리스 21V', '중량: 1.2kg', '보증: 1년 무상 A/S + 배터리 수리', '배터리: 2개 기본 포함'],
  '디월트 DCS372B',
  ['가격: 29만원', '모터: 브러시리스 20V', '중량: 1.7kg', '보증: 1년 제한 보증', '배터리: 별도 구매'],
  true,
  `${CHART_DIR}/chart_price_comparison.png`,
  'APPROACH'
);

// ── 3-16 card_grid dark ──
makeCardGrid(
  'Win Theme W2 — "고장 나면 끝"이 아닌, 국내 A/S가 있습니다',
  [
    { label: '1년 무상 A/S', value: '12개월', sub: '구매일로부터 무상 수리 보장', accent: true },
    { label: '배터리 수리 서비스', value: '유일', sub: '국내 중국산 대비 유일 서비스', accent: false },
    { label: '국내 직영 CS', value: '3채널', sub: '전화·이메일·카카오채널 대응', accent: false },
    { label: 'KC 안전 인증', value: '완료', sub: '리튬이온 배터리 폭발 위험 제로', accent: false },
  ],
  true,
  'APPROACH'
);

// ── 3-17 hero_stat dark ──
makeHeroStat(
  'Win Theme W3 — 1.2kg, 박순영 씨가 한 손으로 쓸 수 있습니다',
  '1.2kg',
  '크래프트볼트 체인톱 중량 — 디월트(1.7kg) 대비 30% 경량',
  [
    { value: '1.2kg', label: '크래프트볼트', color: C.orange },
    { value: '1.7kg', label: '디월트 DCS372B', color: C.grayMid },
    { value: '2.2kg', label: '보쉬 AKE 30', color: C.grayMid },
  ],
  true,
  'APPROACH'
);

// ── 3-18 funnel dark + 채널 도넛 chart ──
makeFunnel(
  '채널 전략 요약 — 쿠팡 100%, 4가지 레버를 동시에 작동합니다',
  [
    { label: '검색광고 — 매출 직접 기여', value: '55% / 1,650만', highlight: true },
    { label: '디스플레이 — 리타겟팅+세트 프로모션', value: '25% / 750만', highlight: false },
    { label: '리뷰 확보 — CVR 부스터', value: '10% / 300만', highlight: false },
    { label: '콘텐츠 제작 — 상세페이지·썸네일', value: '10% / 300만', highlight: false },
  ],
  true,
  `${CHART_DIR}/chart_channel_donut.png`,
  'APPROACH'
);

// ── Part 4 Divider ──
makePartDivider('PART 4', 'EXECUTION — 실행 계획', '월별·주차별 실행 로드맵 13장');

// ── 4-19 timeline light ──
makeTimeline(
  '4월 실행 계획 — "찾고 있던 그 공구"로 검색을 장악합니다',
  [
    { label: 'W1 (4/1~7)', action: '상품 리스팅 전면 리뉴얼\n키워드 50개 등록' },
    { label: 'W2 (4/8~14)', action: '검색광고 본격 운영\n골든타임 입찰+A/B 테스트' },
    { label: 'W3 (4/15~21)', action: '키워드 최적화\n리뷰 확보 활동 시작' },
    { label: 'W4 (4/22~30)', action: '디스플레이 추가\n5월 세트 기획 착수' },
  ],
  false,
  null,
  'EXECUTION'
);

// ── 4-20 table_insight light ──
makeTableInsight(
  '쿠팡 상품 리스팅 최적화 — 제목 한 줄이 CTR을 2배로 만듭니다',
  ['제품', '최적화 제목 (핵심 키워드 포함)', 'CTR 예상 개선'],
  [
    { cells: ['체인톱', '크래프트볼트 21V 충전식 체인톱 8인치 브러시리스 경량1.2kg [배터리2개+충전기] 정원관리 1년무상AS', '+90%'], highlight: false },
    { cells: ['송풍기', '크래프트볼트 21V 충전식 대포 송풍기 브러시리스 [4000mAh×2] 낙엽청소 정원관리 경량', '+75%'], highlight: false },
    { cells: ['전동가위', '크래프트볼트 18V 충전식 전동가위 30mm 가지치기 경량설계 여성OK 1년AS', '+80%'], highlight: false },
    { cells: ['3종 세트', '[봄시즌특가] 크래프트볼트 정원관리 3종세트 체인톱+송풍기+전동가위 21V배터리호환 올인원', '+120%'], highlight: true },
  ],
  false,
  'EXECUTION'
);

// ── 4-21 pyramid light ──
makePyramid(
  '검색광고 키워드 전략 — 헤드·미들·롱테일 3단 구조로 운영합니다',
  [
    { label: '헤드 키워드 30%', sub: '"충전식 체인톱" "전동 송풍기"\nCPC 400~600원 / 인지·노출 확보', color: C.orange },
    { label: '미들 키워드 30%', sub: '"정원관리 전동공구" "가정용 체인톱"\nCPC 200~400원 / 안정적 운영', color: '3A2800' },
    { label: '롱테일 키워드 40%', sub: '"충전식 체인톱 브러시리스" "경량 전동가위 여성용" "디월트 대안"\nCPC 100~200원 / CVR 최적화', color: '2A3A2A' },
  ],
  false,
  'EXECUTION'
);

// ── 4-22 table_insight light ──
makeTableInsight(
  '골든타임 입찰 전략 — 퇴근 후 18~21시, 1.5배 입찰 강화합니다',
  ['시간대', '입찰 계수', '특징', '전략'],
  [
    { cells: ['오전 6~9시', '1.0x', '출근 전 탐색', '기준 입찰 유지'], highlight: false },
    { cells: ['오전 9~18시', '0.8x', '비활성 시간대', '예산 절감 (-20%)'], highlight: false },
    { cells: ['오후 18~21시', '1.5x', '쿠팡 피크 타임', '골든타임 집중'], highlight: true },
    { cells: ['오후 21~24시', '1.2x', '야간 구매 결정', '준골든타임 유지'], highlight: false },
    { cells: ['주말 전일', '1.3x', 'DIY 관심 피크', '주말 강화 운영'], highlight: false },
  ],
  false,
  'EXECUTION'
);

// ── 4-23 process_flow light ──
makeProcessFlow(
  '상세페이지 설계 — 모바일 스크롤 9단계, 이탈 없이 구매까지 이끕니다',
  [
    { num: '①②③', title: '인지 단계', body: '히어로 배너\n"디월트급 성능, 절반 가격"\n→ 핵심 스펙 3줄(브러시리스/21V/1.2kg)\n→ 3-way 비교표' },
    { num: '④⑤⑥', title: '신뢰 단계', body: '실사용 라이프스타일 사진\n(봄 정원 3~4장)\n→ 상세 스펙 테이블\n→ 패키지 구성 Flat Lay' },
    { num: '⑦⑧⑨', title: '행동 단계', body: '1년 무상 A/S 안심 보증 섹션\n→ 실구매 리뷰 하이라이트\n→ FAQ(배터리호환·교환반품)' },
  ],
  false,
  'EXECUTION'
);

// ── 4-24 timeline light ──
makeTimeline(
  '5월 실행 계획 — "마당이 있다면, 이 세트면 끝"으로 객단가를 2배 올립니다',
  [
    { label: 'W5 (5/1~7)', action: '3종 세트 등록\n세트 전용 상세페이지+DA' },
    { label: 'W6 (5/8~14)', action: '세트 검색광고 추가\n"정원관리 세트" 키워드 확장' },
    { label: 'W7 (5/15~21)', action: '가정의 달\n"부모님 선물" 메시지 전환' },
    { label: 'W8 (5/22~31)', action: '세트 리뷰 상세페이지 업데이트\n6월 준비' },
  ],
  false,
  null,
  'EXECUTION'
);

// ── 4-25 card_grid light ──
makeCardGrid(
  '3종 세트 번들 설계 — 배터리 호환 생태계로 재구매를 만듭니다',
  [
    { label: '① 체인톱 (21V)', value: '8인치\n브러시리스', sub: '배터리 2개 기본 포함', accent: true },
    { label: '② 송풍기 (21V)', value: '대포형\n4000mAh', sub: '체인톱 배터리 공용 사용', accent: false },
    { label: '③ 전동가위 (18V)', value: '30mm\n경량 설계', sub: '여성·시니어 원핸드 사용', accent: false },
    { label: '세트 특가', value: '28만원', sub: '개별 합산 38만원 대비 26% 절감\n실질 절감 10만원 이상', accent: true },
  ],
  false,
  'EXECUTION'
);

// ── 4-26 table_insight light ──
makeTableInsight(
  '디스플레이 광고 전략 — 4가지 광고 유형으로 리타겟팅을 완성합니다',
  ['유형', '크리에이티브', '타겟팅', '시기', '예산 비중'],
  [
    { cells: ['① 브랜드 배너', '"봄 정원 시즌, 크래프트볼트로 시작"', '전동공구·원예 방문자', '4~6월 상시', '20%'], highlight: false },
    { cells: ['② 상품 DA', '체인톱 영웅샷 + "반값"', '체인톱 검색 이력자', '4월 집중', '20%'], highlight: false },
    { cells: ['③ 세트 프로모션', '"3종 세트 26% 할인"', 'DIY·40~60대', '5월 집중', '20%'], highlight: false },
    { cells: ['④ 리타겟팅', '"장바구니에 담아두셨나요?"', '조회 후 미구매자', '전 기간', '40%'], highlight: true },
  ],
  false,
  'EXECUTION'
);

// ── 4-27 timeline light ──
makeTimeline(
  '6월 실행 계획 — 리뷰 300개의 힘으로 오가닉 매출을 키웁니다',
  [
    { label: 'W9 (6/1~7)', action: '고성과 키워드 집중\n"장마 전 마당정리" 메시지 전환' },
    { label: 'W10 (6/8~14)', action: '베스트 리뷰 상세페이지 반영\n세트 재프로모션' },
    { label: 'W11 (6/15~21)', action: '5월 미구매자\n리타겟팅 강화' },
    { label: 'W12 (6/22~30)', action: '캠페인 종합 성과 분석\n7월 전략 수립' },
  ],
  false,
  null,
  'EXECUTION'
);

// ── 4-28 process_flow light ──
makeProcessFlow(
  '리뷰 확보 플랜 — 4월 50개, 5월 150개, 6월 300개를 달성합니다',
  [
    { num: '4월', title: '목표 50개', body: '체험단 20명 모집\n(소셜·커뮤니티)\n실사용 사진 리뷰 확보\n구매 확정 후 리뷰 유도 쿠폰\n예산: 100만원' },
    { num: '5월', title: '목표 +100개', body: '세트 구매자\n자동 리뷰 요청 카카오 알림\n베스트 리뷰 작성자 소정 혜택\n예산: 100만원' },
    { num: '6월', title: '목표 +150개', body: '상위 20% 상품 집중 광고\n→ 리뷰 가속 효과\n부정 리뷰 즉각 CS 대응\n예산: 100만원' },
  ],
  false,
  'EXECUTION'
);

// ── 4-29 timeline light (12주 통합) ──
makeTimeline(
  '3개월 통합 타임라인 — 모든 활동의 주차별 실행 로드맵입니다',
  [
    { label: '4월 W1~W2', action: '리스팅 리뉴얼\n키워드 등록\n검색광고 운영' },
    { label: '4월 W3~W4', action: '최적화\n리뷰 착수\nDA 추가' },
    { label: '5월 W5~W6', action: '세트 등록\nDA 집행\n검색광고 확장' },
    { label: '5월 W7~W8', action: '가정의 달\n프로모션\n리뷰 업데이트' },
    { label: '6월 W9~W10', action: '메시지 전환\n리뷰 레버리지\n세트 재촉진' },
    { label: '6월 W11~W12', action: '리타겟팅\n강화\n성과 분석' },
  ],
  false,
  null,
  'EXECUTION'
);

// ── 4-31 table_insight light ──
makeTableInsight(
  '리스크 관리 — 5가지 위험 시나리오와 즉각 대응 플랜입니다',
  ['리스크', '확률·영향', '대응 방안', '경보 기준'],
  [
    { cells: ['초기 리뷰 부족 → CVR 저조', '높음 / 높음', '체험단 20명 조기 집행, 4월 내 50개 달성', 'CVR < 3%'], highlight: false },
    { cells: ['경쟁사 가격 인하', '중간 / 높음', '"국내 A/S + 세트 가성비" 차별화 유지', '경쟁사 10% 이상 인하'], highlight: false },
    { cells: ['검색광고 CPC 급등', '중간 / 중간', '롱테일 비중 40% 유지, CPC 600원 초과 시 키워드 교체', 'CPC > 600원'], highlight: false },
    { cells: ['부정 리뷰 발생', '낮음 / 매우 높음', '즉각 CS 대응, 평점 4.0 미만 긴급 프로토콜', '평점 < 4.0'], highlight: true },
    { cells: ['봄 시즌 조기 종료', '낮음 / 중간', '"장마 전 마당정리" 메시지 조기 전환, 실내 DIY 키워드 추가', 'ROAS < 200%'], highlight: false },
  ],
  false,
  'EXECUTION'
);

// ── Part 5 Divider ──
makePartDivider('PART 5', 'PROOF — 성과 예측', 'KPI 대시보드·시나리오·ROI 분석 7장');

// ── 5-32 kpi_dashboard light + chart ──
makeKpiDashboard(
  'KPI 대시보드 — 3개월 목표 숫자 전체를 한 화면에 담았습니다',
  ['4월', '5월', '6월'],
  [
    { label: '월 매출', values: ['6,000만', '1억', '1.15억'], highlight: true },
    { label: 'ROAS', values: ['350%', '500%', '550%'], highlight: true },
    { label: 'CVR', values: ['5%', '7%', '8%'], highlight: false },
    { label: '평균 CPC', values: ['300원', '280원', '260원'], highlight: false },
    { label: '평균 객단가', values: ['15만원', '20만원', '19만원'], highlight: false },
    { label: '주문 수', values: ['400건', '550건', '600건'], highlight: false },
    { label: '리뷰 (누적)', values: ['50개', '150개', '300개'], highlight: false },
  ],
  `${CHART_DIR}/chart_kpi_dashboard.png`,
  false
);

// ── 5-33 comparison light + 시나리오 chart ──
makeComparison(
  '매출 시나리오 분석 — 보수적 1.85억, 기본 2.75억, 낙관 3.55억입니다',
  '보수적 시나리오 (ROAS 333%)',
  ['4월: 4,000만원', '5월: 6,500만원', '6월: 8,000만원', '3개월 합계: 1.85억원', 'CVR 가정: 3~4%'],
  '기본 시나리오 (ROAS 467%)',
  ['4월: 6,000만원', '5월: 1억원', '6월: 1.15억원', '3개월 합계: 2.75억원', 'CVR 가정: 5~8%'],
  false,
  `${CHART_DIR}/chart_scenario.png`,
  'PROOF'
);

// ── 5-34 hero_stat light ──
makeHeroStat(
  '손익분기 분석 — ROAS 292%, 기본 시나리오는 이를 60% 초과합니다',
  'ROAS 467%',
  '기본 시나리오 달성 시 — 손익분기 ROAS(292%) 대비 +60% 초과',
  [
    { value: '292%', label: '손익분기 ROAS\n(마진 40% 가정)', color: C.grayMid },
    { value: '333%', label: '보수적 시나리오\n손익분기 +14% 초과', color: C.blue },
    { value: '467%', label: '기본 시나리오\n손익분기 +60% 초과', color: C.orange },
  ],
  false,
  'PROOF'
);

// ── 5-35 process_flow light ──
makeProcessFlow(
  '리뷰 선순환 — 리뷰 100개가 CVR을 2배로 만드는 메커니즘입니다',
  [
    { num: '1단계', title: '리뷰 확보', body: '예산 300만원 투자\n체험단+리뷰 유도\n목표: 4월 50개\n5월 150개 / 6월 300개' },
    { num: '2단계', title: 'CVR 상승', body: '리뷰 0~49개: CVR 2.5%\n→ 100개+: CVR 7%\n→ 300개+: CVR 10%\n(4배 차이)' },
    { num: '3단계', title: '매출 증가', body: '동일 클릭 수에서\nCVR 2.5%→7% 시\n매출 +180%\n월 추가 매출 약 3,000만' },
    { num: '4단계', title: '검색 순위 상승', body: '판매량+리뷰 증가\n→ 쿠팡 알고리즘 상위\n→ 오가닉 유입 증가\n→ 선순환 완성' },
  ],
  false,
  'PROOF'
);

// ── 5-36 timeline light ──
makeTimeline(
  '검색 순위 성장 예측 — 4월 3위권 진입, 6월 1위권 목표입니다',
  [
    { label: '현재 (3월)', action: '페이지 2~3위권\n검색 노출 미미' },
    { label: '4월 캠페인 후', action: '페이지 1위권\n(5~10위권 진입)' },
    { label: '5월 세트+리뷰100개', action: '페이지 1위권 상위\n(3~5위권 진입)' },
    { label: '6월 리뷰300개', action: '페이지 1 최상위\n(1~3위권 목표)' },
  ],
  false,
  null,
  'PROOF'
);

// ── 5-37 quote_highlight light ──
makeQuoteHighlight(
  '성공 사례 — 유사 가성비 전동공구 브랜드의 쿠팡 3개월 성과입니다',
  '"국내 가성비 전동공구 브랜드 A사, 2025년 봄 캠페인:\n예산 2,500만원 → 3개월 누적 매출 2.1억원 달성 (ROAS 840%)\n리뷰 200개 달성 후 CVR 7.2% / 3개월 후 오가닉 매출 비중 45%"',
  '출처: 쿠팡 광고 성공사례 — Coupang Ads, 2025 / 크래프트볼트는 예산 20% 더 많고 W3(경량) 차별점 추가',
  '유사 조건 ROAS 840% 달성 선례 존재.\n크래프트볼트 기본 시나리오 ROAS 467%는 보수적으로 설정된 목표입니다.',
  false,
  'PROOF'
);

// ── Part 6 Divider ──
makePartDivider('PART 6', 'RETURN — 투자 효과 & 마무리', '투자 요약·실행 일정·클로징 4장');

// ── 6-38 card_grid dark (3개 카드) ──
makeCardGrid(
  '3가지 이유 — 왜 지금, 왜 크래프트볼트여야 하는가',
  [
    { label: 'W1 — 시장 공백 선점', value: '"디월트급+반값+국내A/S"\n공백 포지션 선점', sub: '2026년 봄 = 선점 마지막 최적 타이밍', accent: true },
    { label: 'W2 — 검증된 전략', value: '유사 카테고리\nROAS 840% 달성 구조', sub: '헤드·미들·롱테일 + 리뷰 선순환 + 번들 객단가', accent: false },
    { label: 'W3 — 안전한 투자', value: '보수적 ROAS 333%\n> 손익분기 292%', sub: '어떤 시나리오에서도 투자 회수 가능한 구조', accent: false },
    { label: '3개월 후 얻는 것', value: '2.75억 매출\n+ 리뷰 자산 + 검색 순위', sub: '광고 종료 후에도 지속되는 중장기 성장 기반', accent: true },
  ],
  true,
  'RETURN'
);

// ── 6-39 comparison dark + 예산 흐름 chart ──
makeComparison(
  '투자 효과 요약 — 3,000만원이 만드는 2.75억원의 구조',
  '투입 (총 3,000만원)',
  ['검색광고 1,650만원 (55%)', '디스플레이 750만원 (25%)', '리뷰 확보 300만원 (10%)', '콘텐츠 제작 300만원 (10%)'],
  '산출 (3개월 기본 시나리오)',
  ['3개월 누적 매출 2.75억원', 'ROAS 467% (손익분기 대비 +60%)', '리뷰 300개 영구 자산', '자연 검색 상위권 순위 자산'],
  true,
  `${CHART_DIR}/chart_budget_flow.png`,
  'RETURN'
);

// ── 6-40 process_flow dark ──
makeProcessFlow(
  '실행 일정 확정 — 4월 1주차 킥오프, 지금 시작할 수 있습니다',
  [
    { num: 'D+1', title: '리스팅 리뉴얼 착수', body: '제목/대표이미지/상세페이지\n전면 리뉴얼 시작\n예상: 5~7일 소요' },
    { num: 'D+7', title: '검색광고 캠페인 세팅', body: '키워드 50개 등록\n입찰 시간대 설정\n예상: 2~3일 소요' },
    { num: 'D+10', title: '체험단 20명 모집', body: '리뷰 확보 1단계 시작\n소셜·커뮤니티 모집' },
    { num: '4/1', title: '캠페인 본격 집행', body: '검색광고 + 디스플레이\n동시 집행 시작' },
    { num: '4/7', title: '1주차 성과 리뷰', body: 'KPI 확인 및 최적화\n첫 주 A/B 결과 반영' },
  ],
  true,
  'RETURN'
);

// ── 6-41 클로징 커버 ──
makeCover(
  '찾고 있던 그 공구\n크래프트볼트 2026 봄 정원 캠페인',
  '"디월트급 성능 · 절반 가격 · 국내 A/S"',
  'W1 디월트급 성능  |  W2 국내 A/S  |  W3 경량 설계\n문의: craftbolt@example.com  |  Q&A 환영합니다',
  true
);

// ─── 저장 ─────────────────────────────────────────────────────
pres.writeFile({ fileName: OUT_FILE })
  .then(() => console.log(`\nPPTX 생성 완료: ${OUT_FILE}`))
  .catch(err => { console.error('오류:', err); process.exit(1); });

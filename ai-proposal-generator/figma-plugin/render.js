#!/usr/bin/env node
// ═══════════════════════════════════════════════════════
// Puppeteer HTML → JSON 렌더러
// 실제 브라우저에서 HTML을 렌더링하고 모든 요소의 좌표/스타일을 추출
// 사용법: node render.js input.html output.json
// ═══════════════════════════════════════════════════════

const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

const args = process.argv.slice(2);
if (args.length < 1) {
  console.error('사용법: node render.js <input.html> [output.json]');
  process.exit(1);
}

const inputPath = path.resolve(args[0]);
const outputPath = args[1] ? path.resolve(args[1]) : inputPath.replace(/\.html?$/i, '.figma.json');

async function render() {
  console.log('🚀 브라우저 시작...');
  const browser = await puppeteer.launch({ headless: true });
  const page = await browser.newPage();

  // 1920px 뷰포트
  await page.setViewport({ width: 1920, height: 10000 });

  console.log('📄 HTML 로딩:', inputPath);
  await page.goto('file://' + inputPath, { waitUntil: 'networkidle0', timeout: 30000 });

  // 폰트 로딩 대기
  await page.evaluate(() => document.fonts.ready);
  await new Promise(r => setTimeout(r, 1000)); // 추가 안정화

  console.log('🔍 요소 추출 중...');

  const slides = await page.evaluate(() => {
    // 추출할 CSS 속성 목록
    const STYLE_PROPS = [
      'display', 'flexDirection', 'justifyContent', 'alignItems',
      'gap', 'flexGrow', 'flexShrink',
      'position',
      'backgroundColor', 'backgroundImage',
      'color', 'fontSize', 'fontWeight', 'fontFamily',
      'lineHeight', 'letterSpacing', 'textAlign', 'textTransform',
      'borderRadius',
      'borderTopLeftRadius', 'borderTopRightRadius', 'borderBottomLeftRadius', 'borderBottomRightRadius',
      'borderTopWidth', 'borderTopColor', 'borderTopStyle',
      'borderRightWidth', 'borderRightColor',
      'borderBottomWidth', 'borderBottomColor',
      'borderLeftWidth', 'borderLeftColor',
      'boxShadow',
      'opacity',
      'overflow',
      'paddingTop', 'paddingRight', 'paddingBottom', 'paddingLeft',
    ];

    function extractNode(el, parentRect) {
      const computed = window.getComputedStyle(el);
      const elRect = el.getBoundingClientRect();

      // 스타일 추출
      const styles = {};
      STYLE_PROPS.forEach(prop => {
        const kebab = prop.replace(/([A-Z])/g, '-$1').toLowerCase();
        const val = computed.getPropertyValue(kebab);
        if (val && val !== 'none' && val !== 'normal' && val !== '0px' && val !== 'auto' && val !== 'rgba(0, 0, 0, 0)' && val !== 'transparent') {
          styles[prop] = val;
        }
      });

      // 항상 포함할 속성
      styles.display = computed.display;
      styles.position = computed.position;
      styles.color = computed.color;
      styles.backgroundColor = computed.backgroundColor;

      // background-image (gradient)
      const bgImg = computed.backgroundImage;
      if (bgImg && bgImg !== 'none') styles.backgroundImage = bgImg;

      // 부모 기준 상대 좌표 (Figma 방식)
      const rect = {
        x: Math.round((elRect.left - parentRect.left) * 100) / 100,
        y: Math.round((elRect.top - parentRect.top) * 100) / 100,
        width: Math.round(elRect.width * 100) / 100,
        height: Math.round(elRect.height * 100) / 100,
      };

      // 자식 처리
      const children = [];
      let directText = '';

      el.childNodes.forEach(child => {
        if (child.nodeType === Node.ELEMENT_NODE) {
          const tag = child.tagName.toLowerCase();
          if (tag === 'br') {
            directText += '\n';
          } else if (tag !== 'script' && tag !== 'style' && tag !== 'link') {
            // 크기가 0인 요소 무시 (display:none 등)
            const childRect = child.getBoundingClientRect();
            if (childRect.width > 0 || childRect.height > 0) {
              children.push(extractNode(child, elRect));
            }
          }
        } else if (child.nodeType === Node.TEXT_NODE) {
          const t = child.textContent.trim();
          if (t) directText += (directText ? ' ' : '') + t;
        }
      });

      // 텍스트
      let text;
      if (children.length === 0) {
        text = directText || el.textContent?.trim() || undefined;
      } else if (directText) {
        text = directText;
      }

      return {
        tag: el.tagName.toLowerCase(),
        id: el.id || undefined,
        classes: Array.from(el.classList),
        text,
        children,
        styles,
        rect,
      };
    }

    // 슬라이드 추출
    const sections = document.querySelectorAll('section.slide');
    const result = [];

    sections.forEach((section, idx) => {
      const slideRect = section.getBoundingClientRect();
      const slideComputed = window.getComputedStyle(section);

      // 슬라이드 스타일
      const slideStyles = {};
      STYLE_PROPS.forEach(prop => {
        const kebab = prop.replace(/([A-Z])/g, '-$1').toLowerCase();
        const val = slideComputed.getPropertyValue(kebab);
        if (val && val !== 'none' && val !== 'normal') {
          slideStyles[prop] = val;
        }
      });
      slideStyles.display = slideComputed.display;
      const bgImg = slideComputed.backgroundImage;
      if (bgImg && bgImg !== 'none') slideStyles.backgroundImage = bgImg;

      // 자식 노드
      const nodes = [];
      section.childNodes.forEach(child => {
        if (child.nodeType === Node.ELEMENT_NODE) {
          const tag = child.tagName.toLowerCase();
          if (tag !== 'script' && tag !== 'style' && tag !== 'link') {
            const childRect = child.getBoundingClientRect();
            if (childRect.width > 0 || childRect.height > 0) {
              nodes.push(extractNode(child, slideRect));
            }
          }
        }
      });

      result.push({
        id: section.id || 'slide-' + idx,
        index: idx,
        nodes,
        slideStyles,
      });
    });

    return result;
  });

  await browser.close();

  // JSON 저장
  const output = JSON.stringify(slides, null, 2);
  fs.writeFileSync(outputPath, output, 'utf8');

  console.log(`✅ 완료! ${slides.length}개 슬라이드 → ${outputPath}`);
  console.log(`   파일 크기: ${(Buffer.byteLength(output) / 1024).toFixed(1)} KB`);
}

render().catch(err => {
  console.error('❌ 오류:', err.message);
  process.exit(1);
});

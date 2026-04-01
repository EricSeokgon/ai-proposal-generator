#!/usr/bin/env python3
"""CraftVolt 차트 Playwright 캡처 스크립트"""

import os
from pathlib import Path
from playwright.sync_api import sync_playwright

CHARTS_DIR = Path("/Users/stevehan/Desktop/안티그래비티 프로젝트/강의 에이전트/브레인스토밍 에이전트/output/크래프트볼트/charts")

CHARTS = [
    ("chart_1_market_size.html",     "chart_market_size.png"),
    ("chart_2_positioning.html",     "chart_positioning.png"),
    ("chart_3_price_comparison.html","chart_price_comparison.png"),
    ("chart_4_channel_donut.html",   "chart_channel_donut.png"),
    ("chart_5_monthly_revenue.html", "chart_monthly_revenue.png"),
    ("chart_6_scenario.html",        "chart_scenario.png"),
    ("chart_7_budget_flow.html",     "chart_budget_flow.png"),
    ("chart_8_kpi_dashboard.html",   "chart_kpi_dashboard.png"),
    ("chart_9_roas_line.html",       "chart_roas_line.png"),
]

def capture_charts():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        for html_file, png_file in CHARTS:
            html_path = CHARTS_DIR / html_file
            png_path  = CHARTS_DIR / png_file

            if not html_path.exists():
                print(f"  [SKIP] {html_file} 파일 없음")
                continue

            page = browser.new_page(
                viewport={"width": 1600, "height": 900},
                device_scale_factor=2
            )
            page.goto(f"file://{html_path}")

            # Chart.js / 폰트 로딩 대기
            page.wait_for_timeout(2500)

            page.screenshot(
                path=str(png_path),
                full_page=False,
                clip={"x": 0, "y": 0, "width": 1600, "height": 900}
            )
            page.close()

            size_kb = png_path.stat().st_size // 1024
            print(f"  [OK] {png_file}  ({size_kb} KB)")

        browser.close()
    print("\n완료: 모든 차트 캡처 완료")

if __name__ == "__main__":
    capture_charts()

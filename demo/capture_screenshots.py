#!/usr/bin/env python3
"""Capture 6 distinct DevPost screenshots with Playwright."""
from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEMO_DIR = PROJECT_ROOT / "demo"
SCREENSHOT_DIR = DEMO_DIR / "screenshots"
SCREENSHOT_DIR.mkdir(exist_ok=True)
STREAMLIT_PORT = 8503
STREAMLIT_URL = f"http://localhost:{STREAMLIT_PORT}"


def start_streamlit():
    print("Starting Streamlit...")
    proc = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", str(DEMO_DIR / "app.py"),
         "--server.headless", "true", "--server.port", str(STREAMLIT_PORT),
         "--browser.gatherUsageStats", "false", "--logger.level", "error"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        cwd=str(PROJECT_ROOT),
        env={**os.environ, "STREAMLIT_SERVER_HEADLESS": "true"},
    )
    for _ in range(30):
        try:
            import urllib.request
            urllib.request.urlopen(STREAMLIT_URL, timeout=1)
            break
        except Exception:
            time.sleep(1)
    else:
        proc.kill()
        raise RuntimeError("Streamlit didn't start")
    print("  Running.")
    return proc


def capture():
    from playwright.sync_api import sync_playwright

    streamlit_proc = start_streamlit()

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1440, "height": 900})

            print("\n--- Capturing Screenshots ---")

            # 1. Landing page — Simulation tab, header visible
            print("[1/6] Landing page")
            page.goto(STREAMLIT_URL, wait_until="networkidle", timeout=30000)
            time.sleep(2)
            page.screenshot(path=str(SCREENSHOT_DIR / "01_landing.png"), full_page=True)
            print(f"  -> {SCREENSHOT_DIR / '01_landing.png'}")

            # 2. Select debate scenario, show agent cards
            print("[2/6] Debate scenario with agent cards")
            try:
                page.click('[data-baseweb="select"]', timeout=5000)
                time.sleep(0.3)
                page.click('text=debate — Agents debate', timeout=5000)
            except Exception:
                pass
            time.sleep(1.5)
            page.evaluate("window.scrollTo(0, 200)")
            time.sleep(0.5)
            page.screenshot(path=str(SCREENSHOT_DIR / "02_scenario_selected.png"), full_page=True)
            print(f"  -> {SCREENSHOT_DIR / '02_scenario_selected.png'}")

            # 3. Run simulation
            print("[3/6] Running simulation...")
            page.click("button:has-text('Run Simulation')")
            try:
                page.wait_for_selector("text=Complete", timeout=120000)
            except Exception:
                time.sleep(30)
            time.sleep(1)
            page.evaluate("window.scrollTo(0, 0)")
            time.sleep(0.5)
            page.screenshot(path=str(SCREENSHOT_DIR / "03_simulation_run.png"), full_page=True)
            print(f"  -> {SCREENSHOT_DIR / '03_simulation_run.png'}")

            # 4. Scroll to agent performance stats + timeline
            print("[4/6] Agent stats + timeline")
            page.evaluate("window.scrollTo(0, 500)")
            time.sleep(0.5)
            page.screenshot(path=str(SCREENSHOT_DIR / "04_agent_performance.png"), full_page=True)
            print(f"  -> {SCREENSHOT_DIR / '04_agent_performance.png'}")

            # 5. Switch to Lark tab, show score card
            print("[5/6] Lark Gatekeeper Red Team tab")
            page.evaluate("window.scrollTo(0, 0)")
            time.sleep(0.3)
            try:
                page.click("text=🛡️ Lark Gatekeeper Red Team", timeout=5000)
                time.sleep(1)
                page.click("button:has-text('Run Red Team')", timeout=5000)
                try:
                    page.wait_for_selector("text=Security Score", timeout=60000)
                    print("  Red Team results loaded")
                except Exception:
                    time.sleep(8)
                time.sleep(1)
                page.evaluate("window.scrollTo(0, 0)")
                time.sleep(0.5)
                page.screenshot(path=str(SCREENSHOT_DIR / "05_lark_red_team.png"), full_page=True)
                print(f"  -> {SCREENSHOT_DIR / '05_lark_red_team.png'}")
            except Exception as e:
                print(f"  Lark capture failed: {e}")

            # 6. Scroll Lark results to show hardening analysis + workflows
            print("[6/6] Lark hardening analysis + workflows")
            page.evaluate("window.scrollTo(0, document.body.scrollHeight - 600)")
            time.sleep(1)
            page.screenshot(path=str(SCREENSHOT_DIR / "06_lark_analysis.png"), full_page=True)
            print(f"  -> {SCREENSHOT_DIR / '06_lark_analysis.png'}")

            browser.close()
            print("\n--- Done ---")

    finally:
        streamlit_proc.terminate()
        try:
            streamlit_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            streamlit_proc.kill()
            streamlit_proc.wait()
        print("Streamlit stopped.")


def main():
    print("=== Agent Colosseum Screenshot Capture ===\n")
    env_file = PROJECT_ROOT / ".env"
    if env_file.exists():
        from dotenv import load_dotenv
        load_dotenv(env_file)
    capture()
    print(f"\nScreenshots saved to {SCREENSHOT_DIR}/")
    for p in sorted(SCREENSHOT_DIR.glob("*.png")):
        print(f"  {p.name} ({p.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()

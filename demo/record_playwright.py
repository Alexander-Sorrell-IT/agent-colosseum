#!/usr/bin/env python3
"""Playwright-based demo recorder for Agent Colosseum Streamlit dashboard.

Captures screenshots of the full user journey:
1. Dashboard landing page
2. Scenario selection
3. Running a debate simulation
4. Interaction timeline
5. Orchestrator AI analysis
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEMO_DIR = PROJECT_ROOT / "demo"
SCREENSHOTS = DEMO_DIR / "screenshots"
SCREENSHOTS.mkdir(exist_ok=True)

STREAMLIT_PORT = 8501
STREAMLIT_URL = f"http://localhost:{STREAMLIT_PORT}"


def start_streamlit():
    """Start Streamlit in background."""
    print("Starting Streamlit server...")
    proc = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", str(DEMO_DIR / "app.py"),
         "--server.headless", "true",
         "--server.port", str(STREAMLIT_PORT),
         "--browser.gatherUsageStats", "false",
         "--logger.level", "error"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        cwd=str(PROJECT_ROOT),
    )
    # Wait for server to be ready
    for _ in range(30):
        try:
            import urllib.request
            urllib.request.urlopen(STREAMLIT_URL, timeout=1)
            break
        except Exception:
            time.sleep(1)
    else:
        raise RuntimeError("Streamlit failed to start")
    print(f"  Streamlit running at {STREAMLIT_URL}")
    return proc


def record_demo():
    """Record the full Streamlit dashboard demo using Playwright."""
    from playwright.sync_api import sync_playwright

    streamlit_proc = start_streamlit()

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={"width": 1280, "height": 800},
                device_scale_factor=1,
            )
            page = context.new_page()

            # ---- Screenshot 1: Landing page ----
            print("\n[1/6] Capturing landing page...")
            page.goto(STREAMLIT_URL, wait_until="networkidle", timeout=30000)
            time.sleep(2)
            page.screenshot(path=str(SCREENSHOTS / "01_landing.png"), full_page=True)
            print("  -> screenshots/01_landing.png")

            # ---- Screenshot 2: Sidebar with scenario selector ----
            print("[2/6] Capturing scenario selector...")
            # Click "Pre-built Scenario" radio if not default
            try:
                page.click("text=Pre-built Scenario", timeout=2000)
            except Exception:
                pass  # Already selected
            time.sleep(1)
            page.screenshot(path=str(SCREENSHOTS / "02_scenario_select.png"), full_page=True)
            print("  -> screenshots/02_scenario_select.png")

            # ---- Screenshot 3: Select debate scenario ----
            print("[3/6] Selecting debate scenario...")
            # Open the selectbox and pick "debate"
            try:
                page.click('[data-baseweb="select"]', timeout=5000)
                time.sleep(0.5)
                page.click('text=debate — Agents debate', timeout=5000)
            except Exception:
                # Fallback: click the first option
                page.select_option('[data-baseweb="select"] select', index=0)
            time.sleep(1)
            page.screenshot(path=str(SCREENSHOTS / "03_debate_selected.png"), full_page=True)
            print("  -> screenshots/03_debate_selected.png")

            # ---- Screenshot 4: Run simulation ----
            print("[4/6] Running debate simulation...")
            # Click the Run button
            page.click("button:has-text('Run Simulation')")
            # Wait for simulation to complete (progress bar at 100%)
            try:
                page.wait_for_selector("text=Complete in", timeout=120000)
                page.wait_for_selector("text=steps run", timeout=10000)
            except Exception:
                print("  Warning: timeout waiting for completion, capturing current state")
            time.sleep(2)
            page.screenshot(path=str(SCREENSHOTS / "04_simulation_results.png"), full_page=True)
            print("  -> screenshots/04_simulation_results.png")

            # ---- Screenshot 5: Interaction timeline ----
            print("[5/6] Capturing interaction timeline...")
            # Expand the first step
            try:
                page.click("text=Step 1", timeout=5000)
                time.sleep(1)
            except Exception:
                pass
            page.screenshot(path=str(SCREENSHOTS / "05_timeline.png"), full_page=True)
            print("  -> screenshots/05_timeline.png")

            # ---- Screenshot 6: Orchestrator analysis ----
            print("[6/6] Capturing AI analysis...")
            # Scroll to the analysis section
            try:
                analysis_el = page.query_selector("text=Orchestrator Analysis")
                if analysis_el:
                    analysis_el.scroll_into_view_if_needed()
                    time.sleep(1)
            except Exception:
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(1)
            page.screenshot(path=str(SCREENSHOTS / "06_analysis.png"), full_page=True)
            print("  -> screenshots/06_analysis.png")

            browser.close()
            print("\nAll screenshots captured in demo/screenshots/")

    finally:
        streamlit_proc.terminate()
        try:
            streamlit_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            streamlit_proc.kill()
            streamlit_proc.wait()
        print("Streamlit server stopped.")


def main():
    print("=== Agent Colosseum Playwright Demo Recorder ===")
    print()

    # Set CRUSOE_API_KEY from .env if available
    env_file = PROJECT_ROOT / ".env"
    if env_file.exists():
        from dotenv import load_dotenv
        load_dotenv(env_file)

    if not os.environ.get("CRUSOE_API_KEY"):
        print("Note: No CRUSOE_API_KEY found. Streamlit will run in offline demo mode.")
        print("Set CRUSOE_API_KEY in .env for live API demo recording.")
        print()

    record_demo()

    print()
    print("Next steps:")
    print("  1. Review screenshots in demo/screenshots/")
    print("  2. Use OBS or FFmpeg to record a video walkthrough")
    print("  3. Submit to DevPost with screenshots + GitHub link")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Record a demo video of the Streamlit dashboard using Playwright video capture."""
from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEMO_DIR = PROJECT_ROOT / "demo"
VIDEO_DIR = DEMO_DIR / "videos"
VIDEO_DIR.mkdir(exist_ok=True)

STREAMLIT_PORT = 8501
STREAMLIT_URL = f"http://localhost:{STREAMLIT_PORT}"


def start_streamlit():
    print("Starting Streamlit server...")
    proc = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", str(DEMO_DIR / "app.py"),
         "--server.headless", "true",
         "--server.port", str(STREAMLIT_PORT),
         "--browser.gatherUsageStats", "false",
         "--logger.level", "error"],
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
        raise RuntimeError("Streamlit failed to start")
    print(f"  Streamlit running at {STREAMLIT_URL}")
    return proc


def record_video():
    from playwright.sync_api import sync_playwright

    streamlit_proc = start_streamlit()

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={"width": 1280, "height": 800},
                record_video_dir=str(VIDEO_DIR),
                record_video_size={"width": 1280, "height": 800},
            )
            page = context.new_page()

            print("\n🎬 Recording demo video...")

            # Scene 1: Landing page (Simulation tab)
            print("[1/6] Landing page...")
            page.goto(STREAMLIT_URL, wait_until="networkidle", timeout=30000)
            time.sleep(2)

            # Scene 2: Select debate scenario and run
            print("[2/6] Selecting debate scenario...")
            try:
                page.click('[data-baseweb="select"]', timeout=5000)
                time.sleep(0.5)
                page.click('text=debate — Agents debate', timeout=5000)
            except Exception:
                pass
            time.sleep(1.5)

            print("[3/6] Running simulation...")
            page.click("button:has-text('Run Simulation')")
            try:
                page.wait_for_selector("text=Complete in", timeout=180000)
            except Exception:
                print("  (waiting for simulation to progress...)")
                time.sleep(30)
            time.sleep(1.5)

            # Scene 3: Scroll through simulation results
            print("[4/6] Showing results...")
            page.evaluate("window.scrollTo(0, 400)")
            time.sleep(1.5)
            page.evaluate("window.scrollTo(0, 800)")
            time.sleep(1.5)

            # Scene 4: Switch to Lark tab
            print("[5/6] Lark Gatekeeper Red Team...")
            page.evaluate("window.scrollTo(0, 0)")
            time.sleep(0.5)
            # Click the Lark tab
            try:
                page.click("text=🛡️ Lark Gatekeeper Red Team", timeout=5000)
                time.sleep(1)
                # Click Run Red Team button
                page.click("button:has-text('Run Red Team')", timeout=5000)
                print("  Red Team running...")
                # Wait for results
                try:
                    page.wait_for_selector("text=Security Score", timeout=60000)
                    print("  Results loaded")
                except Exception:
                    time.sleep(8)
                time.sleep(1)
                # Scroll through Lark results
                page.evaluate("window.scrollTo(0, 300)")
                time.sleep(1.5)
                page.evaluate("window.scrollTo(0, 600)")
                time.sleep(1.5)
                page.evaluate("window.scrollTo(0, document.body.scrollHeight - 400)")
                time.sleep(2)
            except Exception as e:
                print(f"  Lark scene error: {e}")
                time.sleep(2)

            # Scene 6: Final overview
            print("[6/6] Final overview...")
            page.evaluate("window.scrollTo(0, 0)")
            time.sleep(2)

            # Stop recording
            context.close()
            browser.close()

            # Find the recorded video
            videos = list(VIDEO_DIR.glob("*.webm"))
            if videos:
                video_path = videos[0]
                # Rename to something cleaner
                final_path = VIDEO_DIR / "agent_colosseum_demo.webm"
                video_path.rename(final_path)
                print(f"\n✅ Video saved: {final_path}")
                print(f"   Size: {final_path.stat().st_size:,} bytes")
                print(f"   Duration: check with ffprobe")
            else:
                print("\n⚠️  No video file found")

    finally:
        streamlit_proc.terminate()
        try:
            streamlit_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            streamlit_proc.kill()
            streamlit_proc.wait()
        print("Streamlit server stopped.")


def main():
    print("=== Agent Colosseum Demo Video Recorder ===\n")

    env_file = PROJECT_ROOT / ".env"
    if env_file.exists():
        from dotenv import load_dotenv
        load_dotenv(env_file)

    if not os.environ.get("CRUSOE_API_KEY"):
        print("Note: No CRUSOE_API_KEY found, using offline mock mode.\n")

    record_video()

    print("\nNext: Upload demo/videos/agent_colosseum_demo.webm to YouTube/Instagram")
    print("Or convert to MP4: ffmpeg -i demo/videos/agent_colosseum_demo.webm demo.mp4")


if __name__ == "__main__":
    main()

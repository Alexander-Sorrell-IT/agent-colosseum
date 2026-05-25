#!/usr/bin/env python3
"""Playwright demo recorder — generates screenshots and recording for submission video."""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEMO_DIR = PROJECT_ROOT / "demo"
SCREENSHOTS = DEMO_DIR / "screenshots"
SCREENSHOTS.mkdir(exist_ok=True)


def record_cli_demo():
    """Record CLI demo output."""
    print("Recording CLI demo...")

    # Run the demo command
    result = subprocess.run(
        [sys.executable, "-m", "colosseum.cli", "demo"],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT),
        timeout=120,
        env={**__import__("os").environ, "COLUMNS": "120"},
    )
    output = result.stdout + result.stderr

    (DEMO_DIR / "cli_demo_output.txt").write_text(output)
    print(f"  CLI demo saved: {len(output)} chars")


def record_cli_list():
    """Record scenario list."""
    result = subprocess.run(
        [sys.executable, "-m", "colosseum.cli", "list"],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT), timeout=30,
    )
    (DEMO_DIR / "scenarios.txt").write_text(result.stdout)
    print(f"  Scenario list saved")


def record_cli_run():
    """Record a single run."""
    print("Recording CLI run (mock mode)...")
    result = subprocess.run(
        [sys.executable, "-m", "colosseum.cli", "--mock", "run", "debate"],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT), timeout=120,
    )
    (DEMO_DIR / "debate_run.txt").write_text(result.stdout)
    print(f"  Debate run saved: {len(result.stdout)} chars")


def main():
    print("=== Agent Colosseum Demo Recorder ===")
    print()

    record_cli_list()
    record_cli_run()
    record_cli_demo()

    print()
    print("All recordings saved to demo/")
    print()
    print("For Streamlit recording:")
    print(f"  1. Run: ./demo/run_streamlit.sh")
    print(f"  2. Open: http://localhost:8501")
    print(f"  3. Record with OBS or your screen recorder")
    print()
    print("For Playwright browser automation:")
    print(f"  playwright codegen http://localhost:8501")


if __name__ == "__main__":
    main()

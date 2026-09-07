"""Capture a screenshot of the PayFlow Streamlit dashboard."""

import shutil
import subprocess
import sys
import time
from pathlib import Path

import requests
from playwright.sync_api import sync_playwright

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DASHBOARD_SCRIPT = PROJECT_ROOT / "src" / "dashboard" / "dashboard.py"
OUTPUT_PATH = PROJECT_ROOT / "docs" / "assets" / "dashboard.png"
PORT = 8501
URL = f"http://127.0.0.1:{PORT}"


def wait_for_streamlit(timeout: int = 60) -> None:
    """Poll Streamlit until it responds."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            response = requests.get(URL, timeout=2)
            if response.status_code == 200:
                return
        except requests.RequestException:
            time.sleep(0.5)
    raise RuntimeError("Streamlit did not start in time")


def capture_screenshot() -> None:
    """Start Streamlit and save a screenshot of the dashboard."""
    streamlit_bin = shutil.which("streamlit") or str(PROJECT_ROOT / ".venv" / "bin" / "streamlit")
    if not Path(streamlit_bin).exists():
        raise RuntimeError("streamlit executable not found")

    process = subprocess.Popen(
        [
            streamlit_bin,
            "run",
            str(DASHBOARD_SCRIPT),
            "--server.headless",
            "true",
            "--server.port",
            str(PORT),
            "--browser.gatherUsageStats",
            "false",
        ],
        cwd=PROJECT_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    try:
        wait_for_streamlit(timeout=60)
        # Give the page a moment to render initial widgets
        time.sleep(2)

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1400, "height": 900})
            page.goto(URL, wait_until="networkidle")
            # Wait for main content and charts to settle
            page.wait_for_selector("[data-testid='stMetricValue']", timeout=15000)
            page.wait_for_timeout(2000)
            page.screenshot(path=str(OUTPUT_PATH), full_page=True)
            browser.close()

        print(f"Screenshot saved to {OUTPUT_PATH}")
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()


if __name__ == "__main__":
    capture_screenshot()

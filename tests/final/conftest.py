"""
CSE312 Software Architecture - Final Test Suite Configuration
EVENTRA - Unified Event Management Platform
Root Pytest Configuration and Shared Fixtures
"""

import os
import sys
import time
import subprocess
import requests
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

BASE_URL = "http://localhost:3000"
EVIDENCE_DIR = os.path.join(os.path.dirname(__file__), "evidence")
SCREENSHOT_DIR = os.path.join(EVIDENCE_DIR, "screenshots")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)


def is_server_healthy():
    try:
        res = requests.get(f"{BASE_URL}/api/health", timeout=1.5)
        return res.status_code == 200
    except requests.exceptions.RequestException:
        return False


@pytest.fixture(scope="session", autouse=True)
def ensure_eventra_server():
    """Verifies that the Eventra backend server is online before running any tests."""
    if is_server_healthy():
        return

    # Locate eventra-web root directory
    test_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(test_dir, "..", ".."),
        os.path.join(test_dir, ".."),
        r"p:\coding.c\c programes\eventra-web"
    ]
    app_dir = None
    for cand in candidates:
        if os.path.exists(os.path.join(cand, "server", "server.js")):
            app_dir = os.path.abspath(cand)
            break

    if not app_dir:
        pytest.fail("Could not locate 'server/server.js' to auto-start Eventra backend.")

    server_script = os.path.join(app_dir, "server", "server.js")
    proc = subprocess.Popen(
        ["node", server_script],
        cwd=app_dir,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        shell=True
    )

    started = False
    for _ in range(16):
        time.sleep(0.5)
        if is_server_healthy():
            started = True
            break

    if not started:
        pytest.fail(f"Failed to auto-start Eventra server at {BASE_URL} from {server_script}.")


@pytest.fixture(scope="function")
def driver():
    """Headless Chrome WebDriver fixture for System and UI testing."""
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1366,768")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    d = webdriver.Chrome(options=options)
    d.implicitly_wait(5)
    yield d
    d.quit()

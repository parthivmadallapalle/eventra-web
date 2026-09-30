"""
Pytest Global Configuration & Auto-Server Starter
Ensures that the EVENTRA backend server (Node.js on port 3000) is running before any test executes.
"""

import os
import sys
import time
import subprocess
import requests
import pytest

BASE_URL = "http://localhost:3000"


def is_server_healthy():
    try:
        res = requests.get(f"{BASE_URL}/api/health", timeout=1.5)
        return res.status_code == 200
    except requests.exceptions.RequestException:
        return False


@pytest.fixture(scope="session", autouse=True)
def ensure_eventra_server():
    """Checks if Eventra server is up; if not, automatically launches it in the background."""
    if is_server_healthy():
        return

    # Locate eventra-web directory
    test_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(test_dir, ".."),
        os.path.join(test_dir, "..", "eventra-web"),
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
    # Launch server as background process
    proc = subprocess.Popen(
        ["node", server_script],
        cwd=app_dir,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        shell=True
    )

    # Wait for server to come online (up to 8 seconds)
    started = False
    for _ in range(16):
        time.sleep(0.5)
        if is_server_healthy():
            started = True
            break

    if not started:
        pytest.fail(f"Failed to auto-start Eventra server at {BASE_URL} from {server_script}.")

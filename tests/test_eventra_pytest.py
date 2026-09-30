"""
EVENTRA - Unified Event Management Platform
Software Architecture Automated Testing Suite: Pytest API / Architecture Layer

Test Cases:
- TC-PY-01 (Positive): Authentication & Role-Based Access Control (RBAC) Module
- TC-PY-02 (Negative): Gate Security & Ticket Verification Module
"""

import pytest
import requests
import time

BASE_URL = "http://localhost:3000"


@pytest.fixture(scope="session", autouse=True)
def ensure_server_running():
    """Ensure the Eventra backend server is reachable before running tests."""
    max_retries = 5
    for _ in range(max_retries):
        try:
            res = requests.get(f"{BASE_URL}/api/health", timeout=2)
            if res.status_code == 200:
                return
        except requests.exceptions.RequestException:
            pass
        time.sleep(1)
    pytest.fail(f"Could not connect to EVENTRA server at {BASE_URL}. Ensure 'node server/server.js' is running.")


def test_tc_py_01_organizer_authentication_success():
    """
    Test Case ID: TC-PY-01
    Objective: Verify that a registered Event Organizer can authenticate with valid credentials,
               returning HTTP 200 OK, valid user profile, and correct RBAC role assignment.
    Module Tested: Module 1 - Authentication & RBAC Engine (Application/API Layer)
    Type: Positive Test
    """
    endpoint = f"{BASE_URL}/api/auth/login"
    payload = {
        "email": "organizer@fest.org",
        "password": "pass123"
    }

    response = requests.post(endpoint, json=payload, timeout=5)

    # Status Code Assertion
    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}: {response.text}"

    # Response Structure & RBAC Assertions
    data = response.json()
    assert data.get("success") is True, "Expected success to be True in response body"
    assert "user" in data, "User object missing from response"
    
    user = data["user"]
    assert user.get("email") == "organizer@fest.org", f"Expected email organizer@fest.org, got {user.get('email')}"
    # In Eventra Architecture: 0=Admin, 1=Organizer, 2=Attendee, 3=Sponsor, 4=Security Staff
    assert user.get("role") == 1, f"Expected Organizer role ID (1), got: {user.get('role')}"
    assert user.get("name") == "Rohit Somuri", f"Expected user name 'Rohit Somuri', got: {user.get('name')}"


def test_tc_py_02_gate_checkin_tampered_token_rejection():
    """
    Test Case ID: TC-PY-02
    Objective: Verify that the gate verification engine detects and rejects an invalid/counterfeit
               ticket QR token, safeguarding event venue entry.
    Module Tested: Module 4 - Gate Check-In & Access Security Module (Application/API Layer)
    Type: Negative Test
    """
    endpoint = f"{BASE_URL}/api/checkins/verify"
    payload = {
        "token": "FRAUDULENT_QR_TOKEN_TAMPERED_99999_EXPIRED"
    }

    response = requests.post(endpoint, json=payload, timeout=5)

    # Gate API returns HTTP 200 with security status 'INVALID'
    assert response.status_code == 200, f"Unexpected HTTP status: {response.status_code}"
    
    data = response.json()
    assert data.get("status") == "INVALID", (
        f"Security check failed! Counterfeit token was not rejected as INVALID. Response: {data}"
    )
    assert "no ticket matching" in data.get("message", "").lower(), (
        f"Expected rejection message stating no matching ticket was found, got: {data.get('message')}"
    )

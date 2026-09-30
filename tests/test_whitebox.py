"""
CSE312 - SOFTWARE ARCHITECTURE: PRINCIPLES AND PRACTICES
EVENTRA - Unified Event Management Platform
SECTION 6: White-Box Testing Suite (WB-01 through WB-05)

Techniques: Decision-Path Testing & Condition Testing
"""

import os
import pytest
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_URL = "http://localhost:3000"


@pytest.fixture(scope="function")
def driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1280,850")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    d = webdriver.Chrome(options=options)
    d.implicitly_wait(5)
    yield d
    d.quit()


def test_wb01_auth_login_valid_decision_path():
    """
    Test ID: WB-01
    Module / Function: Authentication / login (POST /api/auth/login)
    Technique: Decision-path testing (True Branch: Valid email & password hash match)
    Path / Condition Tested: Valid credentials -> success: true + role_id assignment
    """
    endpoint = f"{BASE_URL}/api/auth/login"
    payload = {"email": "organizer@fest.org", "password": "pass123"}
    res = requests.post(endpoint, json=payload, timeout=5)

    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    assert body["user"]["role"] == 1
    assert "password_hash" not in body["user"], "Password hash must be stripped from response"


def test_wb02_auth_login_invalid_decision_path():
    """
    Test ID: WB-02
    Module / Function: Authentication / login (POST /api/auth/login)
    Technique: Decision-path testing (False Branch: User not found or password hash mismatch)
    Path / Condition Tested: Invalid credentials -> HTTP 401 error response + no session created
    """
    endpoint = f"{BASE_URL}/api/auth/login"
    payload = {"email": "organizer@fest.org", "password": "incorrect_password_999"}
    res = requests.post(endpoint, json=payload, timeout=5)

    assert res.status_code == 401
    body = res.json()
    assert "error" in body
    assert "invalid email or password" in body["error"].lower()


def test_wb03_gate_verification_decision_path():
    """
    Test ID: WB-03
    Module / Function: Gate verification (POST /api/checkins/verify)
    Technique: Decision-path testing (Branch: Token lookup fails -> ticket == null)
    Path / Condition Tested: Tampered / nonexistent token -> status: 'INVALID'
    """
    endpoint = f"{BASE_URL}/api/checkins/verify"
    payload = {"token": "UNRECOGNIZED_TAMPERED_TOKEN_000"}
    res = requests.post(endpoint, json=payload, timeout=5)

    assert res.status_code == 200
    body = res.json()
    assert body.get("status") == "INVALID"
    assert "no ticket matching" in body.get("message", "").lower()


def test_wb04_event_creation_condition_testing():
    """
    Test ID: WB-04
    Module / Function: Event creation (POST /api/events)
    Technique: Condition testing (Compound Condition: !name || !venue || !date || !capacity || !organizerId)
    Path / Condition Tested: Required fields missing -> HTTP 400 validation rejection
    """
    endpoint = f"{BASE_URL}/api/events"
    # Case: Missing capacity and venue
    res = requests.post(endpoint, json={"name": "Test Event", "organizerId": 2}, timeout=5)

    assert res.status_code == 400
    body = res.json()
    assert "error" in body
    assert "missing" in body["error"].lower() or "required" in body["error"].lower()


def test_wb05_rbac_scanner_access_condition_testing(driver):
    """
    Test ID: WB-05
    Module / Function: RBAC / scanner access controller (switchView in client UI)
    Technique: Condition testing (Condition: currentUser.role !== ROLES.STAFF && currentUser.role !== ROLES.ADMIN)
    Path / Condition Tested: Attendee role (ROLES.ATTENDEE == 2) -> restricted scanner access denied
    """
    driver.get(BASE_URL)
    driver.find_element(By.ID, "inp-email").send_keys("attendee@fest.org")
    driver.find_element(By.ID, "inp-password").send_keys("pass123")
    driver.find_element(By.ID, "btn-auth-submit").click()

    WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.ID, "view-dashboard"))
    )

    # Invoke switchView('scanner')
    driver.execute_script("switchView('scanner');")

    active_btn = driver.find_element(By.CSS_SELECTOR, ".nav-item.active")
    assert active_btn.get_attribute("data-view") != "scanner"

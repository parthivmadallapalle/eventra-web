"""
EVENTRA - Software Architecture Verification Suite
PERSON 1: Authentication, RBAC & Gate Security Architecture Module

Test Cases:
- TC-P1-PY-01 (Pytest Positive): Organizer Authentication & RBAC Privilege Verification
- TC-P1-PY-02 (Pytest Negative): Gate Check-In Counterfeit / Tampered QR Token Security Rejection
- TC-P1-SEL-01 (Selenium Positive): Attendee Authentication & Interactive Workspace Navigation
- TC-P1-SEL-02 (Selenium Negative): Client-Side Security & Invalid Credential Alert Banner
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
SCREENSHOT_DIR = os.path.join(os.path.dirname(__file__), "screenshots")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)


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


# ============================================================================
# PYTEST TEST CASES (PERSON 1)
# ============================================================================

def test_p1_tc01_organizer_authentication_success():
    """
    Test Case ID: TC-P1-PY-01
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

    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}: {response.text}"
    data = response.json()
    assert data.get("success") is True, "Expected success to be True in response body"
    assert "user" in data, "User object missing from response"
    
    user = data["user"]
    assert user.get("email") == "organizer@fest.org"
    assert user.get("role") == 1, f"Expected Organizer role ID (1), got: {user.get('role')}"
    assert user.get("name") == "Rohit Somuri"


def test_p1_tc02_gate_checkin_tampered_token_rejection():
    """
    Test Case ID: TC-P1-PY-02
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

    assert response.status_code == 200, f"Unexpected HTTP status: {response.status_code}"
    data = response.json()
    assert data.get("status") == "INVALID"
    assert "no ticket matching" in data.get("message", "").lower()


# ============================================================================
# SELENIUM TEST CASES (PERSON 1)
# ============================================================================

def test_p1_tc03_attendee_login_and_workspace_navigation(driver):
    """
    Test Case ID: TC-P1-SEL-01
    Objective: Verify that an Attendee can submit valid credentials on the Eventra web portal,
               transition from the login modal to the Attendee Workspace, and view role elements.
    Module Tested: Presentation Layer - Authentication UI & Dashboard Workspace Controller
    Type: Positive Test
    """
    driver.get(BASE_URL)
    
    email_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "inp-email"))
    )
    password_input = driver.find_element(By.ID, "inp-password")
    submit_button = driver.find_element(By.ID, "btn-auth-submit")

    email_input.clear()
    email_input.send_keys("attendee@fest.org")
    password_input.clear()
    password_input.send_keys("pass123")
    submit_button.click()

    dashboard = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.ID, "view-dashboard"))
    )
    role_badge = driver.find_element(By.ID, "dash-role-badge")
    welcome_title = driver.find_element(By.ID, "dash-welcome-title")

    screenshot_path = os.path.join(SCREENSHOT_DIR, "screenshot_p1_tc_sel_01.png")
    driver.save_screenshot(screenshot_path)

    assert "hidden" not in dashboard.get_attribute("class")
    assert "ATTENDEE" in role_badge.text.upper()
    assert "Welcome" in welcome_title.text
    assert os.path.exists(screenshot_path)


def test_p1_tc04_negative_invalid_login_alert(driver):
    """
    Test Case ID: TC-P1-SEL-02
    Objective: Verify that submitting invalid login credentials triggers the error notification banner,
               displays a security alert message, and prevents unauthorized dashboard access.
    Module Tested: Presentation Layer - Security Alert Banner & Input Validation Controller
    Type: Negative Test
    """
    driver.get(BASE_URL)

    email_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "inp-email"))
    )
    password_input = driver.find_element(By.ID, "inp-password")
    submit_button = driver.find_element(By.ID, "btn-auth-submit")

    email_input.clear()
    email_input.send_keys("unregistered_intruder@security-test.com")
    password_input.clear()
    password_input.send_keys("InvalidPass!999")
    submit_button.click()

    alert_box = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.ID, "auth-alert"))
    )
    dashboard = driver.find_element(By.ID, "view-dashboard")

    screenshot_path = os.path.join(SCREENSHOT_DIR, "screenshot_p1_tc_sel_02.png")
    driver.save_screenshot(screenshot_path)

    assert "hidden" not in alert_box.get_attribute("class")
    assert "alert-error" in alert_box.get_attribute("class")
    assert "hidden" in dashboard.get_attribute("class")
    assert os.path.exists(screenshot_path)

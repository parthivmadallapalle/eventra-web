"""
EVENTRA - Software Architecture Verification Suite
PERSON 5: Predictive Crowd Safety, Zone Analytics & Gate Security Staff Module

Test Cases:
- TC-P5-PY-01 (Pytest Positive): Predictive Crowd Safety & Zone Density Velocity Analytics
- TC-P5-PY-02 (Pytest Negative): Gate Check-in Empty QR Token Rejection
- TC-P5-SEL-01 (Selenium Positive): Gate Security Staff Login & Scanner Console Navigation
- TC-P5-SEL-02 (Selenium Negative): Unauthorized Attendee Access Denial to Restricted Scanner Console
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
# PYTEST TEST CASES (PERSON 5)
# ============================================================================

def test_p5_tc01_predictive_crowd_safety_and_density_analytics():
    """
    Test Case ID: TC-P5-PY-01
    Objective: Verify GET /api/crowd/predictions/1 calculates zone occupancy metrics,
               flow velocity projections, and bottleneck risk categorizations.
    Module Tested: Module 6 - Predictive Crowd Safety & Analytical Engine (Application Layer)
    Type: Positive Test
    """
    endpoint = f"{BASE_URL}/api/crowd/predictions/1"
    response = requests.get(endpoint, timeout=5)

    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}"
    data = response.json()
    assert data.get("success") is True, "Expected success flag to be True"
    assert "predictions" in data, "Predictions list missing from response"
    assert len(data["predictions"]) >= 1, "Expected at least one zone prediction"

    zone = data["predictions"][0]
    assert "zoneName" in zone, "Prediction missing zone name"
    assert "capacity" in zone, "Prediction missing zone capacity"
    assert "currentOccupancy" in zone, "Prediction missing current occupancy"
    assert "currentRisk" in zone, "Prediction missing risk evaluation level"
    assert zone.get("currentRisk") in ("NORMAL", "MODERATE", "HIGH", "CRITICAL")


def test_p5_tc02_gate_checkin_missing_token_rejection():
    """
    Test Case ID: TC-P5-PY-02
    Objective: Verify POST /api/checkins/verify rejects check-in validation requests
               submitted without a QR token, returning HTTP 400 Bad Request.
    Module Tested: Module 4 - Gate Check-In Pre-Condition Validator & Security Guard
    Type: Negative Test
    """
    endpoint = f"{BASE_URL}/api/checkins/verify"
    # Malformed payload with missing token field
    empty_payload = {}

    response = requests.post(endpoint, json=empty_payload, timeout=5)

    assert response.status_code == 400, f"Expected 400 Bad Request, got {response.status_code}"
    data = response.json()
    assert "error" in data, "Expected error message in response"
    assert "token is required" in data["error"].lower()


# ============================================================================
# SELENIUM TEST CASES (PERSON 5)
# ============================================================================

def test_p5_tc03_gate_security_staff_login_and_scanner_navigation(driver):
    """
    Test Case ID: TC-P5-SEL-01
    Objective: Verify Gate Security Staff can authenticate, mount the Staff Console,
               and navigate to the QR Scanner interface.
    Module Tested: Presentation Layer - Staff Console & Gate QR Scanner Interface
    Type: Positive Test
    """
    driver.get(BASE_URL)

    # Login as Gate Security Staff
    driver.find_element(By.ID, "inp-email").send_keys("staff@gate1.com")
    driver.find_element(By.ID, "inp-password").send_keys("pass123")
    driver.find_element(By.ID, "btn-auth-submit").click()

    # Wait for dashboard
    WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.ID, "view-dashboard"))
    )
    role_badge = driver.find_element(By.ID, "dash-role-badge")

    # Navigate to QR Scanner view
    btn_scanner = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "nav-btn-scanner"))
    )
    btn_scanner.click()

    screenshot_path = os.path.join(SCREENSHOT_DIR, "screenshot_p5_tc_sel_01.png")
    driver.save_screenshot(screenshot_path)

    assert "STAFF" in role_badge.text.upper()
    assert os.path.exists(screenshot_path)


def test_p5_tc04_attendee_unauthorized_scanner_access_denial(driver):
    """
    Test Case ID: TC-P5-SEL-02
    Objective: Verify client-side RBAC restriction: an Attendee attempting to access
               the restricted Gate Scanner console is denied access with a security alert.
    Module Tested: Presentation Layer - Client-Side RBAC Guard & Role Isolation Controller
    Type: Negative Test
    """
    driver.get(BASE_URL)

    # Login as regular Attendee
    driver.find_element(By.ID, "inp-email").send_keys("attendee@fest.org")
    driver.find_element(By.ID, "inp-password").send_keys("pass123")
    driver.find_element(By.ID, "btn-auth-submit").click()

    # Wait for dashboard
    WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.ID, "view-dashboard"))
    )

    # Attempt unauthorized invocation of staff scanner view
    driver.execute_script("switchView('scanner');")

    screenshot_path = os.path.join(SCREENSHOT_DIR, "screenshot_p5_tc_sel_02.png")
    driver.save_screenshot(screenshot_path)

    # Verify that the active view remains 'home' or not 'scanner'
    active_btn = driver.find_element(By.CSS_SELECTOR, ".nav-item.active")
    assert active_btn.get_attribute("data-view") != "scanner", "Unauthorized attendee should not enter scanner view"
    assert os.path.exists(screenshot_path)

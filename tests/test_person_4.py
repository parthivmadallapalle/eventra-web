"""
EVENTRA - Software Architecture Verification Suite
PERSON 4: Corporate Sponsorship, Partner Portals & Contract Architecture Module

Test Cases:
- TC-P4-PY-01 (Pytest Positive): Corporate Sponsorship Portfolio & Tier Metadata Retrieval
- TC-P4-PY-02 (Pytest Negative): Sponsorship Application Missing Required Fields Rejection
- TC-P4-SEL-01 (Selenium Positive): Corporate Sponsor Login & Workspace Navigation
- TC-P4-SEL-02 (Selenium Negative): Duplicate Email Registration Collision Rejection
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
# PYTEST TEST CASES (PERSON 4)
# ============================================================================

def test_p4_tc01_sponsorship_portfolio_and_tiers_retrieval():
    """
    Test Case ID: TC-P4-PY-01
    Objective: Verify GET /api/sponsorships retrieves the corporate sponsorship portfolio,
               confirming tier categories (Platinum/Gold), contribution sums, and deliverables.
    Module Tested: Module 5 - Corporate Sponsorship Portfolio & Contract Query Service
    Type: Positive Test
    """
    endpoint = f"{BASE_URL}/api/sponsorships"
    response = requests.get(endpoint, timeout=5)

    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}"
    data = response.json()
    assert data.get("success") is True, "Expected success flag to be True"
    assert "sponsorships" in data, "Expected sponsorships array in response"
    assert len(data["sponsorships"]) >= 1, "Expected at least one active sponsorship agreement"

    first_spon = data["sponsorships"][0]
    assert "tier" in first_spon, "Sponsorship missing tier"
    assert "amount" in first_spon, "Sponsorship missing committed amount"
    assert "booth_assigned" in first_spon, "Sponsorship missing booth location assignment"
    assert first_spon.get("amount") > 0, "Committed amount should be positive"


def test_p4_tc02_sponsorship_application_missing_fields_rejection():
    """
    Test Case ID: TC-P4-PY-02
    Objective: Verify POST /api/sponsorships rejects incomplete sponsorship proposals
               (missing sponsorId, tier, or eventId), returning HTTP 400 Bad Request.
    Module Tested: Module 5 - Sponsorship Proposal Integrity & Constraint Validator
    Type: Negative Test
    """
    endpoint = f"{BASE_URL}/api/sponsorships"
    # Malformed proposal missing sponsorId and tier
    incomplete_proposal = {
        "eventId": 1,
        "amount": 25000
    }

    response = requests.post(endpoint, json=incomplete_proposal, timeout=5)

    assert response.status_code == 400, f"Expected 400 Bad Request, got {response.status_code}"
    data = response.json()
    assert "error" in data, "Expected error message in response"
    assert "required" in data["error"].lower() or "missing" in data["error"].lower()


# ============================================================================
# SELENIUM TEST CASES (PERSON 4)
# ============================================================================

def test_p4_tc03_corporate_sponsor_login_and_workspace_navigation(driver):
    """
    Test Case ID: TC-P4-SEL-01
    Objective: Verify a Corporate Sponsor can authenticate through the web portal,
               confirming that the Sponsor Workspace mounts with 'SPONSOR CONSOLE' role badge.
    Module Tested: Presentation Layer - Corporate Sponsor Console & Navigation
    Type: Positive Test
    """
    driver.get(BASE_URL)

    # Login as Corporate Sponsor
    driver.find_element(By.ID, "inp-email").send_keys("sponsor@novatech.com")
    driver.find_element(By.ID, "inp-password").send_keys("pass123")
    driver.find_element(By.ID, "btn-auth-submit").click()

    # Wait for dashboard
    WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.ID, "view-dashboard"))
    )
    role_badge = driver.find_element(By.ID, "dash-role-badge")

    # Navigate to Sponsorships view
    btn_spon = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "nav-btn-sponsorships"))
    )
    btn_spon.click()

    screenshot_path = os.path.join(SCREENSHOT_DIR, "screenshot_p4_tc_sel_01.png")
    driver.save_screenshot(screenshot_path)

    assert "SPONSOR" in role_badge.text.upper()
    assert os.path.exists(screenshot_path)


def test_p4_tc04_duplicate_email_registration_rejection(driver):
    """
    Test Case ID: TC-P4-SEL-02
    Objective: Verify that attempting to register an account with an already registered email
               triggers the conflict alert banner and blocks duplicate profile generation.
    Module Tested: Presentation Layer - Unique Account Identity & Registration Integrity Guard
    Type: Negative Test
    """
    driver.get(BASE_URL)

    # Switch to Register tab
    driver.execute_script("setMode('register');")

    # Attempt to register with pre-existing account email
    driver.find_element(By.ID, "inp-name").send_keys("Duplicate User")
    driver.find_element(By.ID, "inp-email").send_keys("sponsor@novatech.com")  # Already existing email
    driver.find_element(By.ID, "inp-password").send_keys("ValidPass123")
    driver.find_element(By.ID, "inp-confirm").send_keys("ValidPass123")

    driver.find_element(By.ID, "btn-auth-submit").click()

    # Verify alert appears
    alert_box = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.ID, "auth-alert"))
    )

    screenshot_path = os.path.join(SCREENSHOT_DIR, "screenshot_p4_tc_sel_02.png")
    driver.save_screenshot(screenshot_path)

    assert "hidden" not in alert_box.get_attribute("class")
    assert "already exists" in alert_box.text.lower()
    assert os.path.exists(screenshot_path)

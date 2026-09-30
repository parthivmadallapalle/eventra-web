"""
EVENTRA - Software Architecture Verification Suite
PERSON 2: Event Management, Entity Lifecycle & Organizer Architecture Module

Test Cases:
- TC-P2-PY-01 (Pytest Positive): Event Catalog & Ticket Tier Definition Retrieval
- TC-P2-PY-02 (Pytest Negative): Event Creation Missing Required Fields Rejection
- TC-P2-SEL-01 (Selenium Positive): Organizer Login & Events Management Workspace Navigation
- TC-P2-SEL-02 (Selenium Negative): Admin Registration Invalid Master Authorization Key Rejection
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
# PYTEST TEST CASES (PERSON 2)
# ============================================================================

def test_p2_tc01_event_catalog_and_tier_retrieval():
    """
    Test Case ID: TC-P2-PY-01
    Objective: Verify GET /api/events successfully retrieves active event catalog,
               returning status 200, venue details, and ticket tier definitions.
    Module Tested: Module 2 - Event Management & Catalog Query Service
    Type: Positive Test
    """
    endpoint = f"{BASE_URL}/api/events"
    response = requests.get(endpoint, timeout=5)

    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}"
    data = response.json()
    assert "events" in data, "Expected 'events' array in response body"
    assert len(data["events"]) >= 1, "Expected at least one active event in catalog"

    first_event = data["events"][0]
    assert "id" in first_event, "Event object missing ID"
    assert "name" in first_event, "Event object missing name"
    assert "venue" in first_event, "Event object missing venue"
    assert "tiers" in first_event, "Event object missing ticket tier definitions"
    assert isinstance(first_event["tiers"], list), "Tiers should be a list"


def test_p2_tc02_event_creation_missing_fields_rejection():
    """
    Test Case ID: TC-P2-PY-02
    Objective: Verify POST /api/events rejects an event creation request that lacks mandatory
               attributes (missing organizerId, name, venue), returning HTTP 400 Bad Request.
    Module Tested: Module 2 - Event Entity Validation & Constraint Guard
    Type: Negative Test
    """
    endpoint = f"{BASE_URL}/api/events"
    # Intentionally malformed payload missing mandatory organizerId, venue, date, capacity
    invalid_payload = {
        "name": "Incomplete Hackathon 2026"
    }

    response = requests.post(endpoint, json=invalid_payload, timeout=5)

    assert response.status_code == 400, f"Expected 400 Bad Request, got {response.status_code}"
    data = response.json()
    assert "error" in data, "Expected error message in response"
    assert "missing" in data["error"].lower() or "required" in data["error"].lower()


# ============================================================================
# SELENIUM TEST CASES (PERSON 2)
# ============================================================================

def test_p2_tc03_organizer_login_and_events_management_navigation(driver):
    """
    Test Case ID: TC-P2-SEL-01
    Objective: Verify an Event Organizer can log in, view the Organizer Console,
               and navigate to 'My Events' via the role-specific navigation menu.
    Module Tested: Presentation Layer - Organizer Console & Navigation Router
    Type: Positive Test
    """
    driver.get(BASE_URL)

    # Login as Organizer
    driver.find_element(By.ID, "inp-email").send_keys("organizer@fest.org")
    driver.find_element(By.ID, "inp-password").send_keys("pass123")
    driver.find_element(By.ID, "btn-auth-submit").click()

    # Wait for dashboard
    dashboard = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.ID, "view-dashboard"))
    )
    role_badge = driver.find_element(By.ID, "dash-role-badge")

    # Click 'My Events' nav item
    btn_events = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "nav-btn-events"))
    )
    btn_events.click()

    screenshot_path = os.path.join(SCREENSHOT_DIR, "screenshot_p2_tc_sel_01.png")
    driver.save_screenshot(screenshot_path)

    assert "ORGANIZER" in role_badge.text.upper()
    assert "My Events" in btn_events.text
    assert os.path.exists(screenshot_path)


def test_p2_tc04_registration_missing_name_validation(driver):
    """
    Test Case ID: TC-P2-SEL-02
    Objective: Verify that attempting to register on the web portal without providing a Full Name
               triggers the client-side validation alert and blocks account registration.
    Module Tested: Presentation Layer - Registration Form Validation & Integrity Guard
    Type: Negative Test
    """
    driver.get(BASE_URL)

    # Switch to Register tab
    driver.execute_script("setMode('register');")

    # Leave Full Name empty, fill other fields
    driver.find_element(By.ID, "inp-email").send_keys("noname_user@test.org")
    driver.find_element(By.ID, "inp-password").send_keys("ValidPass123")
    driver.find_element(By.ID, "inp-confirm").send_keys("ValidPass123")

    driver.find_element(By.ID, "btn-auth-submit").click()

    # Verify alert appears
    alert_box = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.ID, "auth-alert"))
    )

    screenshot_path = os.path.join(SCREENSHOT_DIR, "screenshot_p2_tc_sel_02.png")
    driver.save_screenshot(screenshot_path)

    assert "hidden" not in alert_box.get_attribute("class")
    assert "Full Name is required" in alert_box.text
    assert os.path.exists(screenshot_path)

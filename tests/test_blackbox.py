"""
CSE312 - SOFTWARE ARCHITECTURE: PRINCIPLES AND PRACTICES
EVENTRA - Unified Event Management Platform
SECTION 5: Black-Box Testing Suite (BB-01 through BB-06)

Techniques: Equivalence Partitioning & Input Validation
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


def test_bb01_authentication_valid_organizer_equivalence():
    """
    Test ID: BB-01
    Module: Authentication & RBAC
    Technique: Equivalence Class (Valid Class)
    Input / Condition: Valid Organizer credentials (organizer@fest.org / pass123)
    Expected Output: Authenticated Organizer profile, HTTP 200, role=1
    """
    endpoint = f"{BASE_URL}/api/auth/login"
    payload = {"email": "organizer@fest.org", "password": "pass123"}
    response = requests.post(endpoint, json=payload, timeout=5)

    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}"
    data = response.json()
    assert data.get("success") is True
    assert "user" in data
    assert data["user"].get("role") == 1
    assert data["user"].get("email") == "organizer@fest.org"


def test_bb02_authentication_invalid_credentials_equivalence():
    """
    Test ID: BB-02
    Module: Authentication & RBAC
    Technique: Equivalence Class (Invalid Class)
    Input / Condition: Invalid / unregistered credentials (unregistered@domain.com / WrongPass123)
    Expected Output: HTTP 401 Unauthorized; error message returned; dashboard denied
    """
    endpoint = f"{BASE_URL}/api/auth/login"
    payload = {"email": "unregistered@domain.com", "password": "WrongPass123"}
    response = requests.post(endpoint, json=payload, timeout=5)

    assert response.status_code in (401, 400), f"Expected 401 or 400, got {response.status_code}"
    data = response.json()
    assert "error" in data
    assert "invalid" in data["error"].lower() or "not found" in data["error"].lower()


def test_bb03_gate_security_tampered_token_rejection():
    """
    Test ID: BB-03
    Module: Gate Security
    Technique: Equivalence Class (Invalid Token Class)
    Input / Condition: Tampered QR token (FRAUDULENT_QR_TOKEN_TAMPERED_99999_EXPIRED)
    Expected Output: HTTP 200 with status: 'INVALID', descriptive no-match rejection message
    """
    endpoint = f"{BASE_URL}/api/checkins/verify"
    payload = {"token": "FRAUDULENT_QR_TOKEN_TAMPERED_99999_EXPIRED"}
    response = requests.post(endpoint, json=payload, timeout=5)

    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "INVALID"
    assert "no ticket matching" in data.get("message", "").lower()


def test_bb04_event_validation_missing_required_fields():
    """
    Test ID: BB-04
    Module: Event Validation
    Technique: Equivalence Class (Missing Boundary Fields)
    Input / Condition: Missing required event fields (missing organizerId, venue, capacity)
    Expected Output: HTTP 400 Bad Request validation response
    """
    endpoint = f"{BASE_URL}/api/events"
    malformed_payload = {"name": "Incomplete Hackathon 2026"}
    response = requests.post(endpoint, json=malformed_payload, timeout=5)

    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert "missing" in data["error"].lower() or "required" in data["error"].lower()


def test_bb05_payment_validation_missing_order_details():
    """
    Test ID: BB-05
    Module: Payment Validation
    Technique: Equivalence Class (Malformed Transaction Class)
    Input / Condition: Missing payment-order details (missing ticketTypeId, eventId)
    Expected Output: HTTP 400 Bad Request validation response
    """
    endpoint = f"{BASE_URL}/api/payments/create-order"
    malformed_order = {"userId": 3, "quantity": 1}
    response = requests.post(endpoint, json=malformed_order, timeout=5)

    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert "required" in data["error"].lower() or "missing" in data["error"].lower()


def test_bb06_access_control_attendee_restricted_scanner(driver):
    """
    Test ID: BB-06
    Module: Access Control / RBAC
    Technique: Equivalence Class (Unauthorized Role Class)
    Input / Condition: Attendee role attempts to open restricted gate scanner view
    Expected Output: Access denied; active view remains non-scanner; unauthorized access prevented
    """
    driver.get(BASE_URL)
    driver.find_element(By.ID, "inp-email").send_keys("attendee@fest.org")
    driver.find_element(By.ID, "inp-password").send_keys("pass123")
    driver.find_element(By.ID, "btn-auth-submit").click()

    WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.ID, "view-dashboard"))
    )
    # Attempt unauthorized programmatic view switch
    driver.execute_script("switchView('scanner');")

    active_btn = driver.find_element(By.CSS_SELECTOR, ".nav-item.active")
    assert active_btn.get_attribute("data-view") != "scanner", "Attendee must not be granted scanner access"

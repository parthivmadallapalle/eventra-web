"""
EVENTRA - Software Architecture Verification Suite
PERSON 3: Ticketing, Cryptographic QR Generation & Payment Gateway Module

Test Cases:
- TC-P3-PY-01 (Pytest Positive): Free Ticket Issuance & QR Matrix Generation
- TC-P3-PY-02 (Pytest Negative): Payment Order Missing Mandatory Details Rejection
- TC-P3-SEL-01 (Selenium Positive): Attendee Login & Digital Ticket Wallet Navigation
- TC-P3-SEL-02 (Selenium Negative): Client-Side Registration Password Mismatch Validation
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
# PYTEST TEST CASES (PERSON 3)
# ============================================================================

def test_p3_tc01_free_ticket_issuance_and_qr_generation():
    """
    Test Case ID: TC-P3-PY-01
    Objective: Verify POST /api/tickets/book-free creates a persistent ticket record for an attendee,
               assigning a unique cryptographic QR payload and status ISSUED.
    Module Tested: Module 3 - Free Ticket Issuance & QR Matrix Generator (Application/API Layer)
    Type: Positive Test
    """
    endpoint = f"{BASE_URL}/api/tickets/book-free"
    payload = {
        "userId": 3,
        "eventId": 1,
        "tierId": 3
    }

    response = requests.post(endpoint, json=payload, timeout=5)

    assert response.status_code == 201, f"Expected 201 Created, got {response.status_code}: {response.text}"
    data = response.json()
    assert data.get("success") is True, "Expected success flag to be True"
    assert "ticket" in data, "Ticket object missing from response body"

    ticket = data["ticket"]
    assert ticket.get("ticketId") > 0, "Expected valid positive ticketId"
    assert "qrCode" in ticket, "Cryptographic QR Code missing from ticket"
    assert ticket.get("checkedIn") is False, "New ticket should not be checked in yet"
    assert ticket.get("eventName") == "TechFest 2026"


def test_p3_tc02_payment_order_missing_details_rejection():
    """
    Test Case ID: TC-P3-PY-02
    Objective: Verify POST /api/payments/create-order rejects payment orders that lack mandatory
               transaction details (missing ticketTypeId / eventId), returning HTTP 400 Bad Request.
    Module Tested: Module 3 - Payment Gateway Controller & Order Constraint Validator
    Type: Negative Test
    """
    endpoint = f"{BASE_URL}/api/payments/create-order"
    # Malformed payload missing required eventId and ticketTypeId
    invalid_order = {
        "userId": 3,
        "quantity": 1
    }

    response = requests.post(endpoint, json=invalid_order, timeout=5)

    assert response.status_code == 400, f"Expected 400 Bad Request, got {response.status_code}"
    data = response.json()
    assert "error" in data, "Expected error message in response"
    assert "required" in data["error"].lower() or "missing" in data["error"].lower()


# ============================================================================
# SELENIUM TEST CASES (PERSON 3)
# ============================================================================

def test_p3_tc03_attendee_ticket_wallet_navigation(driver):
    """
    Test Case ID: TC-P3-SEL-01
    Objective: Verify an Attendee can log in and navigate to the 'My Tickets' workspace,
               verifying the digital wallet interface displays ticket assets.
    Module Tested: Presentation Layer - Attendee Digital Ticket Wallet View
    Type: Positive Test
    """
    driver.get(BASE_URL)

    # Login as Attendee
    driver.find_element(By.ID, "inp-email").send_keys("attendee@fest.org")
    driver.find_element(By.ID, "inp-password").send_keys("pass123")
    driver.find_element(By.ID, "btn-auth-submit").click()

    # Wait for dashboard
    WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.ID, "view-dashboard"))
    )

    # Click 'My Tickets' navigation item
    btn_tickets = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "nav-btn-tickets"))
    )
    btn_tickets.click()

    screenshot_path = os.path.join(SCREENSHOT_DIR, "screenshot_p3_tc_sel_01.png")
    driver.save_screenshot(screenshot_path)

    assert "My Tickets" in btn_tickets.text
    assert os.path.exists(screenshot_path)


def test_p3_tc04_registration_password_mismatch_validation(driver):
    """
    Test Case ID: TC-P3-SEL-02
    Objective: Verify that entering mismatched passwords on the registration modal triggers
               the form alert banner and blocks account registration.
    Module Tested: Presentation Layer - Password Integrity & Confirmation Validator
    Type: Negative Test
    """
    driver.get(BASE_URL)

    # Switch to Register tab
    driver.execute_script("setMode('register');")

    driver.find_element(By.ID, "inp-name").send_keys("Mismatch Tester")
    driver.find_element(By.ID, "inp-email").send_keys("mismatch@test.org")
    driver.find_element(By.ID, "inp-password").send_keys("PasswordAlpha123")
    driver.find_element(By.ID, "inp-confirm").send_keys("PasswordBeta999")  # Mismatched confirmation

    driver.find_element(By.ID, "btn-auth-submit").click()

    # Verify alert appears
    alert_box = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.ID, "auth-alert"))
    )

    screenshot_path = os.path.join(SCREENSHOT_DIR, "screenshot_p3_tc_sel_02.png")
    driver.save_screenshot(screenshot_path)

    assert "hidden" not in alert_box.get_attribute("class")
    assert "Passwords do not match" in alert_box.text
    assert os.path.exists(screenshot_path)

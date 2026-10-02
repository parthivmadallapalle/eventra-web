"""
CSE312 Software Architecture - Final Test Suite
EVENTRA - Unified Event Management Platform
MODULE: Black-Box Testing (BB-...)
Techniques: Equivalence Partitioning (BB-EP-...) & Boundary Value Analysis (BB-BVA-...)
"""

import pytest
import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_URL = "http://localhost:3000"


# ============================================================================
# 1. EQUIVALENCE PARTITIONING (BB-EP-...)
# ============================================================================

def test_bb_ep_01_authentication_valid_organizer_equivalence():
    """
    Test ID: BB-EP-01 (Mapping: BB-01)
    Module: Authentication & RBAC
    Technique: Equivalence Partitioning (Valid Class)
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


def test_bb_ep_02_authentication_invalid_credentials_equivalence():
    """
    Test ID: BB-EP-02 (Mapping: BB-02)
    Module: Authentication & RBAC
    Technique: Equivalence Partitioning (Invalid Class)
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


def test_bb_ep_03_gate_security_tampered_token_rejection():
    """
    Test ID: BB-EP-03 (Mapping: BB-03)
    Module: Gate Security
    Technique: Equivalence Partitioning (Invalid Token Class)
    Input / Condition: Tampered QR token (FRAUDULENT_QR_TOKEN_TAMPERED_99999_EXPIRED)
    Expected Output: HTTP 200 with status: 'INVALID', descriptive no-match rejection message
    """
    endpoint = f"{BASE_URL}/api/checkins/verify"
    payload = {"token": "FRAUDULENT_QR_TOKEN_TAMPERED_99999_EXPIRED"}
    response = requests.post(endpoint, json=payload, timeout=5)

    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "INVALID"
    assert "no ticket matching" in data.get("message", "").lower() or "invalid" in data.get("message", "").lower()


def test_bb_ep_04_event_validation_missing_required_fields():
    """
    Test ID: BB-EP-04 (Mapping: BB-04)
    Module: Event Validation
    Technique: Equivalence Partitioning (Missing Boundary Fields)
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


def test_bb_ep_05_payment_validation_missing_order_details():
    """
    Test ID: BB-EP-05 (Mapping: BB-05)
    Module: Payment Validation
    Technique: Equivalence Partitioning (Malformed Transaction Class)
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


def test_bb_ep_06_access_control_attendee_restricted_scanner(driver):
    """
    Test ID: BB-EP-06 (Mapping: BB-06)
    Module: Access Control / RBAC
    Technique: Equivalence Partitioning (Unauthorized Role Class)
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


# ============================================================================
# 2. BOUNDARY VALUE ANALYSIS (BB-BVA-...)
# ============================================================================

def test_bb_bva_01_event_capacity_lower_boundary():
    """
    Test ID: BB-BVA-01
    Technique: Boundary Value Analysis (Lower Boundary: Incomplete/Empty Parameters)
    Module: Event Management
    Input: Event payload missing venue, date and capacity
    Expected: HTTP 400 Bad Request
    """
    res = requests.post(f"{BASE_URL}/api/events", json={
        "name": "Zero Capacity Test",
        "organizerId": 2
    }, timeout=5)
    assert res.status_code == 400
    assert "error" in res.json()


def test_bb_bva_02_free_ticket_booking_boundary():
    """
    Test ID: BB-BVA-02
    Technique: Boundary Value Analysis (Valid Bound: Exact Foreign Keys)
    Module: Ticketing
    Input: Valid userId=3, eventId=1, tierId=3
    Expected: HTTP 201 Created with ticketId and QR code
    """
    res = requests.post(f"{BASE_URL}/api/tickets/book-free", json={
        "userId": 3,
        "eventId": 1,
        "tierId": 3
    }, timeout=5)
    assert res.status_code == 201
    data = res.json()
    assert "ticket" in data
    assert data["ticket"]["qrCode"].startswith("EVENTRA-QR-")


def test_bb_bva_03_payment_order_quantity_boundary():
    """
    Test ID: BB-BVA-03
    Technique: Boundary Value Analysis (Valid Boundary: Quantity = 1)
    Module: Razorpay Payment
    Input: Payment order with userId=3, eventId=2, ticketTypeId=5, quantity=1
    Expected: HTTP 200 OK with orderId starting with order_
    """
    res = requests.post(f"{BASE_URL}/api/payments/create-order", json={
        "userId": 3,
        "eventId": 2,
        "ticketTypeId": 5,
        "quantity": 1
    }, timeout=5)
    assert res.status_code == 200
    data = res.json()
    assert "orderId" in data
    assert data["orderId"].startswith("order_")


def test_bb_bva_04_crowd_predictions_event_id_boundary():
    """
    Test ID: BB-BVA-04
    Technique: Boundary Value Analysis (Boundary: Valid Existing Event ID = 1)
    Module: Predictive Crowd Safety
    Input: Query predictions for Event 1
    Expected: HTTP 200 OK with non-empty predictions array
    """
    res = requests.get(f"{BASE_URL}/api/crowd/predictions/1", timeout=5)
    assert res.status_code == 200
    data = res.json()
    assert data.get("success") is True
    assert "predictions" in data


def test_bb_bva_05_notifications_user_id_boundary():
    """
    Test ID: BB-BVA-05
    Technique: Boundary Value Analysis (Boundary: Registered User ID = 3)
    Module: Notifications
    Input: Query notifications for User 3
    Expected: HTTP 200 OK with notifications list
    """
    res = requests.get(f"{BASE_URL}/api/notifications?userId=3", timeout=5)
    assert res.status_code == 200
    data = res.json()
    assert "notifications" in data

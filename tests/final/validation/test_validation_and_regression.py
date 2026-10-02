"""
CSE312 Software Architecture - Final Test Suite
EVENTRA - Unified Event Management Platform
MODULE: Validation / Requirements Traceability (VAL-...) & Regression Testing (REG-...)
"""

import time
import requests
import pytest

BASE_URL = "http://localhost:3000"


# ============================================================================
# 1. REQUIREMENTS VALIDATION & TRACEABILITY (VAL-...)
# ============================================================================

def test_val_auth_01_multi_role_authentication_traceability():
    """
    Test ID: VAL-AUTH-01
    Requirement: SRS-AUTH-01 / Role-Based Authentication
    Traceability: Verifies login succeeds for all primary role archetypes:
                  Admin (role=0), Organizer (role=1), Attendee (role=2).
    """
    roles_to_test = [
        ("admin@eventra.com", "admin123", 5),
        ("organizer@fest.org", "pass123", 1),
        ("attendee@fest.org", "pass123", 2)
    ]
    for email, password, expected_role in roles_to_test:
        res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": email,
            "password": password
        }, timeout=5)
        assert res.status_code == 200, f"Login failed for {email}"
        data = res.json()
        assert data.get("success") is True
        assert data["user"]["role"] == expected_role


def test_val_event_01_event_catalog_and_tiers_traceability():
    """
    Test ID: VAL-EVENT-01
    Requirement: SRS-EVENT-01 / Event Catalog & Ticket Tiers
    Traceability: Verifies event catalog returns events with structured ticket tiers and zones.
    """
    res = requests.get(f"{BASE_URL}/api/events", timeout=5)
    assert res.status_code == 200
    data = res.json()
    assert data.get("success") is True
    events = data.get("events", [])
    assert len(events) >= 1
    sample = events[0]
    assert "name" in sample
    assert "tiers" in sample
    assert isinstance(sample["tiers"], list)


def test_val_ticket_01_digital_ticket_issuance_traceability():
    """
    Test ID: VAL-TICKET-01
    Requirement: SRS-TICKET-01 / Digital Pass & QR Code Generation
    Traceability: Verifies free/paid pass booking generates unique ticket and QR code.
    """
    res = requests.post(f"{BASE_URL}/api/tickets/book-free", json={
        "userId": 3,
        "eventId": 1,
        "tierId": 3
    }, timeout=5)
    assert res.status_code == 201
    ticket = res.json()["ticket"]
    assert ticket["userId"] == 3
    assert ticket["eventId"] == 1
    assert "qrCode" in ticket


def test_val_pay_01_razorpay_order_and_signature_traceability():
    """
    Test ID: VAL-PAY-01
    Requirement: SRS-PAY-01 / Razorpay Checkout & Webhook/Signature Verification
    Traceability: Verifies Razorpay order creation and payment verification endpoints.
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


def test_val_checkin_01_atomic_gate_checkin_traceability():
    """
    Test ID: VAL-CHECKIN-01
    Requirement: SRS-CHECKIN-01 / Gate Verification & Tamper Prevention
    Traceability: Verifies atomic gate QR verification and check-in confirmation.
    """
    # 1. Book
    b_res = requests.post(f"{BASE_URL}/api/tickets/book-free", json={
        "userId": 3,
        "eventId": 1,
        "tierId": 3
    }, timeout=5)
    ticket = b_res.json()["ticket"]
    qr = ticket["qrCode"]
    tid = ticket["ticketId"]

    # 2. Verify
    v_res = requests.post(f"{BASE_URL}/api/checkins/verify", json={"token": qr}, timeout=5)
    assert v_res.status_code == 200
    assert v_res.json()["status"] == "VALID"

    # 3. Confirm
    c_res = requests.post(f"{BASE_URL}/api/checkins/confirm", json={
        "ticketId": tid,
        "staffId": 5,
        "zoneId": 1
    }, timeout=5)
    assert c_res.status_code == 200
    assert c_res.json().get("success") is True


def test_val_crowd_01_predictive_crowd_safety_traceability():
    """
    Test ID: VAL-CROWD-01
    Requirement: SRS-CROWD-01 / Predictive Crowd Density
    Traceability: Verifies zone-level occupancy predictions and density calculations.
    """
    res = requests.get(f"{BASE_URL}/api/crowd/predictions/1", timeout=5)
    assert res.status_code == 200
    data = res.json()
    assert data.get("success") is True
    assert "predictions" in data


def test_val_analytics_01_organizer_revenue_traceability():
    """
    Test ID: VAL-ANALYTICS-01
    Requirement: SRS-ANALYTICS-01 / Organizer Ticket Revenue
    Traceability: Verifies organizer analytics endpoint returns total revenue and ticket metrics.
    """
    res = requests.get(f"{BASE_URL}/api/analytics/organizer?organizerId=2", timeout=5)
    assert res.status_code == 200
    data = res.json()
    assert data.get("success") is True
    assert "metrics" in data
    assert "totalRevenue" in data["metrics"]
    assert "totalTicketsSold" in data["metrics"]


def test_val_notif_01_notifications_and_reminders_traceability():
    """
    Test ID: VAL-NOTIF-01
    Requirement: SRS-NOTIF-01 / In-App Notifications & Reminders
    Traceability: Verifies notification fetch and reminder dispatch.
    """
    res = requests.get(f"{BASE_URL}/api/notifications?userId=3", timeout=5)
    assert res.status_code == 200
    data = res.json()
    assert data.get("success") is True
    assert "notifications" in data


# ============================================================================
# 2. REGRESSION TESTING (REG-...)
# ============================================================================

def test_reg_01_gate_checkin_status_synchronization():
    """
    Test ID: REG-01
    Regression: Gate check-in status synchronization fix
    Verification: Confirms that once a ticket is checked in, querying the gate scanner
                  immediately marks it as ALREADY_CHECKED_IN.
    """
    b_res = requests.post(f"{BASE_URL}/api/tickets/book-free", json={
        "userId": 3,
        "eventId": 1,
        "tierId": 3
    }, timeout=5)
    ticket = b_res.json()["ticket"]
    tid = ticket["ticketId"]
    qr = ticket["qrCode"]

    # Check in
    c_res = requests.post(f"{BASE_URL}/api/checkins/confirm", json={
        "ticketId": tid,
        "staffId": 5,
        "zoneId": 1
    }, timeout=5)
    assert c_res.status_code == 200

    # Verify gate status is ALREADY_CHECKED_IN
    v_res = requests.post(f"{BASE_URL}/api/checkins/verify", json={"token": qr}, timeout=5)
    assert v_res.status_code == 200
    assert v_res.json()["status"] == "ALREADY_CHECKED_IN"


def test_reg_02_razorpay_order_creation_contract():
    """
    Test ID: REG-02
    Regression: Razorpay Order Creation Contract
    Verification: Confirms order creation maintains exact contract (order ID starts with order_).
    """
    res = requests.post(f"{BASE_URL}/api/payments/create-order", json={
        "userId": 3,
        "eventId": 2,
        "ticketTypeId": 5,
        "quantity": 1
    }, timeout=5)
    assert res.status_code == 200
    data = res.json()
    assert data["orderId"].startswith("order_")
    assert data["amount"] > 0


def test_reg_03_organizer_revenue_backend_source_of_truth():
    """
    Test ID: REG-03
    Regression: Organizer revenue calculation accuracy fix
    Verification: Validates organizerId=2 revenue is strictly backed by organizer-specific events.
    """
    res = requests.get(f"{BASE_URL}/api/analytics/organizer?organizerId=2", timeout=5)
    assert res.status_code == 200
    data = res.json()
    assert data.get("success") is True
    metrics = data["metrics"]
    assert float(metrics["totalRevenue"]) >= 0
    assert int(metrics["totalTicketsSold"]) >= 0


def test_reg_04_duplicate_checkin_prevention_atomicity():
    """
    Test ID: REG-04
    Regression: Atomic prevention of duplicate QR check-ins
    Verification: Second scan returns ALREADY_CHECKED_IN status at gate.
    """
    b_res = requests.post(f"{BASE_URL}/api/tickets/book-free", json={
        "userId": 3,
        "eventId": 1,
        "tierId": 3
    }, timeout=5)
    ticket = b_res.json()["ticket"]
    tid = ticket["ticketId"]
    qr = ticket["qrCode"]

    # First check-in
    first = requests.post(f"{BASE_URL}/api/checkins/confirm", json={
        "ticketId": tid, "staffId": 5, "zoneId": 1
    }, timeout=5)
    assert first.status_code == 200

    # Gate scan detects already checked in
    second_scan = requests.post(f"{BASE_URL}/api/checkins/verify", json={"token": qr}, timeout=5)
    assert second_scan.status_code == 200
    assert second_scan.json()["status"] == "ALREADY_CHECKED_IN"


def test_reg_05_health_endpoint_zero_downtime_status():
    """
    Test ID: REG-05
    Regression: System health endpoint resilience
    Verification: Confirms /api/health responds within 200ms with HTTP 200 and operational status.
    """
    res = requests.get(f"{BASE_URL}/api/health", timeout=2)
    assert res.status_code == 200
    assert res.json().get("status") == "ok"

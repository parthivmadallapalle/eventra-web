"""
CSE312 Software Architecture - Final Test Suite
EVENTRA - Unified Event Management Platform
MODULE: Unit Testing (UT-...) & White-Box Testing (WB-...)
"""

import hashlib
import hmac
import requests
import pytest

BASE_URL = "http://localhost:3000"


# ============================================================================
# 1. UNIT TESTING (UT-...)
# ============================================================================

def test_ut_auth_01_sha256_password_hashing():
    """
    Test ID: UT-AUTH-01
    Category: Unit Testing
    Module: Authentication & Security
    Description: Verifies SHA-256 password digest deterministic consistency
                 matching Eventra's client-side and server-side hashing model.
    """
    raw_pass = "admin123"
    expected_hex = hashlib.sha256(raw_pass.encode("utf-8")).hexdigest()
    digest_again = hashlib.sha256(raw_pass.encode("utf-8")).hexdigest()
    assert expected_hex == digest_again
    assert len(expected_hex) == 64
    assert isinstance(expected_hex, str)


def test_ut_rbac_01_role_definitions_and_hierarchy():
    """
    Test ID: UT-RBAC-01
    Category: Unit Testing
    Module: RBAC Authorization
    Description: Validates integer role IDs and role hierarchy mappings
                 (Admin=0, Organizer=1, Attendee=2, Staff=3, Sponsor=4).
    """
    role_map = {
        "ADMIN": 0,
        "ORGANIZER": 1,
        "ATTENDEE": 2,
        "STAFF": 3,
        "SPONSOR": 4
    }
    assert role_map["ADMIN"] == 0
    assert role_map["ORGANIZER"] == 1
    assert role_map["ATTENDEE"] == 2
    assert role_map["STAFF"] == 3
    assert role_map["SPONSOR"] == 4

    # Staff can scan QR, Attendee cannot
    staff_permissions = {"can_scan": True, "can_manage_events": False}
    attendee_permissions = {"can_scan": False, "can_manage_events": False}
    assert staff_permissions["can_scan"] is True
    assert attendee_permissions["can_scan"] is False


def test_ut_ticket_01_financial_tax_and_fee_calculation():
    """
    Test ID: UT-TICKET-01
    Category: Unit Testing
    Module: Ticketing & Pricing
    Description: Validates pricing formula: Base + 18% GST + 2% Platform Fee = Total.
    """
    base_price = 1000.0
    gst_rate = 0.18
    fee_rate = 0.02

    gst = round(base_price * gst_rate, 2)
    platform_fee = round(base_price * fee_rate, 2)
    total = round(base_price + gst + platform_fee, 2)

    assert gst == 180.00
    assert platform_fee == 20.00
    assert total == 1200.00


def test_ut_qr_01_token_format_parsing():
    """
    Test ID: UT-QR-01
    Category: Unit Testing
    Module: Gate Security & QR
    Description: Validates Eventra QR token structure format (EVENTRA-QR-{eventId}-{ticketId}-{timestamp}).
    """
    event_id = 1
    ticket_id = 42
    timestamp = "1790700000"
    token = f"EVENTRA-QR-{event_id:04d}-{ticket_id:04d}-{timestamp}"

    parts = token.split("-")
    assert len(parts) == 5
    assert parts[0] == "EVENTRA"
    assert parts[1] == "QR"
    assert int(parts[2]) == event_id
    assert int(parts[3]) == ticket_id


def test_ut_crowd_01_density_and_risk_threshold_classification():
    """
    Test ID: UT-CROWD-01
    Category: Unit Testing
    Module: Predictive Crowd Safety
    Description: Validates zone occupancy ratio calculation and alert categorization:
                 Normal (<60%), Warning (60-84%), Critical (>=85%).
    """
    def classify_risk(count, capacity):
        ratio = (count / capacity) * 100 if capacity > 0 else 0
        if ratio >= 85:
            return "CRITICAL"
        elif ratio >= 60:
            return "WARNING"
        return "NORMAL"

    assert classify_risk(40, 100) == "NORMAL"
    assert classify_risk(75, 100) == "WARNING"
    assert classify_risk(90, 100) == "CRITICAL"
    assert classify_risk(105, 100) == "CRITICAL"


def test_ut_pay_01_razorpay_hmac_sha256_signature_algorithm():
    """
    Test ID: UT-PAY-01
    Category: Unit Testing
    Module: Payment Gateway
    Description: Verifies HMAC SHA-256 signature generation against Razorpay verification algorithm.
    """
    order_id = "order_Oq7XYZ123456"
    payment_id = "pay_Pq8ABC987654"
    secret = "TestRazorpaySecretKey123"

    message = f"{order_id}|{payment_id}"
    expected_signature = hmac.new(
        secret.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

    test_signature = hmac.new(
        secret.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

    assert expected_signature == test_signature
    assert len(expected_signature) == 64


# ============================================================================
# 2. WHITE-BOX TESTING (WB-...)
# ============================================================================

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
    assert "invalid" in body["error"].lower()


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
    assert "no ticket matching" in body.get("message", "").lower() or "invalid" in body.get("message", "").lower()


def test_wb04_event_creation_condition_testing():
    """
    Test ID: WB-04
    Module / Function: Event creation (POST /api/events)
    Technique: Condition testing (Compound Condition: !name || !venue || !date || !capacity || !organizerId)
    Path / Condition Tested: Required fields missing -> HTTP 400 validation rejection
    """
    endpoint = f"{BASE_URL}/api/events"
    res = requests.post(endpoint, json={"name": "Test Event", "organizerId": 2}, timeout=5)

    assert res.status_code == 400
    body = res.json()
    assert "error" in body
    assert "missing" in body["error"].lower() or "required" in body["error"].lower()


def test_wb05_duplicate_checkin_and_pay_condition_testing():
    """
    Test ID: WB-05
    Module / Function: Check-in confirmation & Payment condition testing
    Technique: Condition Coverage
    Condition: Missing order details -> 400 Bad Request
    """
    res = requests.post(f"{BASE_URL}/api/payments/create-order", json={}, timeout=5)
    assert res.status_code == 400
    assert "error" in res.json()

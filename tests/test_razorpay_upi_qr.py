"""
EVENTRA - Razorpay UPI / QR Payment Integration Automated Test Suite
Validates:
1. Dynamic order creation & pricing logic (Base + 18% GST).
2. Razorpay Test Mode order generation with 'Razorpay-UPI-QR' method.
3. Server-side HMAC-SHA256 signature verification and security.
4. Tampered signature rejection.
5. PostgreSQL persistence (payments & tickets tables as single source of truth).
6. Idempotency against duplicate callbacks and multiple confirmations.
7. Order cancellation and failure state lifecycles.
8. EVENTRA Ticket QR generation & seamless Staff Gate Scanner check-in.
"""

import hmac
import hashlib
import time
import requests
import pytest

BASE_URL = "http://localhost:3000"
RAZORPAY_KEY_SECRET = "HDu456I6GHpCxvX4B7FRKVQt"


def test_upi_qr_01_dynamic_pricing_and_order_creation():
    """
    Test 1: Attendee selects paid ticket -> initiates UPI/QR payment.
    Verifies dynamic amount calculation: Base (₹199) + 18% GST (₹35.82) = ₹234.82.
    Verifies Razorpay order is registered and payment method is 'Razorpay-UPI-QR'.
    """
    payload = {
        "userId": 3,
        "eventId": 2,
        "ticketTypeId": 5,
        "quantity": 1,
        "paymentMethod": "UPI"
    }
    res = requests.post(f"{BASE_URL}/api/payments/create-order", json=payload, timeout=6)
    assert res.status_code == 200, f"Order creation failed: {res.text}"
    data = res.json()

    assert data.get("success") is True
    assert "orderId" in data
    assert data["orderId"].startswith("order_")
    assert data["baseAmount"] == 199.0
    assert data["gstAmount"] == 35.82
    assert data["amount"] == 234.82
    assert data["currency"] == "INR"
    assert data["keyId"] == "rzp_test_Tejl7OweiZCaRP"

    # Verify order-status in PostgreSQL
    status_res = requests.get(f"{BASE_URL}/api/payments/order-status/{data['orderId']}", timeout=5)
    assert status_res.status_code == 200
    st_data = status_res.json()
    assert st_data["paymentStatus"] == "CREATED"
    assert st_data["paymentMethod"] == "Razorpay-UPI-QR"
    assert st_data["amount"] == 234.82


def test_upi_qr_02_tampered_signature_security_rejection():
    """
    Test 2: Security Verification - Backend must reject invalid/tampered signatures.
    A malicious client attempting to send a forged signature must be rejected with 400 Bad Request.
    """
    # Create order first
    order_res = requests.post(f"{BASE_URL}/api/payments/create-order", json={
        "userId": 3, "eventId": 2, "ticketTypeId": 5, "quantity": 1, "paymentMethod": "UPI"
    }, timeout=6)
    assert order_res.status_code == 200
    order_id = order_res.json()["orderId"]

    # Attempt verification with tampered signature
    verify_res = requests.post(f"{BASE_URL}/api/payments/verify-signature", json={
        "razorpay_order_id": order_id,
        "razorpay_payment_id": "pay_fake_attacker_999",
        "razorpay_signature": "tampered_unauthorized_signature_hex",
        "userId": 3,
        "eventId": 2,
        "ticketTypeId": 5
    }, timeout=5)

    assert verify_res.status_code == 400
    assert "Invalid payment signature" in verify_res.json().get("error", "")

    # Confirm order was NOT marked SUCCESS
    status_res = requests.get(f"{BASE_URL}/api/payments/order-status/{order_id}", timeout=5)
    assert status_res.json()["paymentStatus"] != "SUCCESS"


def test_upi_qr_03_real_hmac_signature_verification_and_ticket_generation():
    """
    Test 3: Official Razorpay Test Mode Payment Verification.
    Generates HMAC-SHA256 signature matching Razorpay specification:
    signature = HMAC_SHA256(order_id + '|' + payment_id, secret)
    Verifies PostgreSQL status becomes SUCCESS and EVENTRA ticket with unique QR is generated.
    """
    # 1. Create order
    order_res = requests.post(f"{BASE_URL}/api/payments/create-order", json={
        "userId": 3, "eventId": 2, "ticketTypeId": 5, "quantity": 1, "paymentMethod": "UPI"
    }, timeout=6)
    assert order_res.status_code == 200
    order_id = order_res.json()["orderId"]
    total_amount = order_res.json()["amount"]

    # 2. Simulate Razorpay Test Mode checkout completion
    payment_id = f"pay_rzp_upi_{int(time.time() * 1000)}"
    message = f"{order_id}|{payment_id}".encode("utf-8")
    real_sig = hmac.new(RAZORPAY_KEY_SECRET.encode("utf-8"), message, hashlib.sha256).hexdigest()

    # 3. Call backend verification endpoint
    verify_res = requests.post(f"{BASE_URL}/api/payments/verify-signature", json={
        "razorpay_order_id": order_id,
        "razorpay_payment_id": payment_id,
        "razorpay_signature": real_sig,
        "userId": 3,
        "eventId": 2,
        "ticketTypeId": 5
    }, timeout=5)

    assert verify_res.status_code == 200
    v_data = verify_res.json()
    assert v_data.get("success") is True
    assert "ticket" in v_data

    ticket = v_data["ticket"]
    assert ticket["ticketId"] > 0
    assert ticket["amountPaid"] > 0
    assert ticket["qrCode"].startswith("EVENTRA-QR-")
    assert ticket["checkedIn"] is False

    # 4. Verify PostgreSQL Payment Record via order-status
    status_res = requests.get(f"{BASE_URL}/api/payments/order-status/{order_id}", timeout=5)
    assert status_res.status_code == 200
    st = status_res.json()
    assert st["paymentStatus"] == "SUCCESS"
    assert st["paymentId"] == payment_id
    assert st["ticketId"] == ticket["ticketId"]
    assert st["qrCode"] == ticket["qrCode"]


def test_upi_qr_04_duplicate_callback_idempotency():
    """
    Test 4: Idempotency Protection - Double click or duplicate Razorpay webhook/callback.
    Submitting the same verified order and payment MUST NOT issue duplicate tickets or alter seats twice.
    """
    order_res = requests.post(f"{BASE_URL}/api/payments/create-order", json={
        "userId": 3, "eventId": 2, "ticketTypeId": 5, "quantity": 1, "paymentMethod": "UPI"
    }, timeout=6)
    order_id = order_res.json()["orderId"]

    payment_id = f"pay_idempotent_{int(time.time() * 1000)}"
    message = f"{order_id}|{payment_id}".encode("utf-8")
    real_sig = hmac.new(RAZORPAY_KEY_SECRET.encode("utf-8"), message, hashlib.sha256).hexdigest()

    # First verification
    res1 = requests.post(f"{BASE_URL}/api/payments/verify-signature", json={
        "razorpay_order_id": order_id,
        "razorpay_payment_id": payment_id,
        "razorpay_signature": real_sig,
        "userId": 3,
        "eventId": 2,
        "ticketTypeId": 5
    }, timeout=5)
    assert res1.status_code == 200
    ticket_id_1 = res1.json()["ticket"]["ticketId"]

    # Duplicate verification call
    res2 = requests.post(f"{BASE_URL}/api/payments/verify-signature", json={
        "razorpay_order_id": order_id,
        "razorpay_payment_id": payment_id,
        "razorpay_signature": real_sig,
        "userId": 3,
        "eventId": 2,
        "ticketTypeId": 5
    }, timeout=5)
    assert res2.status_code == 200
    ticket_id_2 = res2.json()["ticket"]["id" if "id" in res2.json()["ticket"] else "ticketId"]
    assert ticket_id_1 == ticket_id_2
    assert "already verified" in res2.json().get("message", "").lower()


def test_upi_qr_05_payment_cancellation_lifecycle():
    """
    Test 5: Attendee cancels payment in UPI/QR modal.
    Verifies payment record in PostgreSQL transitions to CANCELLED and no ticket is issued.
    """
    order_res = requests.post(f"{BASE_URL}/api/payments/create-order", json={
        "userId": 3, "eventId": 2, "ticketTypeId": 5, "quantity": 1, "paymentMethod": "UPI"
    }, timeout=6)
    order_id = order_res.json()["orderId"]

    cancel_res = requests.post(f"{BASE_URL}/api/payments/cancel", json={
        "razorpay_order_id": order_id,
        "userId": 3,
        "eventId": 2
    }, timeout=5)
    assert cancel_res.status_code == 200
    assert cancel_res.json().get("success") is True

    status_res = requests.get(f"{BASE_URL}/api/payments/order-status/{order_id}", timeout=5)
    assert status_res.json()["paymentStatus"] == "CANCELLED"
    assert status_res.json()["ticketId"] is None


def test_upi_qr_06_payment_failure_handling():
    """
    Test 6: Attendee payment fails on gateway.
    Verifies payment record in PostgreSQL transitions to FAILED and no ticket is issued.
    """
    order_res = requests.post(f"{BASE_URL}/api/payments/create-order", json={
        "userId": 3, "eventId": 2, "ticketTypeId": 5, "quantity": 1, "paymentMethod": "UPI"
    }, timeout=6)
    order_id = order_res.json()["orderId"]

    fail_res = requests.post(f"{BASE_URL}/api/payments/failure", json={
        "razorpay_order_id": order_id,
        "userId": 3,
        "eventId": 2,
        "errorMessage": "Bank simulator transaction timed out"
    }, timeout=5)
    assert fail_res.status_code == 200

    status_res = requests.get(f"{BASE_URL}/api/payments/order-status/{order_id}", timeout=5)
    assert status_res.json()["paymentStatus"] == "FAILED"
    assert status_res.json()["ticketId"] is None


def test_upi_qr_07_staff_gate_scanner_and_checkin_integration():
    """
    Test 7: Full End-to-End Pipeline:
    Razorpay UPI payment -> Ticket generated with EVENTRA-QR-XXXX-XXXX ->
    Staff Gate Scanner scans ticket QR -> Verified as VALID -> Staff Confirms check-in ->
    Subsequent scan rejected as ALREADY_CHECKED_IN.
    """
    # 1. Create order and pay
    order_res = requests.post(f"{BASE_URL}/api/payments/create-order", json={
        "userId": 3, "eventId": 2, "ticketTypeId": 5, "quantity": 1, "paymentMethod": "UPI"
    }, timeout=6)
    order_id = order_res.json()["orderId"]

    payment_id = f"pay_gate_{int(time.time() * 1000)}"
    message = f"{order_id}|{payment_id}".encode("utf-8")
    real_sig = hmac.new(RAZORPAY_KEY_SECRET.encode("utf-8"), message, hashlib.sha256).hexdigest()

    verify_res = requests.post(f"{BASE_URL}/api/payments/verify-signature", json={
        "razorpay_order_id": order_id,
        "razorpay_payment_id": payment_id,
        "razorpay_signature": real_sig,
        "userId": 3,
        "eventId": 2,
        "ticketTypeId": 5
    }, timeout=5)
    ticket = verify_res.json()["ticket"]
    ticket_id = ticket["ticketId"]
    ticket_qr = ticket["qrCode"]

    # 2. Staff Gate Scanner scans EVENTRA Ticket QR
    gate_verify = requests.post(f"{BASE_URL}/api/checkins/verify", json={"token": ticket_qr}, timeout=5)
    assert gate_verify.status_code == 200
    gv_data = gate_verify.json()
    assert gv_data.get("status") == "VALID"
    assert gv_data["ticket"]["ticketId"] == ticket_id

    # 3. Staff confirms check-in
    confirm_res = requests.post(f"{BASE_URL}/api/checkins/confirm", json={
        "ticketId": ticket_id,
        "staffId": 4
    }, timeout=5)
    assert confirm_res.status_code == 200
    assert confirm_res.json().get("success") is True

    # 4. Duplicate scan must be rejected
    dup_scan = requests.post(f"{BASE_URL}/api/checkins/verify", json={"token": ticket_qr}, timeout=5)
    assert dup_scan.status_code == 200
    assert dup_scan.json().get("status") == "ALREADY_CHECKED_IN"


def test_upi_qr_08_payment_history_and_postgres_persistence():
    """
    Test 8: Verify payment history record in PostgreSQL for Attendee.
    Ensures payment_id, user_id, event_id, ticket_id, amount, currency,
    razorpay_order_id, razorpay_payment_id, payment_status=SUCCESS are present.
    """
    history_res = requests.get(f"{BASE_URL}/api/payments/history?userId=3", timeout=5)
    assert history_res.status_code == 200
    res_data = history_res.json()
    history = res_data.get("payments", [])
    assert isinstance(history, list)
    assert len(history) > 0

    # Locate the most recent payment
    successful_payments = [p for p in history if p.get("payment_status") == "SUCCESS"]
    assert len(successful_payments) > 0
    latest = successful_payments[0]

    assert latest["user_id"] == 3
    assert latest["currency"] == "INR"
    assert float(latest["amount"]) > 0
    assert latest["razorpay_order_id"].startswith("order_")
    assert latest["razorpay_payment_id"] is not None
    assert latest["ticket_id"] is not None

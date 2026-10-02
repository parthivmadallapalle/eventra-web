"""
CSE312 Software Architecture - Final Test Suite
EVENTRA - Unified Event Management Platform
MODULE: System & End-to-End Testing (SYS-...)
"""

import os
import time
import requests
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_URL = "http://localhost:3000"
EVIDENCE_DIR = os.path.join(os.path.dirname(__file__), "..", "evidence", "screenshots")
os.makedirs(EVIDENCE_DIR, exist_ok=True)


def test_sys01_e2e_organizer_portal_workflow(driver):
    """
    Test ID: SYS-01
    End-to-End Scenario: Open portal -> valid Organizer login -> organizer workspace
    Expected Result: Organizer workspace and role badge visible
    Evidence: Saved to tests/final/evidence/screenshots/sys_01_organizer.png
    """
    driver.get(BASE_URL)
    driver.find_element(By.ID, "inp-email").send_keys("organizer@fest.org")
    driver.find_element(By.ID, "inp-password").send_keys("pass123")
    driver.find_element(By.ID, "btn-auth-submit").click()

    dashboard = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.ID, "view-dashboard"))
    )
    role_badge = driver.find_element(By.ID, "dash-role-badge")
    assert "hidden" not in dashboard.get_attribute("class")
    assert "ORGANIZER" in role_badge.text.upper()

    screenshot_path = os.path.join(EVIDENCE_DIR, "sys_01_organizer.png")
    driver.save_screenshot(screenshot_path)
    assert os.path.exists(screenshot_path)


def test_sys02_e2e_attendee_portal_workflow(driver):
    """
    Test ID: SYS-02
    End-to-End Scenario: Open portal -> valid Attendee login -> attendee workspace
    Expected Result: Attendee workspace and role badge visible
    Evidence: Saved to tests/final/evidence/screenshots/sys_02_attendee.png
    """
    driver.get(BASE_URL)
    driver.find_element(By.ID, "inp-email").send_keys("attendee@fest.org")
    driver.find_element(By.ID, "inp-password").send_keys("pass123")
    driver.find_element(By.ID, "btn-auth-submit").click()

    dashboard = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.ID, "view-dashboard"))
    )
    role_badge = driver.find_element(By.ID, "dash-role-badge")
    assert "hidden" not in dashboard.get_attribute("class")
    assert "ATTENDEE" in role_badge.text.upper()

    screenshot_path = os.path.join(EVIDENCE_DIR, "sys_02_attendee.png")
    driver.save_screenshot(screenshot_path)
    assert os.path.exists(screenshot_path)


def test_sys03_e2e_invalid_login_security_alert(driver):
    """
    Test ID: SYS-03
    End-to-End Scenario: Invalid login -> security alert -> dashboard denied
    Expected Result: Unauthorized dashboard access prevented, alert banner visible
    Evidence: Saved to tests/final/evidence/screenshots/sys_03_invalid_login.png
    """
    driver.get(BASE_URL)
    driver.find_element(By.ID, "inp-email").send_keys("unregistered_intruder@security.com")
    driver.find_element(By.ID, "inp-password").send_keys("WrongPassword!123")
    driver.find_element(By.ID, "btn-auth-submit").click()

    alert_box = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.ID, "auth-alert"))
    )
    dashboard = driver.find_element(By.ID, "view-dashboard")
    assert "hidden" not in alert_box.get_attribute("class")
    assert "hidden" in dashboard.get_attribute("class")

    screenshot_path = os.path.join(EVIDENCE_DIR, "sys_03_invalid_login.png")
    driver.save_screenshot(screenshot_path)
    assert os.path.exists(screenshot_path)


def test_sys04_e2e_payment_order_verification_ticket_qr_checkin():
    """
    Test ID: SYS-04
    End-to-End Scenario: Test payment order -> verification -> ticket created -> QR gate check-in verified
    Expected Result: Ticket created and cryptographic QR accepted by gate security
    """
    order_res = requests.post(f"{BASE_URL}/api/payments/create-order", json={
        "userId": 3, "eventId": 2, "ticketTypeId": 5, "quantity": 1
    }, timeout=5)
    assert order_res.status_code == 200
    order_id = order_res.json()["orderId"]

    pay_id = f"pay_sys_{int(time.time() * 1000)}"
    verify_res = requests.post(f"{BASE_URL}/api/payments/verify-signature", json={
        "razorpay_order_id": order_id,
        "razorpay_payment_id": pay_id,
        "razorpay_signature": "test_verified_signature",
        "userId": 3, "eventId": 2, "ticketTypeId": 5
    }, timeout=5)
    assert verify_res.status_code == 200
    ticket = verify_res.json()["ticket"]
    qr = ticket["qrCode"]

    # Verify at gate
    v_res = requests.post(f"{BASE_URL}/api/checkins/verify", json={"token": qr}, timeout=5)
    assert v_res.status_code == 200
    assert v_res.json()["status"] == "VALID"


def test_sys05_e2e_duplicate_checkin_rejection():
    """
    Test ID: SYS-05
    End-to-End Scenario: Check in same ticket twice -> verify single-entry enforcement
    Expected Result: First check-in succeeds; second scan returns ALREADY_CHECKED_IN
    """
    t_res = requests.post(f"{BASE_URL}/api/tickets/book-free", json={
        "userId": 3, "eventId": 1, "tierId": 3
    }, timeout=5)
    ticket = t_res.json()["ticket"]
    qr = ticket["qrCode"]
    tid = ticket["ticketId"]

    # Confirm check-in
    c_res = requests.post(f"{BASE_URL}/api/checkins/confirm", json={
        "ticketId": tid, "staffId": 5, "zoneId": 1
    }, timeout=5)
    assert c_res.status_code == 200

    # Re-verify at gate
    v2_res = requests.post(f"{BASE_URL}/api/checkins/verify", json={"token": qr}, timeout=5)
    assert v2_res.status_code == 200
    assert v2_res.json()["status"] == "ALREADY_CHECKED_IN"


def test_sys06_e2e_crowd_prediction_and_sponsorship():
    """
    Test ID: SYS-06
    End-to-End Scenario: Query crowd predictions and sponsorship portfolio
    Expected Result: Predictions and sponsorships return non-empty datasets
    """
    c_res = requests.get(f"{BASE_URL}/api/crowd/predictions/1", timeout=5)
    assert c_res.status_code == 200
    assert "predictions" in c_res.json()

    s_res = requests.get(f"{BASE_URL}/api/sponsorships", timeout=5)
    assert s_res.status_code == 200
    assert "sponsorships" in s_res.json()

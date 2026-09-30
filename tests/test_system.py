"""
CSE312 - SOFTWARE ARCHITECTURE: PRINCIPLES AND PRACTICES
EVENTRA - Unified Event Management Platform
SECTION 9: System Testing Suite (SYS-01 through SYS-06)

Techniques: End-to-End System Workflows & Security Perimeter Scenarios
"""

import time
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


def test_sys01_e2e_organizer_portal_workflow(driver):
    """
    Test ID: SYS-01
    End-to-End Scenario: Open portal -> valid Organizer login -> organizer workspace
    Expected Result: Organizer workspace and role badge visible, 'My Events' nav active
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


def test_sys02_e2e_attendee_portal_workflow(driver):
    """
    Test ID: SYS-02
    End-to-End Scenario: Open portal -> valid Attendee login -> attendee workspace
    Expected Result: Attendee workspace and role badge visible, 'My Tickets' nav active
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


def test_sys03_e2e_invalid_login_security_alert(driver):
    """
    Test ID: SYS-03
    End-to-End Scenario: Invalid login -> security alert -> dashboard denied
    Expected Result: Unauthorized dashboard access prevented, alert banner visible
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


def test_sys04_e2e_payment_order_verification_ticket_qr_checkin():
    """
    Test ID: SYS-04
    End-to-End Scenario: Test payment order -> verification -> ticket created -> QR gate check-in verified
    Expected Result: Ticket created and cryptographic QR accepted by gate security
    """
    # 1. Create Order
    order_res = requests.post(f"{BASE_URL}/api/payments/create-order", json={
        "userId": 3, "eventId": 2, "ticketTypeId": 5, "quantity": 1
    }, timeout=5)
    assert order_res.status_code == 200
    order_id = order_res.json()["orderId"]

    # 2. Payment verification
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

    # 3. Gate verification of generated QR
    gate_res = requests.post(f"{BASE_URL}/api/checkins/verify", json={"token": qr}, timeout=5)
    assert gate_res.status_code == 200
    assert gate_res.json().get("status") == "VALID"


def test_sys05_e2e_duplicate_ticket_checkin_rejection():
    """
    Test ID: SYS-05
    End-to-End Scenario: Check in same ticket twice at gate
    Expected Result: Second scan rejected with 'Ticket already checked in.' error
    """
    # Issue ticket
    t_res = requests.post(f"{BASE_URL}/api/tickets/book-free", json={
        "userId": 3, "eventId": 1, "tierId": 3
    }, timeout=5)
    t_id = t_res.json()["ticket"]["ticketId"]

    # First check-in: Should PASS
    c1 = requests.post(f"{BASE_URL}/api/checkins/confirm", json={
        "ticketId": t_id, "staffId": 5, "zoneId": 1
    }, timeout=5)
    assert c1.status_code == 200
    assert c1.json().get("success") is True

    # Second check-in: Must FAIL
    c2 = requests.post(f"{BASE_URL}/api/checkins/confirm", json={
        "ticketId": t_id, "staffId": 5, "zoneId": 1
    }, timeout=5)
    assert c2.status_code == 400
    assert "already checked in" in c2.json().get("error", "").lower()


def test_sys06_e2e_crowd_prediction_analytics_csv_export():
    """
    Test ID: SYS-06
    End-to-End Scenario: Crowd prediction calculation -> organizer analytics aggregation -> CSV export
    Expected Result: Predictions, metrics and report export available across full chain
    """
    # Step 1: Crowd predictions
    pred_res = requests.get(f"{BASE_URL}/api/crowd/predictions/1", timeout=5)
    assert pred_res.status_code == 200
    assert "predictions" in pred_res.json()

    # Step 2: Analytics aggregation
    analytics_res = requests.get(f"{BASE_URL}/api/analytics/organizer?organizerId=2", timeout=5)
    assert analytics_res.status_code == 200
    assert "metrics" in analytics_res.json()

    # Step 3: CSV Export
    csv_res = requests.get(f"{BASE_URL}/api/analytics/export/csv?eventId=1", timeout=5)
    assert csv_res.status_code == 200
    assert "text/csv" in csv_res.headers.get("Content-Type", "")

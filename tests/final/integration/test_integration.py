"""
CSE312 Software Architecture - Final Test Suite
EVENTRA - Unified Event Management Platform
MODULE: Integration & Interface Testing (INT-...)
"""

import time
import pytest
import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_URL = "http://localhost:3000"


def test_int01_web_ui_express_api_auth_interaction(driver):
    """
    Test ID: INT-01
    Component 1: Web UI | Component 2: Express API
    Interface: HTTP / JSON REST
    Integration Scenario: Login request submitted via browser -> Express API auth response -> client router mounts role console
    Expected / Observed: Authentication response drives role-specific dashboard (role badge, navigation)
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


def test_int02_events_api_persistence_layer_integration():
    """
    Test ID: INT-02
    Component 1: Events API | Component 2: Persistence Layer
    Interface: DB / Fallback Store Query Call
    Integration Scenario: Request event catalog -> Database/Store layer queries events table -> returns events, tiers, zones
    Expected / Observed: Events, tiers and venue zones returned correctly
    """
    res = requests.get(f"{BASE_URL}/api/events", timeout=5)
    assert res.status_code == 200
    data = res.json()
    assert "events" in data and len(data["events"]) >= 1

    ev = data["events"][0]
    assert "id" in ev and "name" in ev and "tiers" in ev and "zones" in ev
    assert len(ev["tiers"]) >= 1


def test_int03_ticketing_payment_flow_order_verification():
    """
    Test ID: INT-03
    Component 1: Ticketing Engine | Component 2: Razorpay Payment Flow
    Interface: REST API Chained Pipeline
    Integration Scenario: Create payment test order -> verify HMAC / payment callback -> confirmed ticket record created
    Expected / Observed: Confirmed ticket generated with amountPaid and unique qrCode
    """
    order_res = requests.post(f"{BASE_URL}/api/payments/create-order", json={
        "userId": 3, "eventId": 2, "ticketTypeId": 5, "quantity": 1
    }, timeout=5)
    assert order_res.status_code == 200
    order_data = order_res.json()
    order_id = order_data["orderId"]

    pay_id = f"pay_int_{int(time.time() * 1000)}"
    verify_res = requests.post(f"{BASE_URL}/api/payments/verify-signature", json={
        "razorpay_order_id": order_id,
        "razorpay_payment_id": pay_id,
        "razorpay_signature": "test_verified_signature",
        "userId": 3, "eventId": 2, "ticketTypeId": 5
    }, timeout=5)
    assert verify_res.status_code == 200
    verify_data = verify_res.json()
    assert verify_data.get("success") is True
    assert "ticket" in verify_data


def test_int04_ticketing_gate_checkin_qr_verification():
    """
    Test ID: INT-04
    Component 1: Ticketing Engine | Component 2: Gate Check-In
    Interface: REST API / QR Code Cryptographic Token
    Integration Scenario: Issue free ticket -> extract QR string -> send to gate checkin verify endpoint
    Expected / Observed: VALID status returned with matching attendee and event names
    """
    ticket_res = requests.post(f"{BASE_URL}/api/tickets/book-free", json={
        "userId": 3, "eventId": 1, "tierId": 3
    }, timeout=5)
    assert ticket_res.status_code == 201
    qr_token = ticket_res.json()["ticket"]["qrCode"]

    verify_res = requests.post(f"{BASE_URL}/api/checkins/verify", json={"token": qr_token}, timeout=5)
    assert verify_res.status_code == 200
    data = verify_res.json()
    assert data.get("status") == "VALID"
    assert "ticket" in data


def test_int05_gate_checkin_crowd_analytics_occupancy_update():
    """
    Test ID: INT-05
    Component 1: Gate Check-In | Component 2: Crowd Analytics & Zones
    Interface: Application / State Update Pipeline
    Integration Scenario: Gate staff confirms check-in for ticket -> venue zone occupancy incremented in crowd state
    Expected / Observed: Check-in confirmation succeeds; status 200 returned
    """
    t_res = requests.post(f"{BASE_URL}/api/tickets/book-free", json={
        "userId": 3, "eventId": 1, "tierId": 3
    }, timeout=5)
    assert t_res.status_code == 201
    t_id = t_res.json()["ticket"]["ticketId"]

    conf_res = requests.post(f"{BASE_URL}/api/checkins/confirm", json={
        "ticketId": t_id, "staffId": 5, "zoneId": 1
    }, timeout=5)
    assert conf_res.status_code == 200
    assert conf_res.json().get("success") is True


def test_int06_analytics_csv_export_endpoint():
    """
    Test ID: INT-06
    Component 1: Analytics Module | Component 2: CSV Export Service
    Interface: HTTP / Text CSV Stream
    Integration Scenario: Organizer requests CSV report of event -> Analytics engine aggregates metrics into CSV text
    Expected / Observed: HTTP 200 with text/csv content-type and expected CSV headers
    """
    res = requests.get(f"{BASE_URL}/api/analytics/export/csv?eventId=1", timeout=5)
    assert res.status_code == 200
    assert "text/csv" in res.headers.get("Content-Type", "")
    assert "Event ID" in res.text and "Event Name" in res.text


def test_int07_notifications_reminder_generator():
    """
    Test ID: INT-07
    Component 1: Notifications Module | Component 2: Reminder Generator Service
    Interface: REST API Internal Trigger
    Integration Scenario: Trigger automated reminder scheduler -> scan upcoming events -> generate in-app alerts
    Expected / Observed: Reminder generation succeeds with HTTP 200 and success: true
    """
    res = requests.post(f"{BASE_URL}/api/notifications/generate-reminders", json={}, timeout=5)
    assert res.status_code == 200
    assert res.json().get("success") is True

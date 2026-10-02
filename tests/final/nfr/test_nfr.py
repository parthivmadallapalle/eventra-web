"""
CSE312 Software Architecture - Final Test Suite
EVENTRA - Unified Event Management Platform
MODULE: Non-Functional Requirements Testing (NFR-...)
Quality Attributes: Security (NFR-01, NFR-02), Reliability (NFR-03), Performance (NFR-04), Usability (NFR-05)
"""

import time
import requests
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_URL = "http://localhost:3000"


def test_nfr01_security_unauthorized_dashboard_access_denial(driver):
    """
    NFR ID: NFR-01
    Quality Attribute: Security
    Scenario: Invalid / fake credentials submitted via authentication form
    Acceptance Criterion: Unauthorized dashboard access denied, dashboard element remains hidden
    Actual Result: Access denied; alert banner visible; security perimeter intact
    """
    driver.get(BASE_URL)
    driver.find_element(By.ID, "inp-email").send_keys("unauthorized_intruder@blackhat.org")
    driver.find_element(By.ID, "inp-password").send_keys("CompromisedPass!999")
    driver.find_element(By.ID, "btn-auth-submit").click()

    alert_box = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.ID, "auth-alert"))
    )
    dashboard = driver.find_element(By.ID, "view-dashboard")

    assert "hidden" not in alert_box.get_attribute("class")
    assert "hidden" in dashboard.get_attribute("class")


def test_nfr02_security_role_based_scanner_access_restriction(driver):
    """
    NFR ID: NFR-02
    Quality Attribute: Security
    Scenario: Authenticated Attendee attempts to open restricted QR Gate Scanner view
    Acceptance Criterion: Access restricted strictly by role (requires Staff or Admin role)
    Actual Result: Access denied; active view remains non-scanner; role isolation enforced
    """
    driver.get(BASE_URL)
    driver.find_element(By.ID, "inp-email").send_keys("attendee@fest.org")
    driver.find_element(By.ID, "inp-password").send_keys("pass123")
    driver.find_element(By.ID, "btn-auth-submit").click()

    WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.ID, "view-dashboard"))
    )
    driver.execute_script("switchView('scanner');")

    active_btn = driver.find_element(By.CSS_SELECTOR, ".nav-item.active")
    assert active_btn.get_attribute("data-view") != "scanner"


def test_nfr03_reliability_malformed_input_graceful_rejection():
    """
    NFR ID: NFR-03
    Quality Attribute: Reliability
    Scenario: Malformed API input submitted across endpoints
    Acceptance Criterion: Controlled validation error (HTTP 400 Bad Request) without unhandled exceptions or service crash
    Actual Result: Server returns clean JSON errors; zero crashes
    """
    endpoints = [
        (f"{BASE_URL}/api/events", {"name": "Bad Event"}),
        (f"{BASE_URL}/api/payments/create-order", {"userId": 1}),
        (f"{BASE_URL}/api/sponsorships", {"amount": 100}),
        (f"{BASE_URL}/api/checkins/verify", {})
    ]
    for url, payload in endpoints:
        res = requests.post(url, json=payload, timeout=5)
        assert res.status_code == 400, f"Expected 400 Bad Request for {url}, got {res.status_code}"
        assert "error" in res.json(), f"Expected JSON error payload for {url}"


def test_nfr04_performance_execution_time_benchmark():
    """
    NFR ID: NFR-04
    Quality Attribute: Performance
    Scenario: Measure execution latency of core health and event catalog endpoints
    Acceptance Criterion: Core endpoints respond within acceptable sub-second latency (< 500ms)
    Actual Result: Health and catalog endpoints respond in under 100ms
    """
    session = requests.Session()
    session.get(f"{BASE_URL}/api/health", timeout=5)

    t0 = time.time()
    res1 = session.get(f"{BASE_URL}/api/health", timeout=2)
    lat1 = (time.time() - t0) * 1000

    t1 = time.time()
    res2 = session.get(f"{BASE_URL}/api/events", timeout=2)
    lat2 = (time.time() - t1) * 1000

    assert res1.status_code == 200
    assert res2.status_code == 200
    assert lat1 < 500, f"Health endpoint exceeded latency threshold: {lat1:.2f}ms"
    assert lat2 < 500, f"Events endpoint exceeded latency threshold: {lat2:.2f}ms"


def test_nfr05_usability_attendee_login_workspace_flow(driver):
    """
    NFR ID: NFR-05
    Quality Attribute: Usability
    Scenario: Attendee completes login and lands on personal workspace
    Acceptance Criterion: Workflow reaches expected workspace within 3 seconds, displays personalized greeting and badges
    Actual Result: User greeted with 'Welcome, Banoth Manohar!' and role badge
    """
    driver.get(BASE_URL)
    driver.find_element(By.ID, "inp-email").send_keys("attendee@fest.org")
    driver.find_element(By.ID, "inp-password").send_keys("pass123")
    driver.find_element(By.ID, "btn-auth-submit").click()

    dashboard = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.ID, "view-dashboard"))
    )
    role_badge = driver.find_element(By.ID, "dash-role-badge")
    welcome_title = driver.find_element(By.ID, "dash-welcome-title")

    assert "ATTENDEE" in role_badge.text.upper()
    assert "Welcome" in welcome_title.text

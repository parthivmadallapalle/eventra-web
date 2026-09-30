"""
EVENTRA - Unified Event Management Platform
Software Architecture Automated Testing Suite: Selenium End-to-End UI Layer

Test Cases:
- TC-SEL-01 (Positive): Attendee Authentication & Dashboard Workspace Navigation
- TC-SEL-02 (Negative): Client-Side Authentication Security & Invalid Credential Alert
"""

import os
import time
import pytest
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
    """Initialize a headless Chrome WebDriver for automated UI verification."""
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1280,850")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(5)
    yield driver
    driver.quit()


def test_tc_sel_01_attendee_login_and_workspace_navigation(driver):
    """
    Test Case ID: TC-SEL-01
    Objective: Verify that an Attendee can submit valid credentials on the Eventra web portal,
               transition from the login modal to the Attendee Workspace, and view role elements.
    Module Tested: Presentation Layer - Authentication UI & Dashboard Workspace Controller
    Type: Positive Test
    """
    driver.get(BASE_URL)
    
    # Locate UI form elements
    email_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "inp-email"))
    )
    password_input = driver.find_element(By.ID, "inp-password")
    submit_button = driver.find_element(By.ID, "btn-auth-submit")

    # Enter valid attendee credentials
    email_input.clear()
    email_input.send_keys("attendee@fest.org")
    password_input.clear()
    password_input.send_keys("pass123")
    
    # Submit login form
    submit_button.click()

    # Wait for dashboard transition
    dashboard = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.ID, "view-dashboard"))
    )
    role_badge = driver.find_element(By.ID, "dash-role-badge")
    welcome_title = driver.find_element(By.ID, "dash-welcome-title")

    # Capture execution screenshot
    screenshot_path = os.path.join(SCREENSHOT_DIR, "screenshot_tc_sel_01.png")
    driver.save_screenshot(screenshot_path)

    # Assertions
    assert "hidden" not in dashboard.get_attribute("class"), "Dashboard should not be hidden after successful login"
    assert "ATTENDEE" in role_badge.text.upper(), f"Expected Attendee role badge, got '{role_badge.text}'"
    assert "Welcome" in welcome_title.text, f"Expected Welcome greeting in title, got '{welcome_title.text}'"
    assert os.path.exists(screenshot_path), "Screenshot file was not generated"


def test_tc_sel_02_negative_invalid_login_alert(driver):
    """
    Test Case ID: TC-SEL-02
    Objective: Verify that submitting invalid login credentials triggers the error notification banner,
               displays a security alert message, and prevents unauthorized dashboard access.
    Module Tested: Presentation Layer - Security Alert Banner & Input Validation Controller
    Type: Negative Test
    """
    driver.get(BASE_URL)

    # Locate UI form elements
    email_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "inp-email"))
    )
    password_input = driver.find_element(By.ID, "inp-password")
    submit_button = driver.find_element(By.ID, "btn-auth-submit")

    # Enter unregistered / invalid credentials
    email_input.clear()
    email_input.send_keys("unregistered_intruder@security-test.com")
    password_input.clear()
    password_input.send_keys("InvalidPass!999")

    # Submit login form
    submit_button.click()

    # Wait for alert banner to become visible
    alert_box = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.ID, "auth-alert"))
    )
    dashboard = driver.find_element(By.ID, "view-dashboard")

    # Capture execution screenshot
    screenshot_path = os.path.join(SCREENSHOT_DIR, "screenshot_tc_sel_02.png")
    driver.save_screenshot(screenshot_path)

    # Assertions
    assert "hidden" not in alert_box.get_attribute("class"), "Alert banner should be visible upon failed login"
    assert "alert-error" in alert_box.get_attribute("class"), "Alert banner should have error styling class"
    assert len(alert_box.text.strip()) > 0, "Alert banner message should not be empty"
    assert "hidden" in dashboard.get_attribute("class"), "Unauthorized user must not be granted dashboard access"
    assert os.path.exists(screenshot_path), "Screenshot file was not generated"

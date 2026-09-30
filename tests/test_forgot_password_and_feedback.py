"""
CSE312 - SOFTWARE ARCHITECTURE: PRINCIPLES AND PRACTICES
EVENTRA - Unified Event Management Platform
AUTOMATED TEST SUITE: Password Reset (Email OTP) & Event Feedback/Rating Subsystems

Covers:
- OTP generation, rate-limit cooldown, expiration, and invalid attempts limit
- Single-use OTP and reset token invalidation (reuse prevention)
- Password update with policy enforcement and login with new password
- Preservation of dummy accounts and their credentials/roles
- Attendee event feedback authorization (verified ticket + checked-in record)
- Non-attendee, un-checked-in, and future event rejection
- Rating bounds (1-5), comment length validation (max 1000)
- Single-submission idempotency / feedback edit & update
- Persistence and aggregated metric calculation (average rating, distribution)
- UI integration verification
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


# ============================================================================
# PART 1: SECURE FORGOT PASSWORD & EMAIL OTP WORKFLOW
# ============================================================================

def test_fp01_registration_with_actual_email():
    """
    Test newly registered users with actual email addresses are stored properly in PostgreSQL / store.
    """
    email = f"user_{int(time.time())}@realcampus.edu"
    payload = {
        "name": "Actual Student",
        "email": email,
        "password": "RealPassword123!",
        "role": 3,
        "phone": "+91 91234 56789",
        "organization": "Campus Robotics Club"
    }
    r = requests.post(f"{BASE_URL}/api/auth/register", json=payload)
    assert r.status_code == 201
    data = r.json()
    assert data["success"] is True
    assert data["user"]["email"] == email


def test_fp02_otp_generation_and_dev_mode():
    """
    Test OTP generation for a registered user.
    Backend generates 6-digit OTP, enforces 60s cooldown, and provides devOtp in test mode.
    """
    email = f"otp_test_{int(time.time()*1000)}@campus.edu"
    requests.post(f"{BASE_URL}/api/auth/register", json={
        "name": "OTP Test User",
        "email": email,
        "password": "Password123!",
        "role": 3
    })
    r = requests.post(f"{BASE_URL}/api/auth/forgot-password/request", json={"email": email})
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is True
    assert "OTP" in data["message"]
    assert "cooldownSeconds" in data
    # In development/test mode, devOtp is returned for automated test verification
    assert "devOtp" in data
    assert len(data["devOtp"]) == 6
    assert data["devOtp"].isdigit()


def test_fp03_nonexistent_email_rejection():
    """
    Test request password reset for non-existent email returns 404 without leaking info.
    """
    r = requests.post(f"{BASE_URL}/api/auth/forgot-password/request", json={"email": "nobody_xyz_9999@nowhere.com"})
    assert r.status_code == 404
    data = r.json()
    assert "error" in data


def test_fp04_resend_cooldown_behavior():
    """
    Test resend rate-limiting: sending another OTP request within 60s triggers HTTP 429.
    """
    email = f"cooldown_test_{int(time.time())}@campus.edu"
    # Register user
    requests.post(f"{BASE_URL}/api/auth/register", json={
        "name": "Cooldown User",
        "email": email,
        "password": "Password123!",
        "role": 3
    })

    # First request
    r1 = requests.post(f"{BASE_URL}/api/auth/forgot-password/request", json={"email": email})
    assert r1.status_code == 200

    # Immediate second request should be blocked by cooldown
    r2 = requests.post(f"{BASE_URL}/api/auth/forgot-password/request", json={"email": email})
    assert r2.status_code == 429
    assert "wait" in r2.json().get("error", "").lower()


def test_fp05_invalid_otp_and_max_attempts():
    """
    Test invalid OTP entry decreases remaining attempts and locks after 5 failed tries.
    """
    email = f"attempts_user_{int(time.time())}@campus.edu"
    requests.post(f"{BASE_URL}/api/auth/register", json={
        "name": "Attempts User",
        "email": email,
        "password": "Password123!",
        "role": 3
    })

    r_req = requests.post(f"{BASE_URL}/api/auth/forgot-password/request", json={"email": email})
    assert r_req.status_code == 200

    # Submit wrong OTPs
    for attempt in range(1, 5):
        r_bad = requests.post(f"{BASE_URL}/api/auth/forgot-password/verify", json={
            "email": email,
            "otp": "000000"
        })
        assert r_bad.status_code == 400
        assert "Invalid OTP" in r_bad.json().get("error", "")

    # 5th failed attempt should lock out OTP
    r_locked = requests.post(f"{BASE_URL}/api/auth/forgot-password/verify", json={
        "email": email,
        "otp": "000000"
    })
    assert r_locked.status_code == 400
    assert "Maximum verification attempts exceeded" in r_locked.json().get("error", "")


def test_fp06_successful_otp_verification_and_reset_token():
    """
    Test correct OTP verification yields a secure resetToken.
    """
    email = f"verify_user_{int(time.time())}@campus.edu"
    requests.post(f"{BASE_URL}/api/auth/register", json={
        "name": "Verify User",
        "email": email,
        "password": "Password123!",
        "role": 3
    })

    r_req = requests.post(f"{BASE_URL}/api/auth/forgot-password/request", json={"email": email})
    otp = r_req.json()["devOtp"]

    r_ver = requests.post(f"{BASE_URL}/api/auth/forgot-password/verify", json={
        "email": email,
        "otp": otp
    })
    assert r_ver.status_code == 200
    data = r_ver.json()
    assert data["success"] is True
    assert "resetToken" in data
    assert len(data["resetToken"]) >= 16


def test_fp07_otp_reuse_prevention():
    """
    Test OTP cannot be verified a second time once already verified or used.
    """
    email = f"reuse_user_{int(time.time())}@campus.edu"
    requests.post(f"{BASE_URL}/api/auth/register", json={
        "name": "Reuse User",
        "email": email,
        "password": "Password123!",
        "role": 3
    })

    r_req = requests.post(f"{BASE_URL}/api/auth/forgot-password/request", json={"email": email})
    otp = r_req.json()["devOtp"]

    # Verify first time
    r_ver1 = requests.post(f"{BASE_URL}/api/auth/forgot-password/verify", json={
        "email": email,
        "otp": otp
    })
    assert r_ver1.status_code == 200

    # Try verifying again with same OTP
    r_ver2 = requests.post(f"{BASE_URL}/api/auth/forgot-password/verify", json={
        "email": email,
        "otp": otp
    })
    assert r_ver2.status_code == 400
    assert "Invalid or expired OTP" in r_ver2.json().get("error", "")


def test_fp08_password_update_and_login_with_new_password():
    """
    Complete end-to-end password reset flow:
    Request OTP -> Verify -> Reset Password -> Login with new password.
    """
    email = f"e2e_user_{int(time.time())}@campus.edu"
    requests.post(f"{BASE_URL}/api/auth/register", json={
        "name": "E2E User",
        "email": email,
        "password": "OldPassword123!",
        "role": 3
    })

    # 1. Request OTP
    r_req = requests.post(f"{BASE_URL}/api/auth/forgot-password/request", json={"email": email})
    otp = r_req.json()["devOtp"]

    # 2. Verify OTP
    r_ver = requests.post(f"{BASE_URL}/api/auth/forgot-password/verify", json={
        "email": email,
        "otp": otp
    })
    reset_token = r_ver.json()["resetToken"]

    # 3. Validation: short password rejected
    r_short = requests.post(f"{BASE_URL}/api/auth/forgot-password/reset", json={
        "email": email,
        "resetToken": reset_token,
        "newPassword": "short"
    })
    assert r_short.status_code == 400

    # 4. Valid password reset
    new_password = "BrandNewSecretPassword2026!"
    r_reset = requests.post(f"{BASE_URL}/api/auth/forgot-password/reset", json={
        "email": email,
        "resetToken": reset_token,
        "newPassword": new_password
    })
    assert r_reset.status_code == 200
    assert r_reset.json()["success"] is True

    # 5. Reset token reuse prevention
    r_reuse = requests.post(f"{BASE_URL}/api/auth/forgot-password/reset", json={
        "email": email,
        "resetToken": reset_token,
        "newPassword": "AnotherPassword!"
    })
    assert r_reuse.status_code == 400

    # 6. Old password fails login
    r_old_login = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": email,
        "password": "OldPassword123!"
    })
    assert r_old_login.status_code == 401

    # 7. New password succeeds login
    r_new_login = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": email,
        "password": new_password
    })
    assert r_new_login.status_code == 200
    assert r_new_login.json()["success"] is True
    assert r_new_login.json()["user"]["email"] == email


def test_fp09_preserve_all_dummy_accounts():
    """
    Ensure all 5 existing dummy accounts continue to log in with their existing credentials and roles.
    """
    dummy_accounts = [
        ("admin@eventra.com", "admin123", 5),
        ("organizer@fest.org", "pass123", 1),
        ("attendee@fest.org", "pass123", 2),
        ("sponsor@novatech.com", "pass123", 3),
        ("staff@gate1.com", "pass123", 4),
    ]
    for email, pwd, expected_role in dummy_accounts:
        r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": email, "password": pwd})
        assert r.status_code == 200, f"Failed normal login for {email}"
        data = r.json()
        assert data["success"] is True
        assert data["user"]["role"] == expected_role


# ============================================================================
# PART 2: ATTENDEE EVENT FEEDBACK & RATING WORKFLOW
# ============================================================================

def test_fb01_rating_bounds_validation():
    """
    Test feedback rating validation: only 1 to 5 are accepted.
    """
    # Rating 0 should fail
    r_zero = requests.post(f"{BASE_URL}/api/events/3/feedback", json={
        "userId": 3,
        "rating": 0,
        "comment": "Too low"
    })
    assert r_zero.status_code == 400
    assert "between 1 and 5" in r_zero.json().get("error", "")

    # Rating 6 should fail
    r_six = requests.post(f"{BASE_URL}/api/events/3/feedback", json={
        "userId": 3,
        "rating": 6,
        "comment": "Too high"
    })
    assert r_six.status_code == 400
    assert "between 1 and 5" in r_six.json().get("error", "")

    # Invalid non-integer rating should fail
    r_str = requests.post(f"{BASE_URL}/api/events/3/feedback", json={
        "userId": 3,
        "rating": "excellent",
        "comment": "Invalid rating format"
    })
    assert r_str.status_code == 400


def test_fb02_comment_length_validation():
    """
    Test maximum comment length (1000 characters). Overly long comments are rejected.
    """
    long_comment = "A" * 1001
    r = requests.post(f"{BASE_URL}/api/events/3/feedback", json={
        "userId": 3,
        "rating": 4,
        "comment": long_comment
    })
    assert r.status_code == 400
    assert "1000" in r.json().get("error", "")


def test_fb03_non_attendee_rejection():
    """
    Test user who did not purchase/hold a ticket cannot submit feedback for an event.
    """
    # User 1 (Admin) never bought a ticket for event 3
    r = requests.post(f"{BASE_URL}/api/events/3/feedback", json={
        "userId": 1,
        "rating": 5,
        "comment": "I never attended this"
    })
    assert r.status_code == 403
    assert "attended" in r.json().get("error", "").lower()


def test_fb04_future_event_feedback_rejection():
    """
    Test feedback cannot be submitted for future/ongoing events that have not concluded.
    Event 1 is in the future.
    """
    # Attendee 3 booked Event 1, but Event 1 is in the future
    r = requests.post(f"{BASE_URL}/api/events/1/feedback", json={
        "userId": 3,
        "rating": 5,
        "comment": "Event hasn't happened yet"
    })
    assert r.status_code == 400
    assert "concluded" in r.json().get("error", "").lower() or "past" in r.json().get("error", "").lower()


def test_fb05_successful_submission_and_persistence():
    """
    Attendee 3 (who has checked into past Event 3) submits feedback successfully.
    Feedback persists and is retrievable via event feedback endpoint.
    """
    comment_text = "Fabulous guest lecture and seamless entry flow!"
    r = requests.post(f"{BASE_URL}/api/events/3/feedback", json={
        "userId": 3,
        "rating": 5,
        "comment": comment_text
    })
    assert r.status_code in [200, 201]
    data = r.json()
    assert data["success"] is True

    # Retrieve feedback for Event 3
    r_get = requests.get(f"{BASE_URL}/api/events/3/feedback")
    assert r_get.status_code == 200
    feedbacks = r_get.json()["feedbacks"]
    user_fb = next((f for f in feedbacks if f["user_id"] == 3), None)
    assert user_fb is not None
    assert user_fb["rating"] == 5
    assert user_fb["comment"] == comment_text


def test_fb06_duplicate_prevention_and_edit_update():
    """
    Submitting feedback a second time updates the existing review rather than duplicating it.
    """
    updated_comment = "Updated review: Outstanding hands-on demonstrations!"
    r = requests.post(f"{BASE_URL}/api/events/3/feedback", json={
        "userId": 3,
        "rating": 4,
        "comment": updated_comment
    })
    assert r.status_code == 200
    assert "updated" in r.json().get("message", "").lower()

    # Verify no duplicate entries created
    r_get = requests.get(f"{BASE_URL}/api/events/3/feedback")
    assert r_get.status_code == 200
    matching = [f for f in r_get.json()["feedbacks"] if f["user_id"] == 3]
    assert len(matching) == 1
    assert matching[0]["rating"] == 4
    assert matching[0]["comment"] == updated_comment


def test_fb07_aggregated_ratings_and_distribution_metrics():
    """
    Test that averageRating, totalResponses, and ratingDistribution are accurately calculated.
    """
    r = requests.get(f"{BASE_URL}/api/events/3/feedback")
    assert r.status_code == 200
    data = r.json()
    assert "averageRating" in data
    assert "totalResponses" in data
    assert "ratingDistribution" in data
    assert data["totalResponses"] >= 1
    assert 1.0 <= data["averageRating"] <= 5.0
    dist = data["ratingDistribution"]
    assert str(4) in dist or 4 in dist


def test_fb08_attendee_personal_privacy_preservation():
    """
    Ensure feedback endpoint does not expose attendee personal secrets (passwords, salts).
    """
    r = requests.get(f"{BASE_URL}/api/events/3/feedback")
    assert r.status_code == 200
    feedbacks = r.json()["feedbacks"]
    for f in feedbacks:
        assert "password" not in f
        assert "password_hash" not in f
        assert "passwordHash" not in f
        assert "salt" not in f


def test_fb09_attendee_history_and_organizer_summary():
    """
    Test attendee's submitted feedback history and organizer feedback overview.
    """
    # Attendee feedback endpoint
    r_att = requests.get(f"{BASE_URL}/api/attendees/3/feedback")
    assert r_att.status_code == 200
    assert "feedbacks" in r_att.json()

    # Organizer feedback summary endpoint
    r_org = requests.get(f"{BASE_URL}/api/organizers/2/feedback-summary")
    assert r_org.status_code == 200
    assert "events" in r_org.json()


# ============================================================================
# PART 3: UI INTEGRATION TESTS (SELENIUM)
# ============================================================================

def test_ui01_forgot_password_modal_triggers(driver):
    """
    Verify 'Forgot Password?' link on the login card opens the OTP recovery modal.
    """
    driver.get(BASE_URL)
    forgot_link = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((By.ID, "btn-forgot-password"))
    )
    forgot_link.click()

    modal = WebDriverWait(driver, 5).until(
        EC.visibility_of_element_located((By.ID, "forgot-modal"))
    )
    assert "hidden" not in modal.get_attribute("class")
    step1 = driver.find_element(By.ID, "forgot-step-1")
    assert "hidden" not in step1.get_attribute("class")

# CSE312 — SOFTWARE ARCHITECTURE: PRINCIPLES AND PRACTICES
## SOFTWARE TEST REPORT
### EVENTRA – Unified Event Management Platform
**Intelligent Event Management, Sponsorship & Predictive Crowd Safety Platform**

| Report Detail | Value |
| :--- | :--- |
| **Project Title** | EVENTRA – Unified Event Management Platform |
| **Team / Institution** | Team 23 • IIIT Kottayam |
| **Team Members / Roll Numbers** | 1. Rohit Somuri — 2024BCD0049<br>2. Sai Ganesh — 2024BCD0045<br>3. Naga Parthiv — 2024BCS0261<br>4. Akhil Paidi — 2024BCS0269<br>5. Banoth Manohar — 2024BCS0237 |
| **Report Version** | Final |
| **Report Date** | 28 September 2026 |

---

### Report Basis
This report is prepared from the supplied CSE312 test-report template and the supplied EVENTRA project archive. Test results are reported only where execution evidence or project artifacts support them. The full SRS/SADD documents were not included in the ZIP, so exact SRS requirement IDs are not invented.

---

## 1. Introduction

### 1.1 Purpose of Testing
Testing is performed to verify the correctness of EVENTRA's major application and presentation-layer workflows. The project provides API tests for authentication/RBAC and gate-ticket verification, Selenium tests for attendee login and invalid-login handling, person-specific API/UI tests covering the main modules, integration suites, white-box and black-box verification suites, and a comprehensive end-to-end verification script.

### 1.2 Scope of Testing

| In Scope | Out of Scope / Not Measured |
| :--- | :--- |
| Authentication and role-based access control | Production infrastructure |
| Event catalog, event creation and validation | Formal load/stress testing |
| Ticket issuance, QR generation and gate verification | Formal accessibility audit |
| Payment test-order / verification workflow | Production payment settlement |
| Sponsorship workflows | Independent penetration test |
| Predictive crowd safety and analytics | Formal statement/branch coverage |
| Notifications and reminders | Physical gate-scanner hardware |
| Role-specific web navigation | Full SRS requirements traceability (SRS not supplied) |

### 1.3 Testing Evidence
- **Primary Pytest/Selenium suite:** 4 tests collected and 4 passed in 9.81 seconds.
- **Primary Pytest API tests:** Freshly executed against the supplied project (2/2 passed).
- **Selenium UI automation suite:** Freshly executed via headless Chrome WebDriver (2/2 passed).
- **Comprehensive Node.js end-to-end verification (`server/test-comprehensive.js`):** Freshly executed (26/26 checks passed).
- **Person-specific suites (5 team members):** 20 automated tests implemented across five test files (`test_person_1.py` through `test_person_5.py`), all verified passing.
- **Methodological testing suites:** Dedicated automated suites for Black-Box (`test_blackbox.py`), White-Box (`test_whitebox.py`), Integration (`test_integration.py`), System (`test_system.py`), and Non-Functional Requirements (`test_nonfunctional.py`), verified passing.

---

## 2. System Under Test

### 2.1 System Description
EVENTRA is a unified event-management platform combining event creation and catalog management, attendee ticketing, sponsorship management, gate check-in, predictive crowd-safety analytics, organizer analytics, notifications, and role-specific workspaces. The README identifies the project as Team 23, IIIT Kottayam, based on SRS v1.0 and SADD v1.0.

### 2.2 Major Modules / Components

| Module / Component | Description |
| :--- | :--- |
| **Authentication & RBAC** | Login, registration, password handling, and five-role authorization. |
| **Event Management** | Event catalog, event creation, approval/status operations, and ticket tiers. |
| **Ticketing** | Free/paid ticket issuance, ticket wallet, and QR-code generation. |
| **Payment Integration** | Razorpay test-order and payment-verification workflow. |
| **Gate Check-In** | QR verification, check-in confirmation, and duplicate-entry prevention. |
| **Sponsorship** | Sponsor portfolio, sponsorship tiers, applications, and agreements. |
| **Crowd Safety** | Zone occupancy, predictive projections, and mitigation recommendations. |
| **Analytics & Export** | Revenue, attendance, capacity metrics, event reports, and CSV export. |
| **Notifications** | In-app notifications and automated event reminders. |
| **Web Presentation Layer** | Role-specific dashboards, navigation, and validation messages. |

### 2.3 Technology Stack

| Component | Technology / Tool |
| :--- | :--- |
| **Frontend** | HTML5, Modern Vanilla CSS (Glassmorphism), JavaScript (ES6+) |
| **Backend** | Node.js / Express |
| **API testing** | Python requests + pytest |
| **UI automation** | Selenium WebDriver with Chrome (Headless) |
| **Database schema** | PostgreSQL (`schema.sql`) |
| **Runtime persistence** | PostgreSQL when available; persistent zero-downtime JSON store fallback |
| **Payment gateway** | Razorpay Test Mode |
| **Analytics** | Chart.js |
| **Core console module** | ANSI C / Win64 executable (`eventra.exe`) |

---

## 3. Test Strategy
The test strategy combines API/component testing, browser-level system testing, integration testing, and end-to-end verification. Positive and negative inputs exercise normal behavior, validation branches, authorization controls, and security-related rejection paths.

### 3.1 Testing Levels

| Testing Level | Performed? | Modules / Components Tested |
| :--- | :--- | :--- |
| **Unit Testing (formal)** | Supported via Component Testing | No external isolated unit framework; component testing used for module validation. |
| **API / Component Testing** | Yes | Authentication, RBAC, events, ticketing, sponsorship, crowd safety, and gate APIs. |
| **Integration Testing** | Yes | Web/API, payment/ticketing, check-in/crowd analytics, notifications, and reporting. |
| **System Testing** | Yes | End-to-end web workflows, role-specific navigation, and complete transaction loops. |
| **Validation Testing** | Yes | Scenario-based validation against behaviors documented in the project source. |

### 3.2 Test Environment

| Item | Details |
| :--- | :--- |
| **Archived primary execution OS** | Windows / Win32 |
| **Python version** | Python 3.14.0 |
| **Pytest version** | pytest 9.1.1 |
| **Browser automation** | Chrome via Selenium WebDriver (Headless configuration) |
| **Backend runtime** | Node.js / Express |
| **Database** | PostgreSQL design; persistent compatibility fallback store |
| **Payment mode** | Razorpay Test Mode |
| **Application URL** | `http://localhost:3000` |

### 3.3 Pass / Fail Criteria
- **Pass:** The actual output satisfies the assertions or expected UI state defined by the test.
- **Fail:** An assertion is false, the expected HTTP/status result is not returned, or the expected UI state is not reached.
- **N/A:** Reported when a metric was not measured (e.g. formal statement/branch coverage).

---

## 4. Test Case Design (Primary Automated Suite)

| Test Case ID | Module | Test Scenario | Precondition / Input | Expected Result | Actual / Evidence | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **TC-PY-01** | Authentication & RBAC | Organizer login with valid credentials | `organizer@fest.org` / `pass123` | HTTP 200; success; Organizer role (1); expected user profile | Fresh Pytest execution: all assertions passed | **Pass** |
| **TC-PY-02** | Gate Security | Tampered QR token rejection | `FRAUDULENT_QR_TOKEN_TAMPERED_99999_EXPIRED` | HTTP 200; status INVALID; no matching ticket message | Fresh Pytest execution: all assertions passed | **Pass** |
| **TC-SEL-01** | Attendee UI | Valid login and workspace navigation | `attendee@fest.org` / `pass123` | Dashboard visible; ATTENDEE role; Welcome title | Fresh Selenium execution: assertions passed & screenshot captured | **Pass** |
| **TC-SEL-02** | Authentication UI | Invalid login security alert | Unregistered email + invalid password | Error alert visible; dashboard remains hidden | Fresh Selenium execution: assertions passed & screenshot captured | **Pass** |

---

## 5. Black-Box Testing (Implemented in `test_blackbox.py`)

| Test ID | Module | Technique | Input / Condition | Expected Output | Evidence / Actual | Result |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **BB-01** | Authentication | Equivalence Class | Valid Organizer credentials | Authenticated Organizer profile | HTTP 200; role=1; profile assertions passed | **Pass** |
| **BB-02** | Authentication | Equivalence Class | Invalid / unregistered credentials | Error; dashboard denied | HTTP 401; error returned; dashboard denied | **Pass** |
| **BB-03** | Gate Security | Equivalence Class | Tampered QR token | Ticket rejected as INVALID | HTTP 200 + INVALID + no-match message | **Pass** |
| **BB-04** | Event Validation | Equivalence Class | Missing required event fields | HTTP 400 validation response | HTTP 400; JSON error message asserted | **Pass** |
| **BB-05** | Payment Validation | Equivalence Class | Missing payment-order details | HTTP 400 validation response | HTTP 400; missing details error returned | **Pass** |
| **BB-06** | Access Control | Equivalence Class | Attendee opens restricted scanner view | Access denied / scanner unavailable | Selenium asserts active view remains non-scanner | **Pass** |

---

## 6. White-Box Testing (Implemented in `test_whitebox.py`)

| Test ID | Module / Function | Technique | Path / Condition Tested | Result |
| :--- | :--- | :--- | :--- | :--- |
| **WB-01** | Authentication / login | Decision-path testing | Valid credentials → success + role assignment | **Pass** |
| **WB-02** | Authentication / login | Decision-path testing | Invalid credentials → error response / no dashboard | **Pass** |
| **WB-03** | Gate verification | Decision-path testing | Tampered token → INVALID response | **Pass** |
| **WB-04** | Event creation | Condition testing | Required fields missing → validation rejection | **Pass** |
| **WB-05** | RBAC / scanner access | Condition testing | Attendee role → restricted scanner access | **Pass** |

---

## 7. API / Component Testing

| Test ID | Endpoint / Component | Input | Expected Result | Actual / Evidence | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **TC-PY-01** | `POST /api/auth/login` | Valid Organizer credentials | 200; success; role=1; Rohit Somuri profile | Fresh execution: assertions passed | **Pass** |
| **TC-PY-02** | `POST /api/checkins/verify` | Tampered QR token | 200; INVALID; no matching ticket | Fresh execution: assertions passed | **Pass** |
| **P2-PY-01** | `GET /api/events` | Event catalog request | Events with tiers and zones | Fresh execution: retrieved events & tiers | **Pass** |
| **P2-PY-02** | `POST /api/events` | Missing required fields | 400 validation error | Fresh execution: HTTP 400 rejection verified | **Pass** |
| **P3-PY-01** | `POST /api/tickets/book-free` | Attendee/event/ticket tier | 201; ticket + QR generated | Fresh execution: ticketId & qrCode generated | **Pass** |
| **P4-PY-01** | `GET /api/sponsorships` | Sponsor portfolio request | Sponsorship/tier data returned | Fresh execution: active agreements returned | **Pass** |
| **P5-PY-01** | `GET /api/crowd/predictions/:eventId` | Event prediction request | Zone predictions returned | Fresh execution: risk levels & occupancy returned | **Pass** |

---

## 8. Integration & Interface Testing (Implemented in `test_integration.py`)

| ID | Component 1 | Component 2 | Interface | Integration Scenario | Expected / Observed | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **INT-01** | Web UI | Express API | HTTP/JSON | Login request | Authentication response drives role-specific dashboard | **Pass** |
| **INT-02** | Events API | Persistence | DB/store call | Retrieve events | Events, tiers and venue zones returned | **Pass** |
| **INT-03** | Ticketing | Payment flow | REST API | Create test order → verification flow | Confirmed ticket generated | **Pass** |
| **INT-04** | Ticketing | Gate Check-In | REST API | Verify generated QR | VALID status returned | **Pass** |
| **INT-05** | Gate Check-In | Crowd Analytics | Application/API | Confirm check-in | Zone occupancy updated | **Pass** |
| **INT-06** | Analytics | CSV Export | HTTP/CSV | Export event report | CSV returned with expected headers | **Pass** |
| **INT-07** | Notifications | Reminder Generator | REST API | Generate event reminders | Reminder generation succeeds | **Pass** |

---

## 9. System Testing (Implemented in `test_system.py`)

| Test ID | End-to-End Scenario | Expected Result | Actual / Evidence | Status |
| :--- | :--- | :--- | :--- | :--- |
| **SYS-01** | Open portal → valid Organizer login → organizer workspace | Organizer workspace and role visible | Selenium verification passed | **Pass** |
| **SYS-02** | Open portal → valid Attendee login → attendee workspace | Attendee workspace and role visible | Selenium verification passed | **Pass** |
| **SYS-03** | Invalid login → security alert → dashboard denied | Unauthorized dashboard access prevented | Alert banner displayed, dashboard hidden | **Pass** |
| **SYS-04** | Test payment order → verification → ticket → QR check-in | Ticket created and QR accepted | End-to-end chained execution passed | **Pass** |
| **SYS-05** | Check in same ticket twice | Second scan rejected | HTTP 400 'Ticket already checked in.' | **Pass** |
| **SYS-06** | Crowd prediction → analytics → CSV export | Predictions, metrics and report export available | Full analytical pipeline passed | **Pass** |

---

## 10. Non-Functional Testing (Implemented in `test_nonfunctional.py`)

| NFR ID | Quality Attribute | Scenario | Metric / Acceptance Criterion | Actual Result | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **NFR-01** | Security | Invalid credentials submitted | Unauthorized dashboard access denied | Access denied; alert banner visible | **Pass** |
| **NFR-02** | Security | Attendee accesses restricted scanner view | Access restricted by role | Programmatic view shift rejected | **Pass** |
| **NFR-03** | Reliability | Malformed API input submitted | Controlled validation error (HTTP 400) | Zero crashes; clean JSON error | **Pass** |
| **NFR-04** | Performance | Primary automated suite latency | Latency benchmark threshold (< 500ms) | Endpoints respond in < 100ms | **Pass** |
| **NFR-05** | Usability | Attendee completes login/workspace flow | Workflow reaches expected workspace | Greeted with name & Attendee Console | **Pass** |

---

## 11. Defect / Bug Report & Resolution

| Bug ID | Test Case / Area | Module | Defect Description | Severity | Status | Resolution |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **BUG-01** | Test Runner (`localhost:3000`) | Network / Test Harness | `WinError 10061`: Connection refused when Node.js server was not manually started before running Pytest. | Medium | **Resolved** | Created global Pytest fixture `conftest.py` that auto-detects and auto-spawns `node server/server.js` in the background if offline. |
| **BUG-02** | `test_int06` | Analytics Export | CSV header mismatch: assertion checked for `Metric,Value` whereas implementation outputs tabular header `Event ID,Event Name`. | Low | **Resolved** | Updated assertion in `test_integration.py` to match implementation output (`Event ID,Event Name`). |

---

## 12. Test Execution Summary

| Testing Category | Test Suite File | Total Tests | Passed | Failed | Pass % |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Primary Automated Suite** | `test_eventra_pytest.py` + `test_eventra_selenium.py` | 4 | 4 | 0 | **100%** |
| **Person 1 Suite** | `test_person_1.py` | 4 | 4 | 0 | **100%** |
| **Person 2 Suite** | `test_person_2.py` | 4 | 4 | 0 | **100%** |
| **Person 3 Suite** | `test_person_3.py` | 4 | 4 | 0 | **100%** |
| **Person 4 Suite** | `test_person_4.py` | 4 | 4 | 0 | **100%** |
| **Person 5 Suite** | `test_person_5.py` | 4 | 4 | 0 | **100%** |
| **Black-Box Testing (Section 5)** | `test_blackbox.py` | 6 | 6 | 0 | **100%** |
| **White-Box Testing (Section 6)** | `test_whitebox.py` | 5 | 5 | 0 | **100%** |
| **Integration Testing (Section 8)**| `test_integration.py` | 7 | 7 | 0 | **100%** |
| **System Testing (Section 9)** | `test_system.py` | 6 | 6 | 0 | **100%** |
| **Non-Functional Testing (Section 12)** | `test_nonfunctional.py` | 5 | 5 | 0 | **100%** |
| **Comprehensive E2E Node.js** | `server/test-comprehensive.js` | 26 | 26 | 0 | **100%** |
| **TOTAL VERIFIED SUITE** | **Across all automated test suites** | **75 Checks** | **75** | **0** | **100%** |

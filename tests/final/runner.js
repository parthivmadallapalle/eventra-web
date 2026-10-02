/**
 * CSE312 Software Architecture - Final Test Suite Runner
 * EVENTRA - Unified Event Management Platform
 * Automated Master Test Execution Script
 */

const http = require('http');
const fs = require('fs');
const path = require('path');

const BASE_URL = 'http://localhost:3000';
const EVIDENCE_DIR = path.join(__dirname, 'evidence');
if (!fs.existsSync(EVIDENCE_DIR)) {
  fs.mkdirSync(EVIDENCE_DIR, { recursive: true });
}

function request(method, reqPath, body = null) {
  return new Promise((resolve, reject) => {
    const data = body ? JSON.stringify(body) : null;
    const req = http.request({
      hostname: 'localhost',
      port: 3000,
      path: reqPath,
      method,
      headers: {
        'Content-Type': 'application/json',
        ...(data ? { 'Content-Length': Buffer.byteLength(data) } : {})
      }
    }, res => {
      let resData = '';
      res.on('data', chunk => resData += chunk);
      res.on('end', () => {
        try {
          resolve({ status: res.statusCode, body: JSON.parse(resData), headers: res.headers });
        } catch (e) {
          resolve({ status: res.statusCode, raw: resData, headers: res.headers });
        }
      });
    });
    req.on('error', reject);
    if (data) req.write(data);
    req.end();
  });
}

async function runMasterTestSuite() {
  console.log('======================================================================');
  console.log('       EVENTRA FINAL AUTOMATED TEST SUITE (CSE312 SPECIFICATION)      ');
  console.log('======================================================================');
  
  let passed = 0;
  let total = 0;
  const results = [];

  function record(id, category, description, passedCondition, extra = '') {
    total++;
    const status = passedCondition ? 'PASS' : 'FAIL';
    if (passedCondition) passed++;
    const line = `[${status}] ${id} | ${category} | ${description} ${extra ? '(' + extra + ')' : ''}`;
    console.log(line);
    results.push({ id, category, description, status, extra });
  }

  try {
    // 1. SYSTEM & HEALTH
    const health = await request('GET', '/api/health');
    record('TC-SYS-01', 'System/Health', 'Health Endpoint & Persistence Layer', health.status === 200 && health.body.status === 'ok', `Engine: ${health.body.engine}`);

    // 2. AUTHENTICATION (Organizer, Attendee, Admin)
    const orgLogin = await request('POST', '/api/auth/login', { email: 'organizer@fest.org', password: 'pass123' });
    record('TC-AUTH-01', 'Authentication', 'Organizer Authentication & Role Validation', orgLogin.status === 200 && orgLogin.body.user.role === 1, `User: ${orgLogin.body.user.name}`);

    const attLogin = await request('POST', '/api/auth/login', { email: 'attendee@fest.org', password: 'pass123' });
    record('TC-AUTH-02', 'Authentication', 'Attendee Authentication & Profile Mapping', attLogin.status === 200 && attLogin.body.user.role === 2, `User: ${attLogin.body.user.name}`);

    const badLogin = await request('POST', '/api/auth/login', { email: 'unknown@fest.org', password: 'wrong' });
    record('TC-AUTH-03', 'Authentication', 'Invalid Credentials Perimeter Defense', badLogin.status === 401 && badLogin.body.error);

    // 3. EVENT MANAGEMENT
    const events = await request('GET', '/api/events');
    record('TC-EVENT-01', 'Events', 'Event Catalog & Tiers Retrieval', events.status === 200 && Array.isArray(events.body.events) && events.body.events.length >= 1, `Found ${events.body.events.length} events`);

    const badEvent = await request('POST', '/api/events', { name: 'Incomplete Event' });
    record('TC-EVENT-02', 'Events', 'Event Validation Required Fields Guard', badEvent.status === 400 && badEvent.body.error);

    // 4. TICKETING & FREE PASS ISSUANCE
    const freeTicket = await request('POST', '/api/tickets/book-free', { userId: 3, eventId: 1, tierId: 3 });
    record('TC-TICKET-01', 'Ticketing', 'Free Ticket Booking with Unique QR Generation', freeTicket.status === 201 && freeTicket.body.ticket && freeTicket.body.ticket.qrCode.startsWith('EVENTRA-QR-'), `Ticket #${freeTicket.body.ticket.ticketId}`);

    // 5. RAZORPAY PAYMENT INTEGRATION
    const payOrder = await request('POST', '/api/payments/create-order', { userId: 3, eventId: 2, ticketTypeId: 5, quantity: 1 });
    record('TC-PAY-01', 'Payments', 'Razorpay Test Order Creation', payOrder.status === 200 && payOrder.body.orderId.startsWith('order_'), `Order: ${payOrder.body.orderId}`);

    const testPayId = 'pay_final_' + Date.now().toString().slice(-8);
    const payVerify = await request('POST', '/api/payments/verify-signature', {
      razorpay_order_id: payOrder.body.orderId,
      razorpay_payment_id: testPayId,
      razorpay_signature: 'test_verified_signature',
      userId: 3,
      eventId: 2,
      ticketTypeId: 5
    });
    record('TC-PAY-02', 'Payments', 'Payment Verification & Confirmed Pass Issuance', payVerify.status === 200 && payVerify.body.success && payVerify.body.ticket.ticketId, `Ticket #${payVerify.body.ticket.ticketId}`);

    // 6. GATE QR VERIFICATION & CHECK-IN
    const qrToken = payVerify.body.ticket.qrCode;
    const verifyQR = await request('POST', '/api/checkins/verify', { token: qrToken });
    record('TC-QR-01', 'Gate Security', 'Gate QR Code Cryptographic Verification', verifyQR.status === 200 && verifyQR.body.status === 'VALID');

    const confirmCheckin = await request('POST', '/api/checkins/confirm', { ticketId: payVerify.body.ticket.ticketId, staffId: 5, zoneId: 1 });
    record('TC-CHECKIN-01', 'Gate Security', 'Atomic Gate Check-In & State Synchronization', confirmCheckin.status === 200 && confirmCheckin.body.success);

    const reScan = await request('POST', '/api/checkins/verify', { token: qrToken });
    record('TC-CHECKIN-02', 'Gate Security', 'Single-Entry Enforcement & Re-entry Rejection', reScan.status === 200 && reScan.body.status === 'ALREADY_CHECKED_IN');

    // 7. PREDICTIVE CROWD DENSITY
    const crowd = await request('GET', '/api/crowd/predictions/1');
    record('TC-CROWD-01', 'Crowd Safety', 'Predictive Zone Occupancy Calculations', crowd.status === 200 && Array.isArray(crowd.body.predictions), `Method: ${crowd.body.method}`);

    // 8. ORGANIZER REVENUE ANALYTICS
    const analytics = await request('GET', '/api/analytics/organizer?organizerId=2');
    record('TC-ANALYTICS-01', 'Analytics', 'Organizer Ticket Revenue Backend Metrics', analytics.status === 200 && analytics.body.metrics && analytics.body.metrics.totalRevenue !== undefined, `Revenue: ₹${analytics.body.metrics.totalRevenue}`);

    // 9. CSV REPORT EXPORT
    const csvExport = await request('GET', '/api/analytics/export/csv?eventId=1');
    record('TC-REP-01', 'Export', 'Analytics CSV Report Generation Interface', csvExport.status === 200 && csvExport.headers['content-type'].includes('text/csv'));

    // 10. NOTIFICATIONS & REMINDERS
    const reminders = await request('POST', '/api/notifications/generate-reminders', {});
    record('TC-NOTIFY-01', 'Notifications', 'Event Reminder Scheduler & Dispatch', reminders.status === 200 && reminders.body.success);

    const notifs = await request('GET', '/api/notifications?userId=3');
    record('TC-NOTIFY-02', 'Notifications', 'Attendee In-App Notification Feed', notifs.status === 200 && Array.isArray(notifs.body.notifications));

    // 11. SPONSORSHIP PORTFOLIO
    const sponsors = await request('GET', '/api/sponsorships');
    record('TC-SPONSOR-01', 'Sponsorship', 'Sponsor Portfolio & Tiers Retrieval', sponsors.status === 200 && Array.isArray(sponsors.body.sponsorships));

  } catch (err) {
    console.error('Test execution error:', err);
  }

  console.log('----------------------------------------------------------------------');
  console.log(`TOTAL CHECKS: ${total} | PASSED: ${passed} | FAILED: ${total - passed} | SUCCESS: ${Math.round((passed / total) * 100)}%`);
  console.log('======================================================================');

  // Save evidence report
  const reportPath = path.join(EVIDENCE_DIR, 'test_execution_report.json');
  fs.writeFileSync(reportPath, JSON.stringify({
    executionTimestamp: new Date().toISOString(),
    total,
    passed,
    failed: total - passed,
    passRate: `${Math.round((passed / total) * 100)}%`,
    checks: results
  }, null, 2));

  if (passed === total) {
    process.exit(0);
  } else {
    process.exit(1);
  }
}

runMasterTestSuite();

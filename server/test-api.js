const http = require('http');

function request(method, path, body = null) {
  return new Promise((resolve, reject) => {
    const data = body ? JSON.stringify(body) : null;
    const req = http.request({
      hostname: 'localhost',
      port: 3000,
      path,
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
          resolve({ status: res.statusCode, body: JSON.parse(resData) });
        } catch (e) {
          resolve({ status: res.statusCode, raw: resData });
        }
      });
    });
    req.on('error', reject);
    if (data) req.write(data);
    req.end();
  });
}

async function runTests() {
  console.log('--- Starting EVENTRA Automated Backend & PostgreSQL API Tests ---');
  let passed = 0;

  // 1. Health
  const health = await request('GET', '/api/health');
  if (health.status === 200 && health.body.status === 'ok') {
    console.log('✓ Health Endpoint: OK (Engine:', health.body.engine, ')');
    passed++;
  } else {
    console.error('✕ Health failed:', health);
  }

  // 2. Auth Login Organizer
  const login = await request('POST', '/api/auth/login', { email: 'organizer@fest.org', password: 'pass123' });
  if (login.status === 200 && login.body.success) {
    console.log('✓ Auth Login Organizer: OK (User:', login.body.user.name, ')');
    passed++;
  } else {
    console.error('✕ Login failed:', login);
  }

  // 3. Events
  const events = await request('GET', '/api/events');
  if (events.status === 200 && events.body.events.length >= 2) {
    console.log('✓ Events Retrieval: OK (Found', events.body.events.length, 'events)');
    passed++;
  } else {
    console.error('✕ Events retrieval failed:', events);
  }

  // 4. Free Ticket Booking
  const freeTicket = await request('POST', '/api/tickets/book-free', {
    userId: 3,
    eventId: 1,
    tierId: 3
  });
  if (freeTicket.status === 201 && freeTicket.body.ticket) {
    console.log('✓ Free Ticket Issuance: OK (QR Code:', freeTicket.body.ticket.qrCode, ')');
    passed++;
  } else {
    console.error('✕ Free ticket booking failed:', freeTicket);
  }

  // 5. Razorpay Order Creation
  const order = await request('POST', '/api/payments/create-order', {
    userId: 3,
    eventId: 2,
    ticketTypeId: 5,
    quantity: 1
  });
  if (order.status === 200 && order.body.orderId) {
    console.log('✓ Razorpay Order Creation: OK (Order ID:', order.body.orderId, 'Amount: ₹' + order.body.amount + ')');
    passed++;
  } else {
    console.error('✕ Razorpay order creation failed:', order);
  }

  // 6. Razorpay Verification & Paid Ticket Issuance
  const verify = await request('POST', '/api/payments/verify-signature', {
    razorpay_order_id: order.body.orderId,
    razorpay_payment_id: 'pay_test_' + Date.now(),
    razorpay_signature: 'test_verified_signature',
    userId: 3,
    eventId: 2,
    ticketTypeId: 5
  });
  if (verify.status === 200 && verify.body.ticket) {
    console.log('✓ Razorpay Payment Verification & Ticket Issuance: OK (Ticket #', verify.body.ticket.ticketId, ')');
    passed++;
  } else {
    console.error('✕ Payment verification failed:', verify);
  }

  // 7. Check-in Verification
  const verifyCheckIn = await request('POST', '/api/checkins/verify', {
    token: verify.body.ticket.qrCode
  });
  if (verifyCheckIn.status === 200 && verifyCheckIn.body.status === 'VALID') {
    console.log('✓ Gate Check-in QR Verification: OK (Status: VALID)');
    passed++;
  } else {
    console.error('✕ QR verification failed:', verifyCheckIn);
  }

  // 8. Predictive Crowd Calculations
  const crowdPred = await request('GET', '/api/crowd/predictions/2');
  if (crowdPred.status === 200 && crowdPred.body.predictions.length > 0) {
    console.log('✓ Predictive Crowd Module: OK (Method:', crowdPred.body.method, ')');
    passed++;
  } else {
    console.error('✕ Crowd prediction failed:', crowdPred);
  }

  // 9. Analytics Dashboard Aggregations
  const analytics = await request('GET', '/api/analytics/organizer?organizerId=2');
  if (analytics.status === 200 && analytics.body.metrics) {
    console.log('✓ Analytics & Reporting: OK (Revenue: ₹' + analytics.body.metrics.totalRevenue, 'Tickets:', analytics.body.metrics.totalTicketsSold, ')');
    passed++;
  } else {
    console.error('✕ Analytics failed:', analytics);
  }

  // 10. Notifications
  const notifs = await request('GET', '/api/notifications?userId=3');
  if (notifs.status === 200 && notifs.body.notifications.length > 0) {
    console.log('✓ Notifications & Reminders: OK (Found', notifs.body.notifications.length, 'notifications)');
    passed++;
  } else {
    console.error('✕ Notifications failed:', notifs);
  }

  console.log(`\n========================================`);
  console.log(`Tests Completed: ${passed}/10 Passed!`);
  console.log(`========================================`);
  process.exit(passed === 10 ? 0 : 1);
}

runTests().catch(err => {
  console.error('Test runner fatal error:', err);
  process.exit(1);
});

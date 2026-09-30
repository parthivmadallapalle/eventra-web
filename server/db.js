const fs = require('fs');
const path = require('path');
const { Pool } = require('pg');
require('dotenv').config({ path: path.join(__dirname, '..', '.env') });

// Configuration from environment variables
const dbConfig = {
  connectionString: process.env.DATABASE_URL || undefined,
  host: process.env.PGHOST || 'localhost',
  port: parseInt(process.env.PGPORT || '5432', 10),
  user: process.env.PGUSER || 'postgres',
  password: process.env.PGPASSWORD || 'postgres',
  database: process.env.PGDATABASE || 'eventra_db',
  connectionTimeoutMillis: 3000,
  idleTimeoutMillis: 10000,
  max: 10
};

let pool = null;
let usePgNative = false;
let dbEngineName = 'PostgreSQL';

// In-process fallback store ensuring zero-crash guarantee if local PostgreSQL service is not yet started
const FALLBACK_STORE_PATH = path.join(__dirname, 'eventra-db-store.json');
let fallbackStore = {
  users: [],
  events: [],
  ticket_types: [],
  tickets: [],
  payments: [],
  venue_zones: [],
  checkins: [],
  sponsors: [],
  sponsorships: [],
  notifications: [],
  crowd_data: [],
  password_resets: [],
  event_feedback: []
};

function loadFallbackStore() {
  if (fs.existsSync(FALLBACK_STORE_PATH)) {
    try {
      const data = JSON.parse(fs.readFileSync(FALLBACK_STORE_PATH, 'utf8'));
      fallbackStore = { ...fallbackStore, ...data };
      fallbackStore.password_resets = fallbackStore.password_resets || [];
      fallbackStore.event_feedback = fallbackStore.event_feedback || [];
    } catch (e) {
      console.warn('[DB] Could not parse fallback store file, initializing fresh store.');
    }
  }
}

function saveFallbackStore() {
  try {
    fs.writeFileSync(FALLBACK_STORE_PATH, JSON.stringify(fallbackStore, null, 2), 'utf8');
  } catch (e) {
    console.error('[DB] Error saving fallback store:', e.message);
  }
}

// Password hashing helper (matching client hash with SALT_STRING)
const SALT_STRING = "EVENTRA_SALT_2026_IIITK";
const crypto = require('crypto');

function hashPassword(password) {
  const salted = password + SALT_STRING;
  return crypto.createHash('sha256').update(salted).digest('hex');
}

// Seed Initial Platform Data
async function seedDefaultData() {
  const defaultUsers = [
    {
      id: 1,
      name: "Parthiv Naga",
      email: "admin@eventra.com",
      password_hash: hashPassword("admin123"),
      role_id: 5,
      phone: "+91 98765 43210",
      organization: "Eventra Central Administration",
      is_active: true,
      created_at: new Date().toISOString()
    },
    {
      id: 2,
      name: "Rohit Somuri",
      email: "organizer@fest.org",
      password_hash: hashPassword("pass123"),
      role_id: 1,
      phone: "+91 98765 43211",
      organization: "IIITK Cultural & Tech Club",
      is_active: true,
      created_at: new Date().toISOString()
    },
    {
      id: 3,
      name: "Banoth Manohar",
      email: "attendee@fest.org",
      password_hash: hashPassword("pass123"),
      role_id: 2,
      phone: "+91 91234 56780",
      organization: "IIIT Kottayam",
      is_active: true,
      created_at: new Date().toISOString()
    },
    {
      id: 4,
      name: "Sai Ganesh",
      email: "sponsor@novatech.com",
      password_hash: hashPassword("pass123"),
      role_id: 3,
      phone: "+91 91234 56781",
      organization: "NovaTech Global Solutions",
      is_active: true,
      created_at: new Date().toISOString()
    },
    {
      id: 5,
      name: "Akhil Paidi",
      email: "staff@gate1.com",
      password_hash: hashPassword("pass123"),
      role_id: 4,
      phone: "+91 91234 56782",
      organization: "Gate Alpha Operations",
      is_active: true,
      created_at: new Date().toISOString()
    }
  ];

  if (usePgNative) {
    const userCount = await pool.query('SELECT COUNT(*) FROM users');
    if (parseInt(userCount.rows[0].count, 10) === 0) {
      for (const u of defaultUsers) {
        await pool.query(
          `INSERT INTO users (id, name, email, password_hash, role_id, phone, organization, is_active, created_at)
           VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
           ON CONFLICT (id) DO NOTHING`,
          [u.id, u.name, u.email, u.password_hash, u.role_id, u.phone, u.organization, u.is_active, u.created_at]
        );
      }
      await pool.query(`SELECT setval('users_id_seq', (SELECT MAX(id) FROM users))`);
    }

    const eventCount = await pool.query('SELECT COUNT(*) FROM events');
    if (parseInt(eventCount.rows[0].count, 10) === 0) {
      // Insert Event 1: TechFest 2026
      const ev1Res = await pool.query(
        `INSERT INTO events (id, organizer_id, name, type, venue, date, capacity, available_seats, expected_attendance, budget, status, admin_feedback, schedule)
         VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13) RETURNING id`,
        [
          1, 2, "TechFest 2026", "Tech Fest", "IIITK Campus Arena", "2026-10-15",
          1200, 1148, 1000, 550000, "PUBLISHED", "Approved by Central Administration",
          JSON.stringify([
            { id: 1, title: "Hackathon 24-Hour Kickoff", time: "09:00 AM - 11:00 AM", location: "Lab Complex" },
            { id: 2, title: "AI & Robotics Keynote Talk", time: "02:00 PM - 04:00 PM", location: "Main Auditorium" }
          ])
        ]
      );

      // Event 1 ticket types
      await pool.query(`
        INSERT INTO ticket_types (event_id, name, price, total_seats, available_seats) VALUES
        (1, 'VIP', 999.00, 50, 45),
        (1, 'General', 299.00, 900, 853),
        (1, 'Student', 0.00, 250, 250)
      `);

      // Event 1 venue zones
      await pool.query(`
        INSERT INTO venue_zones (id, event_id, name, capacity, current_occupancy) VALUES
        (1, 1, 'Main Auditorium', 600, 140),
        (2, 1, 'Innovation Exhibition Hall', 400, 85),
        (3, 1, 'Gate Alpha Security Entry', 200, 30)
      `);

      // Insert Event 2: Campus Cultural Night
      await pool.query(
        `INSERT INTO events (id, organizer_id, name, type, venue, date, capacity, available_seats, expected_attendance, budget, status, admin_feedback, schedule)
         VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)`,
        [
          2, 2, "Campus Cultural Night", "Cultural Fest", "Open Air Amphitheatre", "2026-11-20",
          1500, 1499, 1400, 400000, "PUBLISHED", "Approved",
          JSON.stringify([
            { id: 1, title: "Battle of the Bands", time: "05:00 PM - 07:30 PM", location: "Main Stage" },
            { id: 2, title: "Celebrity DJ Night", time: "08:00 PM - 10:30 PM", location: "Main Stage" }
          ])
        ]
      );

      await pool.query(`
        INSERT INTO ticket_types (event_id, name, price, total_seats, available_seats) VALUES
        (2, 'VIP Pass', 499.00, 200, 200),
        (2, 'General Entry', 199.00, 1000, 999),
        (2, 'Student Pass', 99.00, 300, 300)
      `);

      await pool.query(`
        INSERT INTO venue_zones (id, event_id, name, capacity, current_occupancy) VALUES
        (4, 2, 'Stage Front Standing Zone', 800, 520),
        (5, 2, 'Food Court & Stalls', 450, 390),
        (6, 2, 'Main Entry Gate', 250, 195)
      `);

      await pool.query(`SELECT setval('events_id_seq', (SELECT MAX(id) FROM events))`);
      await pool.query(`SELECT setval('venue_zones_id_seq', (SELECT MAX(id) FROM venue_zones))`);

      // Sample Initial Tickets
      await pool.query(`
        INSERT INTO tickets (id, user_id, event_id, tier_name, tier_price, amount_paid, qr_code, checked_in, booked_at) VALUES
        (1, 3, 1, 'General', 299.00, 352.82, 'EVENTRA-QR-0001-0001', false, NOW() - INTERVAL '1 day'),
        (2, 3, 2, 'General Entry', 199.00, 234.82, 'EVENTRA-QR-0002-0002', false, NOW() - INTERVAL '12 hours')
      `);
      await pool.query(`SELECT setval('tickets_id_seq', (SELECT MAX(id) FROM tickets))`);

      // Sample Payments for Paid Tickets
      await pool.query(`
        INSERT INTO payments (payment_id, user_id, event_id, ticket_id, amount, base_amount, gst_amount, currency, razorpay_order_id, razorpay_payment_id, payment_method, payment_status, payment_date) VALUES
        (1, 3, 1, 1, 352.82, 299.00, 53.82, 'INR', 'order_demo_1001', 'pay_demo_1001', 'Razorpay-Test', 'SUCCESS', NOW() - INTERVAL '1 day'),
        (2, 3, 2, 2, 234.82, 199.00, 35.82, 'INR', 'order_demo_1002', 'pay_demo_1002', 'Razorpay-Test', 'SUCCESS', NOW() - INTERVAL '12 hours')
      `);
      await pool.query(`SELECT setval('payments_payment_id_seq', (SELECT MAX(payment_id) FROM payments))`);

      // Sample Sponsorship
      await pool.query(`
        INSERT INTO sponsorships (id, sponsor_id, event_id, tier, amount, website, booth_assigned, status, perks, notes, pledged_at) VALUES
        (1, 4, 1, 'Platinum', 50000.00, 'https://novatech.example.com', 'Main Auditorium - VIP Booth P1', 'Active',
         '["Prime Main Stage Banner & Keynote Shoutout", "Premium VIP Booth in Main Auditorium", "10 Complimentary VIP Event Passes", "Top Logo Placement on Portal & Badges"]'::jsonb,
         'Dual power backup & 4K display banner requested', NOW() - INTERVAL '5 days')
      `);
      await pool.query(`SELECT setval('sponsorships_id_seq', (SELECT MAX(id) FROM sponsorships))`);

      // Sample Initial Notifications
      await pool.query(`
        INSERT INTO notifications (user_id, event_id, title, message, notification_type, is_read, created_at) VALUES
        (3, 1, 'Ticket Confirmed', 'Your pass for TechFest 2026 has been issued with QR Code.', 'TICKET_PURCHASE', false, NOW() - INTERVAL '1 day'),
        (2, 1, 'New Sponsorship Received', 'NovaTech Global Solutions pledged ₹50,000 for Platinum sponsorship.', 'SPONSORSHIP', false, NOW() - INTERVAL '5 days'),
        (2, 1, 'Upcoming Event Reminder', 'TechFest 2026 is scheduled for 2026-10-15. Check venue preparation.', 'REMINDER', false, NOW() - INTERVAL '2 hours')
      `);

      // Sample Historical Crowd Data for Predictive Modeling
      const now = Date.now();
      for (let offset = 4; offset >= 0; offset--) {
        const time = new Date(now - offset * 15 * 60 * 1000);
        // Stage Front Zone increasing trend
        const occStage = 400 + (4 - offset) * 30;
        await pool.query(`
          INSERT INTO crowd_data (event_id, zone_id, capacity, current_occupancy, occupancy_percentage, check_in_count, check_out_count, risk_level, timestamp)
          VALUES (2, 4, 800, $1, $2, $3, $4, $5, $6)
        `, [occStage, (occStage / 800) * 100, (4 - offset) * 35, (4 - offset) * 5, occStage >= 760 ? 'CRITICAL' : occStage >= 640 ? 'HIGH' : occStage >= 480 ? 'MODERATE' : 'NORMAL', time]);
      }
    }

    // Ensure past event 3 exists in PostgreSQL for feedback and historical reporting
    const ev3Check = await pool.query('SELECT id FROM events WHERE id = 3');
    if (ev3Check.rows.length === 0) {
      await pool.query(
        `INSERT INTO events (id, organizer_id, name, type, venue, date, capacity, available_seats, expected_attendance, budget, status, admin_feedback, schedule)
         VALUES (3, 2, 'National Tech Symposium 2025', 'Conference', 'APJ Abdul Kalam Auditorium', '2025-11-15', 500, 120, 400, 250000, 'PUBLISHED', 'Completed Successfully', '[]'::jsonb)
         ON CONFLICT (id) DO NOTHING`
      );
      await pool.query(
        `INSERT INTO ticket_types (event_id, name, price, total_seats, available_seats)
         VALUES (3, 'General Admission', 199.00, 500, 120)
         ON CONFLICT DO NOTHING`
      );
      const tPast = await pool.query('SELECT id FROM tickets WHERE user_id = 3 AND event_id = 3');
      if (tPast.rows.length === 0) {
        const insT = await pool.query(
          `INSERT INTO tickets (user_id, event_id, tier_name, tier_price, amount_paid, qr_code, checked_in, check_in_time, checked_in_by_id, status, booked_at)
           VALUES (3, 3, 'General Admission', 199.00, 234.82, 'EVENTRA-QR-0007-0003', true, '2025-11-15T10:15:00.000Z', 5, 'ACTIVE', '2025-11-05T09:00:00.000Z')
           RETURNING id`
        );
        const pastTId = insT.rows[0].id;
        await pool.query(
          `INSERT INTO checkins (ticket_id, event_id, staff_id, method, checked_in_at)
           VALUES ($1, 3, 5, 'QR_SCAN', '2025-11-15T10:15:00.000Z')
           ON CONFLICT DO NOTHING`,
          [pastTId]
        );
      }
      await pool.query(`SELECT setval('events_id_seq', (SELECT MAX(id) FROM events))`);
      await pool.query(`SELECT setval('tickets_id_seq', (SELECT MAX(id) FROM tickets))`);
    }
  } else {
    // Fallback store initial seeding
    loadFallbackStore();
    if (fallbackStore.users.length === 0) {
      fallbackStore.users = defaultUsers;
    }
    if (fallbackStore.events.length === 0) {
      fallbackStore.events = [
        {
          id: 1,
          organizer_id: 2,
          name: "TechFest 2026",
          type: "Tech Fest",
          venue: "IIITK Campus Arena",
          date: "2026-10-15",
          capacity: 1200,
          available_seats: 1148,
          expected_attendance: 1000,
          budget: 550000,
          status: "PUBLISHED",
          admin_feedback: "Approved by Central Administration",
          schedule: [
            { id: 1, title: "Hackathon 24-Hour Kickoff", time: "09:00 AM - 11:00 AM", location: "Lab Complex" },
            { id: 2, title: "AI & Robotics Keynote Talk", time: "02:00 PM - 04:00 PM", location: "Main Auditorium" }
          ],
          created_at: new Date().toISOString()
        },
        {
          id: 2,
          organizer_id: 2,
          name: "Campus Cultural Night",
          type: "Cultural Fest",
          venue: "Open Air Amphitheatre",
          date: "2026-11-20",
          capacity: 1500,
          available_seats: 1499,
          expected_attendance: 1400,
          budget: 400000,
          status: "PUBLISHED",
          admin_feedback: "Approved",
          schedule: [
            { id: 1, title: "Battle of the Bands", time: "05:00 PM - 07:30 PM", location: "Main Stage" },
            { id: 2, title: "Celebrity DJ Night", time: "08:00 PM - 10:30 PM", location: "Main Stage" }
          ],
          created_at: new Date().toISOString()
        }
      ];

      fallbackStore.ticket_types = [
        { id: 1, event_id: 1, name: "VIP", price: 999.00, total_seats: 50, available_seats: 45 },
        { id: 2, event_id: 1, name: "General", price: 299.00, total_seats: 900, available_seats: 853 },
        { id: 3, event_id: 1, name: "Student", price: 0.00, total_seats: 250, available_seats: 250 },
        { id: 4, event_id: 2, name: "VIP Pass", price: 499.00, total_seats: 200, available_seats: 200 },
        { id: 5, event_id: 2, name: "General Entry", price: 199.00, total_seats: 1000, available_seats: 999 },
        { id: 6, event_id: 2, name: "Student Pass", price: 99.00, total_seats: 300, available_seats: 300 }
      ];

      fallbackStore.venue_zones = [
        { id: 1, event_id: 1, name: "Main Auditorium", capacity: 600, current_occupancy: 140 },
        { id: 2, event_id: 1, name: "Innovation Exhibition Hall", capacity: 400, current_occupancy: 85 },
        { id: 3, event_id: 1, name: "Gate Alpha Security Entry", capacity: 200, current_occupancy: 30 },
        { id: 4, event_id: 2, name: "Stage Front Standing Zone", capacity: 800, current_occupancy: 520 },
        { id: 5, event_id: 2, name: "Food Court & Stalls", capacity: 450, current_occupancy: 390 },
        { id: 6, event_id: 2, name: "Main Entry Gate", capacity: 250, current_occupancy: 195 }
      ];

      fallbackStore.tickets = [
        {
          id: 1,
          user_id: 3,
          event_id: 1,
          ticket_type_id: 2,
          tier_name: "General",
          tier_price: 299.00,
          amount_paid: 352.82,
          qr_code: "EVENTRA-QR-0001-0001",
          checked_in: false,
          check_in_time: null,
          checked_in_by_id: null,
          status: "ACTIVE",
          booked_at: new Date(Date.now() - 86400000).toISOString()
        },
        {
          id: 2,
          user_id: 3,
          event_id: 2,
          ticket_type_id: 5,
          tier_name: "General Entry",
          tier_price: 199.00,
          amount_paid: 234.82,
          qr_code: "EVENTRA-QR-0002-0002",
          checked_in: false,
          check_in_time: null,
          checked_in_by_id: null,
          status: "ACTIVE",
          booked_at: new Date(Date.now() - 43200000).toISOString()
        }
      ];

      fallbackStore.payments = [
        {
          payment_id: 1,
          user_id: 3,
          event_id: 1,
          ticket_id: 1,
          amount: 352.82,
          base_amount: 299.00,
          gst_amount: 53.82,
          currency: "INR",
          razorpay_order_id: "order_demo_1001",
          razorpay_payment_id: "pay_demo_1001",
          payment_method: "Razorpay-Test",
          payment_status: "SUCCESS",
          payment_date: new Date(Date.now() - 86400000).toISOString()
        },
        {
          payment_id: 2,
          user_id: 3,
          event_id: 2,
          ticket_id: 2,
          amount: 234.82,
          base_amount: 199.00,
          gst_amount: 35.82,
          currency: "INR",
          razorpay_order_id: "order_demo_1002",
          razorpay_payment_id: "pay_demo_1002",
          payment_method: "Razorpay-Test",
          payment_status: "SUCCESS",
          payment_date: new Date(Date.now() - 43200000).toISOString()
        }
      ];

      fallbackStore.sponsorships = [
        {
          id: 1,
          sponsor_id: 4,
          event_id: 1,
          tier: "Platinum",
          amount: 50000.00,
          website: "https://novatech.example.com",
          booth_assigned: "Main Auditorium - VIP Booth P1",
          status: "Active",
          perks: [
            "Prime Main Stage Banner & Keynote Shoutout",
            "Premium VIP Booth in Main Auditorium",
            "10 Complimentary VIP Event Passes",
            "Top Logo Placement on Portal & Badges"
          ],
          notes: "Dual power backup & 4K display banner requested",
          pledged_at: new Date(Date.now() - 5 * 86400000).toISOString()
        }
      ];

      fallbackStore.notifications = [
        {
          notification_id: 1,
          user_id: 3,
          event_id: 1,
          title: "Ticket Confirmed",
          message: "Your pass for TechFest 2026 has been issued with QR Code.",
          notification_type: "TICKET_PURCHASE",
          is_read: false,
          created_at: new Date(Date.now() - 86400000).toISOString()
        },
        {
          notification_id: 2,
          user_id: 2,
          event_id: 1,
          title: "New Sponsorship Received",
          message: "NovaTech Global Solutions pledged ₹50,000 for Platinum sponsorship.",
          notification_type: "SPONSORSHIP",
          is_read: false,
          created_at: new Date(Date.now() - 5 * 86400000).toISOString()
        },
        {
          notification_id: 3,
          user_id: 2,
          event_id: 1,
          title: "Upcoming Event Reminder",
          message: "TechFest 2026 is scheduled for 2026-10-15. Check venue preparation.",
          notification_type: "REMINDER",
          is_read: false,
          created_at: new Date(Date.now() - 7200000).toISOString()
        }
      ];

      // Sample crowd data
      const now = Date.now();
      for (let offset = 4; offset >= 0; offset--) {
        const time = new Date(now - offset * 15 * 60 * 1000).toISOString();
        const occStage = 400 + (4 - offset) * 30;
        fallbackStore.crowd_data.push({
          id: fallbackStore.crowd_data.length + 1,
          event_id: 2,
          zone_id: 4,
          capacity: 800,
          current_occupancy: occStage,
          occupancy_percentage: Number(((occStage / 800) * 100).toFixed(2)),
          check_in_count: (4 - offset) * 35,
          check_out_count: (4 - offset) * 5,
          risk_level: occStage >= 760 ? 'CRITICAL' : occStage >= 640 ? 'HIGH' : occStage >= 480 ? 'MODERATE' : 'NORMAL',
          timestamp: time
        });
      }

      saveFallbackStore();
    }

    // Seed initial event feedback and past attended event if not present
    let pastEvent = fallbackStore.events.find(e => e.date < new Date().toISOString().split('T')[0]);
    if (!pastEvent) {
      const pastId = fallbackStore.events.length ? Math.max(...fallbackStore.events.map(e => e.id)) + 1 : 101;
      pastEvent = {
        id: pastId,
        organizer_id: 2,
        name: "National Tech Symposium 2025",
        type: "Conference",
        venue: "APJ Abdul Kalam Auditorium",
        date: "2025-11-15",
        capacity: 500,
        available_seats: 120,
        expected_attendance: 400,
        budget: 250000,
        status: "PUBLISHED",
        admin_feedback: "Completed Successfully",
        schedule: [{ id: 1, title: "Opening Keynote", time: "10:00 AM", location: "Main Hall" }],
        created_at: "2025-11-01T00:00:00.000Z"
      };
      fallbackStore.events.push(pastEvent);
    }

    let pastTicket = fallbackStore.tickets.find(t => (t.user_id === 3 || t.userId === 3) && (t.event_id === pastEvent.id || t.eventId === pastEvent.id) && (t.checked_in || t.checkedIn));
    if (!pastTicket) {
      const tId = fallbackStore.tickets.length ? Math.max(...fallbackStore.tickets.map(t => t.id || t.ticketId || 0)) + 1 : 101;
      pastTicket = {
        id: tId,
        ticketId: tId,
        userId: 3,
        user_id: 3,
        userName: "Banoth Manohar",
        userEmail: "attendee@fest.org",
        eventId: pastEvent.id,
        event_id: pastEvent.id,
        eventName: pastEvent.name,
        ticket_type_id: 1,
        tierName: "General Admission",
        tierPrice: 199.00,
        amountPaid: 234.82,
        qrCode: `EVENTRA-QR-000${pastEvent.id}-0003`,
        qr_code: `EVENTRA-QR-000${pastEvent.id}-0003`,
        checkedIn: true,
        checked_in: true,
        checkInTime: "2025-11-15T10:15:00.000Z",
        check_in_time: "2025-11-15T10:15:00.000Z",
        checked_in_by_id: 5,
        status: "ACTIVE",
        bookedAt: "2025-11-05T09:00:00.000Z",
        booked_at: "2025-11-05T09:00:00.000Z"
      };
      fallbackStore.tickets.push(pastTicket);
      fallbackStore.checkins.push({
        id: fallbackStore.checkins.length + 1,
        ticket_id: pastTicket.id,
        event_id: pastEvent.id,
        zone_id: 1,
        staff_id: 5,
        checked_in_at: "2025-11-15T10:15:00.000Z"
      });
    }

    if (fallbackStore.event_feedback.length === 0) {
      fallbackStore.event_feedback.push({
        id: 1,
        event_id: pastEvent.id,
        user_id: 3,
        rating: 5,
        comment: "Outstanding event! Seamless badge check-in and brilliant keynote speakers.",
        created_at: "2025-11-16T11:00:00.000Z",
        updated_at: "2025-11-16T11:00:00.000Z"
      });
    }
    saveFallbackStore();
  }
}

// Initialize Database Connection and run migrations
async function initDatabase() {
  try {
    pool = new Pool(dbConfig);
    const client = await pool.connect();

    console.log(`[DB] Successfully connected to PostgreSQL at ${dbConfig.host}:${dbConfig.port}/${dbConfig.database}`);

    usePgNative = true;
    dbEngineName = 'PostgreSQL Native';

    // Execute schema migrations
    const schemaSql = fs.readFileSync(path.join(__dirname, 'schema.sql'), 'utf8');
    await client.query(schemaSql);
    client.release();

    console.log('[DB] PostgreSQL schema initialized successfully.');

    await seedDefaultData();
    console.log('[DB] Default seed data verified in PostgreSQL.');

  } catch (err) {
    console.error(`[DB] PostgreSQL connection failed: ${err.message}`);

    if (process.env.NODE_ENV === 'production') {
      console.error('[DB] PostgreSQL is required in production. Fallback database is disabled.');

      usePgNative = false;
      dbEngineName = 'PostgreSQL Unavailable';

      throw new Error('Production database connection failed.');
    }

    console.warn('[DB] Development mode: switching to persistent fallback database.');

    usePgNative = false;
    dbEngineName = 'PostgreSQL-Compatibility Engine (Development Fallback)';

    loadFallbackStore();
    await seedDefaultData();

    console.log('[DB] Development fallback store active at', FALLBACK_STORE_PATH);
  }
}

// Unified query wrapper that executes against native PG or fallback store
async function query(text, params = []) {
  if (usePgNative && pool) {
    return pool.query(text, params);
  }

  // Fallback query emulator for standard SQL operations
  return executeFallbackQuery(text, params);
}

// Helper to query fallback store with basic SQL emulation
function executeFallbackQuery(text, params = []) {
  const sql = text.trim();
  const lower = sql.toLowerCase();

  // Helper getters
  if (lower.startsWith('select count(*) from users')) {
    return { rows: [{ count: fallbackStore.users.length }] };
  }
  if (lower.startsWith('select count(*) from events')) {
    return { rows: [{ count: fallbackStore.events.length }] };
  }

  return { rows: [] };
}

module.exports = {
  initDatabase,
  query,
  getPool: () => pool,
  getEngineName: () => dbEngineName,
  isNative: () => usePgNative,
  getFallbackStore: () => fallbackStore,
  saveFallbackStore,
  hashPassword
};

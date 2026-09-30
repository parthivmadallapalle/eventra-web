-- =============================================================================
-- EVENTRA Event Management System - PostgreSQL Database Schema
-- SRS v1.0 & SADD v1.0 Compliant • Team 23, IIIT Kottayam
-- =============================================================================

-- 1. Users Table (RBAC 5 Roles: 1=Organizer, 2=Attendee, 3=Sponsor, 4=Staff, 5=Admin)
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role_id INT NOT NULL CHECK (role_id BETWEEN 1 AND 5),
    phone VARCHAR(30),
    organization VARCHAR(150),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Events Table (One organizer can create multiple events)
CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY,
    organizer_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    type VARCHAR(100) NOT NULL,
    venue VARCHAR(200) NOT NULL,
    date DATE NOT NULL,
    capacity INT NOT NULL CHECK (capacity > 0),
    available_seats INT NOT NULL CHECK (available_seats >= 0),
    expected_attendance INT NOT NULL DEFAULT 0,
    budget NUMERIC(12,2) NOT NULL DEFAULT 0,
    status VARCHAR(50) NOT NULL DEFAULT 'DRAFT',
    admin_feedback TEXT,
    schedule JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Ticket Types Table (One event can have multiple ticket types)
CREATE TABLE IF NOT EXISTS ticket_types (
    id SERIAL PRIMARY KEY,
    event_id INT NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    price NUMERIC(10,2) NOT NULL DEFAULT 0 CHECK (price >= 0),
    total_seats INT NOT NULL CHECK (total_seats > 0),
    available_seats INT NOT NULL CHECK (available_seats >= 0),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4. Tickets Table (One attendee can purchase multiple tickets; each belongs to event & ticket type)
CREATE TABLE IF NOT EXISTS tickets (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    event_id INT NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    ticket_type_id INT REFERENCES ticket_types(id) ON DELETE SET NULL,
    tier_name VARCHAR(100),
    tier_price NUMERIC(10,2) DEFAULT 0,
    amount_paid NUMERIC(10,2) DEFAULT 0,
    qr_code VARCHAR(100) UNIQUE NOT NULL,
    checked_in BOOLEAN DEFAULT FALSE,
    check_in_time TIMESTAMP WITH TIME ZONE,
    checked_in_by_id INT REFERENCES users(id) ON DELETE SET NULL,
    status VARCHAR(30) DEFAULT 'ACTIVE',
    cancelled_at TIMESTAMP WITH TIME ZONE,
    booked_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 5. Payments Table (Each paid ticket can have a payment record, with Razorpay integration)
CREATE TABLE IF NOT EXISTS payments (
    payment_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    event_id INT NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    ticket_id INT REFERENCES tickets(id) ON DELETE SET NULL,
    amount NUMERIC(10,2) NOT NULL,
    base_amount NUMERIC(10,2) DEFAULT 0,
    gst_amount NUMERIC(10,2) DEFAULT 0,
    currency VARCHAR(10) DEFAULT 'INR',
    razorpay_order_id VARCHAR(100),
    razorpay_payment_id VARCHAR(100),
    razorpay_signature VARCHAR(255),
    payment_method VARCHAR(50) DEFAULT 'Razorpay-Test',
    payment_status VARCHAR(30) NOT NULL DEFAULT 'CREATED', -- 'CREATED', 'PENDING', 'SUCCESS', 'FAILED'
    payment_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 6. Venue Zones Table (One event can have multiple venue zones)
CREATE TABLE IF NOT EXISTS venue_zones (
    id SERIAL PRIMARY KEY,
    event_id INT NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    name VARCHAR(150) NOT NULL,
    capacity INT NOT NULL CHECK (capacity > 0),
    current_occupancy INT NOT NULL DEFAULT 0 CHECK (current_occupancy >= 0),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 7. Checkins Table (Staff members perform check-ins)
CREATE TABLE IF NOT EXISTS checkins (
    id SERIAL PRIMARY KEY,
    ticket_id INT NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
    event_id INT NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    zone_id INT REFERENCES venue_zones(id) ON DELETE SET NULL,
    staff_id INT REFERENCES users(id) ON DELETE SET NULL,
    method VARCHAR(50) DEFAULT 'QR_SCAN',
    checked_in_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 8. Sponsors Table (Sponsor organization profile)
CREATE TABLE IF NOT EXISTS sponsors (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    company_name VARCHAR(200) NOT NULL,
    website VARCHAR(255),
    contact_person VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 9. Sponsorships Table (Events can have multiple sponsors and sponsorship records)
CREATE TABLE IF NOT EXISTS sponsorships (
    id SERIAL PRIMARY KEY,
    sponsor_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    event_id INT NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    tier VARCHAR(50) NOT NULL, -- 'Platinum', 'Gold', 'Silver'
    amount NUMERIC(10,2) NOT NULL,
    website VARCHAR(255),
    booth_assigned VARCHAR(150),
    status VARCHAR(50) DEFAULT 'Active',
    perks JSONB DEFAULT '[]'::jsonb,
    notes TEXT,
    pledged_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 10. Notifications Table (In-app notifications and reminders)
CREATE TABLE IF NOT EXISTS notifications (
    notification_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    event_id INT REFERENCES events(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    notification_type VARCHAR(50) NOT NULL, -- TICKET_PURCHASE, PAYMENT_SUCCESS, PAYMENT_FAILURE, CHECK_IN, CROWD_ALERT, SPONSORSHIP, REMINDER, SYSTEM
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 11. Crowd Data Table (Historical and periodic crowd occupancy for predictive modeling)
CREATE TABLE IF NOT EXISTS crowd_data (
    id SERIAL PRIMARY KEY,
    event_id INT NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    zone_id INT NOT NULL REFERENCES venue_zones(id) ON DELETE CASCADE,
    capacity INT NOT NULL,
    current_occupancy INT NOT NULL,
    occupancy_percentage NUMERIC(5,2),
    check_in_count INT DEFAULT 0,
    check_out_count INT DEFAULT 0,
    risk_level VARCHAR(20) NOT NULL, -- 'NORMAL', 'MODERATE', 'HIGH', 'CRITICAL'
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Performance & Foreign Key Indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_events_organizer ON events(organizer_id);
CREATE INDEX IF NOT EXISTS idx_events_status ON events(status);
CREATE INDEX IF NOT EXISTS idx_tickets_user ON tickets(user_id);
CREATE INDEX IF NOT EXISTS idx_tickets_event ON tickets(event_id);
CREATE INDEX IF NOT EXISTS idx_tickets_qr ON tickets(qr_code);
CREATE INDEX IF NOT EXISTS idx_payments_user ON payments(user_id);
CREATE INDEX IF NOT EXISTS idx_payments_event ON payments(event_id);
CREATE INDEX IF NOT EXISTS idx_payments_order ON payments(razorpay_order_id);
CREATE INDEX IF NOT EXISTS idx_venue_zones_event ON venue_zones(event_id);
CREATE INDEX IF NOT EXISTS idx_checkins_ticket ON checkins(ticket_id);
CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id, is_read);
CREATE INDEX IF NOT EXISTS idx_crowd_data_event_zone ON crowd_data(event_id, zone_id, timestamp);

-- 12. Password Resets Table (Email OTP Verification for Secure Password Reset)
CREATE TABLE IF NOT EXISTS password_resets (
    id SERIAL PRIMARY KEY,
    email VARCHAR(150) NOT NULL,
    otp_hash VARCHAR(255) NOT NULL,
    reset_token VARCHAR(255),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    attempts INT DEFAULT 0,
    used BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_password_resets_email ON password_resets(email);
CREATE INDEX IF NOT EXISTS idx_password_resets_token ON password_resets(reset_token);

-- 13. Event Feedback Table (Attendee Ratings & Reviews for Completed Events)
CREATE TABLE IF NOT EXISTS event_feedback (
    id SERIAL PRIMARY KEY,
    event_id INT NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    rating INT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    comment TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_event_user_feedback UNIQUE (event_id, user_id)
);
CREATE INDEX IF NOT EXISTS idx_feedback_event ON event_feedback(event_id);
CREATE INDEX IF NOT EXISTS idx_feedback_user ON event_feedback(user_id);

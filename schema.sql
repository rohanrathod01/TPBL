-- HelpConnect Database Schema (SQLite) - Version 3
-- This script creates the four core tables: profiles, availabilities, jobs, and reviews.

-- --------------------------------------------------------
-- Table 1: profiles (Stores both Clients and Helpers)
-- --------------------------------------------------------
DROP TABLE IF EXISTS profiles;
CREATE TABLE profiles (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL, 
    role TEXT NOT NULL, -- 'client' or 'helper'
    full_name TEXT NOT NULL,
    phone TEXT,
    city TEXT NOT NULL,
    state TEXT,
    description TEXT,
    skills TEXT, -- Comma-separated list of skills
    hourly_rate REAL,
    rating REAL DEFAULT 0.0,
    reviews_count INTEGER DEFAULT 0,
    member_since INTEGER,
    avatar_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- --------------------------------------------------------
-- Table 2: availabilities (Stores a Helper's weekly schedule)
-- --------------------------------------------------------
DROP TABLE IF EXISTS availabilities;
CREATE TABLE availabilities (
    id TEXT PRIMARY KEY,
    helper_id TEXT NOT NULL,
    days TEXT NOT NULL, -- Comma-separated days (e.g., "Mon,Tue,Wed")
    start_time TEXT NOT NULL, -- Format: HH:MM
    end_time TEXT NOT NULL,   -- Format: HH:MM
    note TEXT,
    FOREIGN KEY (helper_id) REFERENCES profiles(id)
);

-- --------------------------------------------------------
-- Table 3: jobs (Stores service bookings/requests)
-- --------------------------------------------------------
DROP TABLE IF EXISTS jobs;
CREATE TABLE jobs (
    id TEXT PRIMARY KEY,
    client_id TEXT NOT NULL,
    helper_id TEXT, -- Nullable until accepted by a helper
    scheduled_date TEXT NOT NULL, -- Date of service
    scheduled_start TEXT NOT NULL,
    scheduled_end TEXT NOT NULL,
    agreed_hourly_rate REAL,
    total_amount REAL,
    status TEXT NOT NULL, -- e.g., 'requested', 'accepted', 'completed', 'cancelled'
    details TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES profiles(id),
    FOREIGN KEY (helper_id) REFERENCES profiles(id)
);

-- --------------------------------------------------------
-- Table 4: reviews (Stores ratings and comments)
-- --------------------------------------------------------
DROP TABLE IF EXISTS reviews;
CREATE TABLE reviews (
    id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL,
    reviewer_id TEXT NOT NULL,
    reviewee_id TEXT NOT NULL, -- The profile being reviewed (usually the helper)
    rating INTEGER NOT NULL, -- 1 to 5 stars
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (job_id) REFERENCES jobs(id),
    FOREIGN KEY (reviewer_id) REFERENCES profiles(id),
    FOREIGN KEY (reviewee_id) REFERENCES profiles(id)
);


-- --------------------------------------------------------
-- Sample Data Insertion (Passwords are 'password' for testing)
-- --------------------------------------------------------

INSERT INTO profiles (id, email, password_hash, role, full_name, city, state, description, skills, hourly_rate, rating, reviews_count, member_since) VALUES
('h1', 'priya@example.com', 'mock_hash', 'helper', 'Priya Sharma', 'Mumbai', 'Maharashtra', 'Experienced in household management with 5+ years of service.', 'Cleaning,Cooking,Childcare', 200.00, 4.8, 24, 2020),
('h2', 'seema@example.com', 'mock_hash', 'helper', 'Seema Patel', 'Mumbai', 'Maharashtra', 'Specialized in traditional and modern cooking.', 'Cooking,Cleaning', 250.00, 4.9, 31, 2019),
('h3', 'anita@example.com', 'mock_hash', 'helper', 'Anita Das', 'Pune', 'Maharashtra', 'Good with baby care and cleaning.', 'Baby Care,Cleaning', 200.00, 4.7, 18, 2021),
('c1', 'client1@example.com', 'mock_hash', 'client', 'Swati Verma', 'Mumbai', 'Maharashtra', 'Software Engineer looking for reliable help.', NULL, NULL, NULL, NULL, 2023),
('c2', 'client2@example.com', 'mock_hash', 'client', 'Rohan Mehra', 'Pune', 'Maharashtra', 'Need help with house cleaning every weekend.', NULL, NULL, NULL, NULL, 2024);

INSERT INTO availabilities (id, helper_id, days, start_time, end_time, note) VALUES
('a1', 'h1', 'Mon,Tue,Wed,Fri', '09:00', '17:00', 'Available standard days'),
('a2', 'h2', 'Mon,Tue,Wed,Thu,Fri', '10:00', '14:00', 'Part-time only');

INSERT INTO jobs (id, client_id, helper_id, scheduled_date, scheduled_start, scheduled_end, agreed_hourly_rate, total_amount, status, details) VALUES
('j1', 'c1', 'h1', '2025-10-28', '09:00', '12:00', 200.00, 600.00, 'completed', 'Standard house cleaning and kitchen maintenance.');

INSERT INTO reviews (id, job_id, reviewer_id, reviewee_id, rating, comment) VALUES
('r1', 'j1', 'c1', 'h1', 5, 'Very polite and hardworking helper! Highly recommended.');

-- --------------------------------------------------------
-- Indexes (for performance)
-- --------------------------------------------------------
CREATE INDEX idx_profiles_city ON profiles (city);
CREATE INDEX idx_profiles_role ON profiles (role);
CREATE INDEX idx_profiles_email ON profiles (email);
CREATE INDEX idx_jobs_status ON jobs (status);

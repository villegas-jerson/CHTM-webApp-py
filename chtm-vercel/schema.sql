-- CHTM Admin Panel — Postgres schema (for Neon, Supabase, or any Postgres host)
-- Run this once against your database, e.g.:
--   psql "your-connection-string" -f schema.sql

CREATE TABLE IF NOT EXISTS admin_users (
  id SERIAL PRIMARY KEY,
  username VARCHAR(50) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS announcements (
  id SERIAL PRIMARY KEY,
  title VARCHAR(255) NOT NULL,
  body TEXT NOT NULL,
  image_url VARCHAR(500),
  sort_order INT NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS events (
  id SERIAL PRIMARY KEY,
  title VARCHAR(255) NOT NULL,
  subtitle TEXT,
  sort_order INT NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS event_images (
  id SERIAL PRIMARY KEY,
  event_id INT NOT NULL REFERENCES events(id) ON DELETE CASCADE,
  image_url VARCHAR(500) NOT NULL,
  sort_order INT NOT NULL DEFAULT 0
);

-- Seed one admin account: username "admin", password "chtm2026"
-- (hash generated with werkzeug's generate_password_hash; change the password after first login)
INSERT INTO admin_users (username, password_hash)
VALUES ('admin', 'scrypt:32768:8:1$7M7R3Wjhvn8P0xgM$faea338c411ddc5dc7f2baddc0629ecba291f3dbb494d87ac11a7f42266131d145c1a151024d8b46237104770149e651f9de6718e5d5aad19dd9ee824d1dc208')
ON CONFLICT (username) DO NOTHING;

-- Seed the two existing announcement cards so the page isn't empty on first load
INSERT INTO announcements (title, body, image_url, sort_order)
SELECT 'NAMEPLATE AVAILABILITY',
 '<p>Good day, Junior Hoteliers!</p><p>The Society of Junior Hoteliers (SJH) would like to inform everyone that nameplates are now available for ordering at the SJH Office.</p><p>Students who need their official nameplates are encouraged to visit the SJH Office during office hours to place their orders. This is open to all eligible Hospitality Management students who have not yet secured their nameplates or wish to request an update or replacement.</p><p>Please ensure that all necessary details are correct upon ordering to avoid errors or delays. Orders will be processed accordingly, and further instructions regarding release will be provided upon confirmation.</p><p>For additional inquiries, kindly approach any SJH officer or contact us through our official communication channels.</p><p>Thank you for your cooperation and please be guided accordingly.</p>',
 NULL, 1
WHERE NOT EXISTS (SELECT 1 FROM announcements WHERE title = 'NAMEPLATE AVAILABILITY');

INSERT INTO announcements (title, body, image_url, sort_order)
SELECT 'SUBMISSION OF GRADUATION DOCUMENT REQUIREMENTS',
 '<p>Good day!</p><p>The Office of the Registrar would like to remind all <strong>2nd Semester Graduating Students for SY 2025-2026</strong> to submit the required graduation documents in preparation for enrollment for School Year 2025-2026. These documents will be used to determine the subjects you need to take to qualify for graduation.</p><p>The required documents are as follows:</p><p>1. Evaluated Prospectus (accessible through your student portal)<br>2. PSA / Birth Certificate (BC)<br>3. SF10 / Transcript of Records (TOR)<br>4. Form 138 / Original Report Card</p><p><strong>Deadline of Submission: December 12, 2025</strong></p><p>Please be reminded that failure to submit the above-mentioned documents will result in the removal of your name from the roster of graduating students.</p><p>Kindly refer to the attached list for any lacking requirements.</p><p>Thank you for your cooperation and please be guided accordingly.</p>',
 NULL, 2
WHERE NOT EXISTS (SELECT 1 FROM announcements WHERE title = 'SUBMISSION OF GRADUATION DOCUMENT REQUIREMENTS');

-- Seed the two existing event hero blocks
INSERT INTO events (title, subtitle, sort_order)
SELECT 'UC CARES Outreach Program', 'Service-learning, community engagement, and hands-on hospitality experiences beyond the campus.', 1
WHERE NOT EXISTS (SELECT 1 FROM events WHERE title = 'UC CARES Outreach Program');

INSERT INTO events (title, subtitle, sort_order)
SELECT 'Hospitality & Tourism Congress', 'Industry partners, student leaders, and faculty coming together to celebrate innovation and excellence.', 2
WHERE NOT EXISTS (SELECT 1 FROM events WHERE title = 'Hospitality & Tourism Congress');

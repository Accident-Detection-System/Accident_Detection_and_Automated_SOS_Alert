USE accident_detection;

-- Run this once. Adds the "hospital accepts the alert" + live-tracking support.

ALTER TABLE alerts
  ADD COLUMN status ENUM('pending','accepted','resolved') NOT NULL DEFAULT 'pending',
  ADD COLUMN user_id INT NULL,
  ADD COLUMN accepted_by_hospital_id INT NULL,
  ADD COLUMN accepted_at TIMESTAMP NULL,
  ADD COLUMN notified_hospital_ids VARCHAR(255) NULL;

ALTER TABLE alerts
  ADD CONSTRAINT fk_alerts_user FOREIGN KEY (user_id) REFERENCES users(id),
  ADD CONSTRAINT fk_alerts_accepted_hospital FOREIGN KEY (accepted_by_hospital_id) REFERENCES hospitals(id);

-- Backfill: anything already marked accident_detected before this migration is
-- left as 'pending' by default above, which is correct — nobody has accepted them yet.

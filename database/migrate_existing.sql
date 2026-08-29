-- Use this only when upgrading an existing database created from the original project.
USE accident_detection;

ALTER TABLE hospitals ADD COLUMN latitude DECIMAL(10,8) NULL;
ALTER TABLE hospitals ADD COLUMN longitude DECIMAL(11,8) NULL;
ALTER TABLE alerts ADD COLUMN accident_clip_path VARCHAR(500) NULL;
ALTER TABLE alerts ADD COLUMN severity_label VARCHAR(20) NULL;
ALTER TABLE alerts ADD COLUMN severity_score INT NULL;

-- If a statement says the column already exists, skip that statement and continue.
-- Then add real hospital coordinates, for example:
-- UPDATE hospitals SET latitude=17.3850, longitude=78.4867 WHERE id=1;

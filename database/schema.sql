CREATE DATABASE IF NOT EXISTS accident_detection CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE accident_detection;

CREATE TABLE IF NOT EXISTS hospitals (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  email VARCHAR(255) UNIQUE NOT NULL,
  password VARCHAR(255) NOT NULL,
  location VARCHAR(255),
  phone VARCHAR(20),
  latitude DECIMAL(10,8) NULL,
  longitude DECIMAL(11,8) NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  email VARCHAR(255) UNIQUE NOT NULL,
  password VARCHAR(255) NOT NULL,
  phone VARCHAR(20),
  latitude DECIMAL(10,8) NULL,
  longitude DECIMAL(11,8) NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS cameras (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  location VARCHAR(255),
  status ENUM('pending','accepted','rejected') DEFAULT 'pending',
  hospital_id INT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (hospital_id) REFERENCES hospitals(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS alerts (
  id INT AUTO_INCREMENT PRIMARY KEY,
  camera_id INT,
  hospital_id INT,
  video_name VARCHAR(255),
  accident_detected BOOLEAN DEFAULT FALSE,
  screenshot_path VARCHAR(500),
  accident_clip_path VARCHAR(500) NULL,
  location TEXT,
  email_sent BOOLEAN DEFAULT FALSE,
  severity_label VARCHAR(20) NULL,
  severity_score INT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (camera_id) REFERENCES cameras(id) ON DELETE SET NULL,
  FOREIGN KEY (hospital_id) REFERENCES hospitals(id) ON DELETE SET NULL,
  INDEX idx_alert_hospital_created (hospital_id, created_at),
  INDEX idx_alert_accident (accident_detected)
);

CREATE DATABASE IF NOT EXISTS ai_ranger
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE ai_ranger;

CREATE TABLE IF NOT EXISTS admin_users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(150) NOT NULL,
    email VARCHAR(200) NOT NULL,
    role VARCHAR(100) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS detection_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    original_filename VARCHAR(255) NOT NULL,
    saved_filename VARCHAR(255) NOT NULL,
    original_image_url VARCHAR(255) NOT NULL,
    image_url VARCHAR(255) NOT NULL,
    detection_type VARCHAR(100) NOT NULL,
    confidence FLOAT NOT NULL,
    severity VARCHAR(32) NOT NULL,
    detection_count INT NOT NULL DEFAULT 0,
    detections_json LONGTEXT NOT NULL,
    location VARCHAR(150) NOT NULL,
    timestamp DATETIME NOT NULL,
    source_type VARCHAR(32) NOT NULL,
    source_frame_index INT NULL,
    source_timestamp_seconds FLOAT NULL,
    processed_frames INT NULL,
    notification_status VARCHAR(64) NULL,
    notification_message TEXT NULL
);

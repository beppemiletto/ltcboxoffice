-- Database Setup Script for LTC Box Office
-- Run this script as MySQL root user

-- Create database
CREATE DATABASE IF NOT EXISTS ltcboxoffice CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Create user (if not exists)
CREATE USER IF NOT EXISTS 'djangodbuser'@'localhost' IDENTIFIED BY 'aSdF!234';

-- Grant privileges
GRANT ALL PRIVILEGES ON ltcboxoffice.* TO 'djangodbuser'@'localhost';

-- Apply changes
FLUSH PRIVILEGES;

-- Show created database
SHOW DATABASES LIKE 'ltcboxoffice';

-- Show user grants
SHOW GRANTS FOR 'djangodbuser'@'localhost';

-- Paste in phpMyAdmin SQL tab (or: sudo mysql < scripts/create_local_db.sql)
-- Local app user only. Change the password if this box is shared.

CREATE DATABASE IF NOT EXISTS mess_db
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS mess_db_test
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'mess'@'127.0.0.1' IDENTIFIED BY 'mess_dev';
CREATE USER IF NOT EXISTS 'mess'@'localhost' IDENTIFIED BY 'mess_dev';
ALTER USER 'mess'@'127.0.0.1' IDENTIFIED BY 'mess_dev';
ALTER USER 'mess'@'localhost' IDENTIFIED BY 'mess_dev';

GRANT ALL PRIVILEGES ON mess_db.* TO 'mess'@'127.0.0.1';
GRANT ALL PRIVILEGES ON mess_db.* TO 'mess'@'localhost';
GRANT ALL PRIVILEGES ON mess_db_test.* TO 'mess'@'127.0.0.1';
GRANT ALL PRIVILEGES ON mess_db_test.* TO 'mess'@'localhost';

FLUSH PRIVILEGES;

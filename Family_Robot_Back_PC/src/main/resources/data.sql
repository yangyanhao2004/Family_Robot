-- Clear old seed data (idempotent, FK-safe order)
DELETE FROM command_logs WHERE user_id = 1;
DELETE FROM photos WHERE id IN (1, 2, 3, 4);
DELETE FROM user_settings WHERE user_id = 1;
DELETE FROM robots WHERE id = 1;
DELETE FROM users WHERE id = 1;

-- Seed admin user (password: admin123, BCrypt hashed)
INSERT INTO users (id, email, password_hash, name, role, created_at)
VALUES (1, 'admin@family-robot.local',
        '$2a$10$OdJbJO9yiJGsz.ThK/SKa.hShyMXgyHtPC.wLLbA61O5y9gFBo.o.',
        'Admin', 'Admin', NOW());

-- Seed default settings for admin
INSERT INTO user_settings (user_id, auto_save, firmware_version, serial_number)
VALUES (1, true, 'v2.4.1 (latest)', 'RBT-98234-XYZ');

-- Seed sample photos
INSERT INTO photos (id, url, filename, date, user_id, created_at)
VALUES (1, 'https://images.unsplash.com/photo-1485827404703-89b55fcc595e?w=400', 'robot_view_01.jpg', '2026-05-10', 1, NOW()),
       (2, 'https://images.unsplash.com/photo-1527430253228-e93688616381?w=400', 'robot_view_02.jpg', '2026-05-09', 1, NOW()),
       (3, 'https://images.unsplash.com/photo-1558618666-fcd25c85f82e?w=400', 'robot_view_03.jpg', '2026-05-08', 1, NOW()),
       (4, 'https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?w=400', 'robot_view_04.jpg', '2026-05-07', 1, NOW());

-- Seed sample robot (unassigned)
INSERT INTO robots (id, serial_number, user_id, created_at)
VALUES (1, 'RBT-98234-XYZ', NULL, NOW());

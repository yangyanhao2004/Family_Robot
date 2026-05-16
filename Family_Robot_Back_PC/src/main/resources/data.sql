-- Clear old seed data (idempotent, FK-safe order)
DELETE FROM verification_codes WHERE email = 'admin@family-robot.local';
DELETE FROM command_logs WHERE user_id = 1;
DELETE FROM photos WHERE id IN (1, 2, 3, 4);
DELETE FROM user_settings WHERE user_id = 1;
DELETE FROM robots WHERE id = 1;
DELETE FROM users WHERE id = 1;

-- Seed sample robot (unassigned)
INSERT INTO robots (id, serial_number, user_id, created_at)
VALUES (1, 'RBT-98234-XYZ', NULL, NOW());

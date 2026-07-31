INSERT INTO registered_clients (client_id, client_name, redirect_uri, status) VALUES
('client_001', 'Auth Portal Main', 'https://auth.example.com/callback', 'ACTIVE'),
('client_002', 'Payment Service', 'https://pay.example.com/oauth', 'ACTIVE'),
('client_003', 'Phishing Risk Client', 'https://auth-phish.com/oauth/callback', 'ACTIVE'),
('client_004', 'Analytics Portal', 'https://analytics.example.org/login', 'ACTIVE'),
('client_005', 'Trusted Proxy Gateway', 'https://auth-phish.com.trusted-proxy.net/oauth/callback', 'ACTIVE'),
('client_006', 'Audit Logging Portal', 'https://audit.example.net/callback', 'ACTIVE'),
('client_007', 'Anti-Phishing Security Center', 'https://anti-phishing-defense.org/oauth/callback', 'ACTIVE'),
('client_008', 'Enterprise Portal', 'https://enterprise.example.com/oauth', 'ACTIVE'),
('client_009', 'Phish Guard Proxy', 'https://auth-phish.com.security-gateway.com/callback', 'ACTIVE');

INSERT INTO signing_keys (key_id, client_id, key_type, key_value, status, released_at) VALUES
('key_001', 'client_001', 'RSA-2048', 'pubkey_001_valid_base64', 'ACTIVE', '2026-01-15 00:00:00'),
('key_002', 'client_002', 'RSA-2048', 'pubkey_002_revoked_base64', 'REVOKED', '2026-02-01 00:00:00'),
('key_003', 'client_003', 'RSA-2048', 'pubkey_003_phishing_base64', 'ACTIVE', '2026-03-10 00:00:00'),
('key_004', 'client_004', 'RSA-2048', 'pubkey_004_valid_base64', 'ACTIVE', '2026-04-05 00:00:00'),
('key_005', 'client_005', 'RSA-2048', 'pubkey_005_valid_base64', 'ACTIVE', '2026-05-10 00:00:00'),
('key_006', 'client_006', 'RSA-2048', 'pubkey_006_valid_base64', 'ACTIVE', '2026-06-01 00:00:00'),
('key_007', 'client_007', 'RSA-2048', 'pubkey_007_valid_base64', 'ACTIVE', '2026-07-01 00:00:00'),
('key_008', 'client_008', 'RSA-2048', 'pubkey_008_valid_base64', 'ACTIVE', '2026-07-15 00:00:00'),
('key_009', 'client_009', 'RSA-2048', 'pubkey_009_valid_base64', 'ACTIVE', '2026-07-20 00:00:00');

INSERT INTO revoked_keys (key_id, revocation_reason, revoked_at) VALUES
('key_002', 'Compromised signing key released under v1.0.0-key-revoked', '2026-02-01 10:00:00');

-- Codes are stored only as SHA-256 digests. Binding is an atomic SQL update.
CREATE TABLE IF NOT EXISTS activation_codes (
 id TEXT PRIMARY KEY,
 code_hash TEXT NOT NULL UNIQUE CHECK(length(code_hash)=64),
 created_at INTEGER NOT NULL,
 device_id TEXT,
 machine_binding TEXT,
 claimed_at INTEGER,
 disabled INTEGER NOT NULL DEFAULT 0 CHECK(disabled IN (0,1))
);
CREATE UNIQUE INDEX IF NOT EXISTS activation_one_license_per_device ON activation_codes(device_id) WHERE device_id IS NOT NULL;
CREATE TABLE IF NOT EXISTS activation_challenges (
 id TEXT PRIMARY KEY,
 nonce TEXT NOT NULL,
 device_id TEXT NOT NULL,
 public_jwk TEXT NOT NULL,
 machine_binding TEXT NOT NULL,
 operation TEXT NOT NULL CHECK(operation IN ('redeem','recover')),
 code_hash TEXT NOT NULL DEFAULT '',
 expires_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS activation_challenge_expiry ON activation_challenges(expires_at);
CREATE TABLE IF NOT EXISTS activation_limits (
 id TEXT PRIMARY KEY,
 count INTEGER NOT NULL,
 expires_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS activation_limit_expiry ON activation_limits(expires_at);

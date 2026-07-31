DROP TABLE IF EXISTS revoked_keys;
DROP TABLE IF EXISTS signing_keys;
DROP TABLE IF EXISTS registered_clients;

CREATE TABLE registered_clients (
    client_id VARCHAR(50) PRIMARY KEY,
    client_name VARCHAR(100) NOT NULL,
    redirect_uri VARCHAR(255) NOT NULL,
    status VARCHAR(20) NOT NULL
);

CREATE TABLE signing_keys (
    key_id VARCHAR(50) PRIMARY KEY,
    client_id VARCHAR(50) NOT NULL,
    key_type VARCHAR(20) NOT NULL,
    key_value TEXT NOT NULL,
    status VARCHAR(20) NOT NULL,
    released_at TIMESTAMP NOT NULL,
    FOREIGN KEY (client_id) REFERENCES registered_clients(client_id)
);

CREATE TABLE revoked_keys (
    key_id VARCHAR(50) PRIMARY KEY,
    revocation_reason TEXT NOT NULL,
    revoked_at TIMESTAMP NOT NULL,
    FOREIGN KEY (key_id) REFERENCES signing_keys(key_id)
);

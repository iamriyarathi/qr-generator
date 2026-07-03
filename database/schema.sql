-- Professional QR Code Generator — database schema
-- SQLite

CREATE TABLE IF NOT EXISTS history (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    qr_type         TEXT    NOT NULL,
    user_input      TEXT    NOT NULL,
    qr_data         TEXT    NOT NULL,
    file_name       TEXT    NOT NULL,
    customization   TEXT,
    created_date    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    download_count  INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_history_type ON history (qr_type);
CREATE INDEX IF NOT EXISTS idx_history_created ON history (created_date);

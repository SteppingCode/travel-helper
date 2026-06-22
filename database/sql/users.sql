CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fullname TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    phone TEXT UNIQUE NOT NULL,
    city TEXT DEFAULT '',
    country TEXT NOT NULL,
    hashed_password TEXT NOT NULL,
    is_admin BOOLEAN NOT NULL DEFAULT 0,
    email_notifications BOOLEAN NOT NULL DEFAULT 0,
    budget DECIMAL(12, 2) DEFAULT NULL,
    has_avatar BOOLEAN NOT NULL DEFAULT 0,
    personal_id TEXT UNIQUE NOT NULL,
    created_at DATETIME NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_users_personal_id ON users(personal_id);
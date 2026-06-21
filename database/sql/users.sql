CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fullname TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    phone TEXT UNIQUE NOT NULL,
    city TEXT,
    country TEXT NOT NULL,
    hashed_password TEXT NOT NULL,
    is_admin BOOLEAN NOT NULL DEFAULT 0,
    email_notifications BOOLEAN NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL
);
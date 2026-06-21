CREATE TABLE IF NOT EXISTS places (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    city VARCHAR(100) NOT NULL,
    country VARCHAR(100) NOT NULL,
    rating FLOAT,
    description TEXT NOT NULL,
    subtitle VARCHAR(200),
    created_at DATETIME NOT NULL
);
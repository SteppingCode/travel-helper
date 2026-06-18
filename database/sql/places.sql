CREATE TABLE IF NOT EXISTS places (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    city VARCHAR(100) NOT NULL,
    country VARCHAR(100) NOT NULL,
    rating FLOAT,
    descriptions TEXT NOT NULL,
    images text not null,
    tags text not null
);
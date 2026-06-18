CREATE TABLE IF NOT EXISTS images (
    id INTEGER PRIMARY KEY,
    file_path VARCHAR(500) NOT NULL,
    original_name VARCHAR(255),
    mime_type VARCHAR(100),
    file_size BIGINT,
    width INT,
    height INT,
    created_at TIMESTAMP
);
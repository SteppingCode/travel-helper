CREATE TABLE IF NOT EXISTS images_links (
    image_id INTEGER NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id INTEGER NOT NULL,
    created_at DATETIME NOT NULL
);
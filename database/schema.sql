CREATE TABLE IF NOT EXISTS users (
    product_id VARCHAR(255) PRIMARY KEY,
    user_name VARCHAR(255),
    user_rating VARCHAR(255),
    user_registered VARCHAR(255),
    last_online VARCHAR(255),
    user_located VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS product_data (
    product_id VARCHAR(255) PRIMARY KEY,
    url VARCHAR(255),
    img_url JSON,
    posted_at VARCHAR(255),
    title VARCHAR(255),
    price VARCHAR(255),
    phone JSON,
    product_types JSON,
    olx_delivery BOOLEAN,
    description TEXT,
    views VARCHAR(255)
);
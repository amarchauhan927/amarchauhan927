-- =====================================================
--  init_db.sql — Database Setup for Shop Application
--  Run with:  mysql -u root -p < init_db.sql
-- =====================================================

-- 1. Create (or reset) the database
DROP DATABASE IF EXISTS shop_db;
CREATE DATABASE shop_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE shop_db;

-- 2. Products table
CREATE TABLE products (
    id        INT          AUTO_INCREMENT PRIMARY KEY,
    name      VARCHAR(120) NOT NULL,
    price     DECIMAL(10,2) NOT NULL,
    image_url VARCHAR(255) NOT NULL
);

-- 3. Cart table  (product_id is a FK to products)
CREATE TABLE cart (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    quantity   INT NOT NULL DEFAULT 1,
    CONSTRAINT fk_product
        FOREIGN KEY (product_id) REFERENCES products(id)
        ON DELETE CASCADE
);

-- 4. Orders table (one row per completed checkout)
CREATE TABLE orders (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    grand_total DECIMAL(10,2) NOT NULL,
    -- Billing info
    full_name   VARCHAR(120) NOT NULL,
    email       VARCHAR(180) NOT NULL,
    phone       VARCHAR(30)  NOT NULL,
    address     VARCHAR(255) NOT NULL,
    city        VARCHAR(100) NOT NULL,
    state       VARCHAR(100) NOT NULL DEFAULT '',
    zip_code    VARCHAR(20)  NOT NULL,
    country     VARCHAR(100) NOT NULL,
    status      ENUM('pending','processing','shipped','delivered') NOT NULL DEFAULT 'pending'
);

-- 5. Order line items (one row per product per order)
CREATE TABLE order_items (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    order_id   INT          NOT NULL,
    product_id INT          NOT NULL,
    name       VARCHAR(120) NOT NULL,
    price      DECIMAL(10,2) NOT NULL,
    quantity   INT          NOT NULL,
    subtotal   DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (order_id)   REFERENCES orders(id)   ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE RESTRICT
);

-- 6. Seed — 3 sample products
INSERT INTO products (name, price, image_url) VALUES
(
    'Wireless Noise-Cancelling Headphones',
    129.99,
    'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=600&q=80'
),
(
    'Minimalist Leather Watch',
    249.00,
    'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=600&q=80'
),
(
    'Portable Bluetooth Speaker',
    79.95,
    'https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?w=600&q=80'
);

-- Verify
SELECT * FROM products;

-- Online Shop database
-- Week 9: Customers, Products, Orders, Order_Items (Task 9)
-- Week 10: password_hash, Payments
-- Week 12: unique product names, order_token, status 'cancelled',
--          Product_Features (Aigerim), Reviews (Altair)
PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS Reviews;
DROP TABLE IF EXISTS Product_Features;
DROP TABLE IF EXISTS Payments;
DROP TABLE IF EXISTS Order_Items;
DROP TABLE IF EXISTS Orders;
DROP TABLE IF EXISTS Products;
DROP TABLE IF EXISTS Customers;


CREATE TABLE Customers (
    customer_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name     VARCHAR(100) NOT NULL,
    email         VARCHAR(100) NOT NULL UNIQUE CHECK (email LIKE '%_@_%._%'),
    phone         VARCHAR(20),
    address       VARCHAR(200) NOT NULL,
    password_hash VARCHAR(200)          -- week 10: password stored only as a hash
);


CREATE TABLE Products (
    product_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    name          VARCHAR(100) NOT NULL UNIQUE COLLATE NOCASE,  -- week 12: no duplicate products
    category      VARCHAR(50)  NOT NULL,
    price         DECIMAL(10,2) NOT NULL CHECK (price > 0),
    stock_qty     INTEGER NOT NULL DEFAULT 0 CHECK (stock_qty >= 0)
);


CREATE TABLE Orders (
    order_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id    INTEGER NOT NULL,
    order_date     DATE NOT NULL,
    payment_status VARCHAR(10) NOT NULL DEFAULT 'pending'
                   CHECK (payment_status IN ('pending', 'paid', 'failed', 'cancelled')),
    total_amount   DECIMAL(10,2) NOT NULL CHECK (total_amount >= 0),
    -- week 12: one order form = one order. A double click sends the same token twice,
    -- and UNIQUE stops the second order (NULL for test orders created before week 12).
    order_token    VARCHAR(36) UNIQUE,
    FOREIGN KEY (customer_id) REFERENCES Customers(customer_id) ON DELETE RESTRICT
);


CREATE TABLE Order_Items (
    order_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id      INTEGER NOT NULL,
    product_id    INTEGER NOT NULL,
    quantity      INTEGER NOT NULL CHECK (quantity >= 1),
    unit_price    DECIMAL(10,2) NOT NULL CHECK (unit_price > 0),
    UNIQUE (order_id, product_id),
    FOREIGN KEY (order_id)   REFERENCES Orders(order_id)     ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES Products(product_id) ON DELETE RESTRICT
);


INSERT INTO Customers (full_name, email, phone, address) VALUES
('Customer One',   'user01@example.com', '+7 700 000 0001', 'Almaty, Street 1'),
('Customer Two',   'user02@example.com', '+7 700 000 0002', 'Almaty, Street 2'),
('Customer Three', 'user03@example.com', '+7 700 000 0003', 'Astana, Street 3'),
('Customer Four',  'user04@example.com', NULL,              'Shymkent, Street 4'),
('Customer Five',  'user05@example.com', '+7 700 000 0005', 'Almaty, Street 5');

INSERT INTO Products (name, category, price, stock_qty) VALUES
('Wireless Mouse',    'Accessories', 12000, 40),
('USB-C Adapter',     'Accessories',  2500, 60),
('Mechanical Keyboard','Accessories', 28000, 15),
('External SSD 1TB',  'Storage',     45000,  8),
('27" Monitor',       'Displays',    95000,  5);

INSERT INTO Orders (customer_id, order_date, payment_status, total_amount) VALUES
(1, '2026-10-01', 'paid',     42500),
(2, '2026-10-03', 'paid',     28000),
(3, '2026-10-05', 'paid',     57000),
(1, '2026-10-10', 'pending',  95000),
(4, '2026-10-12', 'paid',     24000),
(5, '2026-10-15', 'failed',   45000),
(2, '2026-10-18', 'paid',     14500);

INSERT INTO Order_Items (order_id, product_id, quantity, unit_price) VALUES
(1, 1, 1, 12000), (1, 2, 1, 2500), (1, 3, 1, 28000),
(2, 3, 1, 28000),
(3, 1, 1, 12000), (3, 4, 1, 45000),
(4, 5, 1, 95000),
(5, 1, 2, 12000),
(6, 4, 1, 45000),
(7, 1, 1, 12000), (7, 2, 1, 2500);

-- =========================================================
-- Week 10: Payments table (next action from Task 9)
-- One order can have several payment attempts (1:M):
-- e.g. a failed card payment and then a successful one.
-- =========================================================
CREATE TABLE Payments (
    payment_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id    INTEGER NOT NULL,
    amount      DECIMAL(10,2) NOT NULL CHECK (amount > 0),
    method      VARCHAR(10) NOT NULL CHECK (method IN ('card', 'kaspi', 'cash')),
    status      VARCHAR(10) NOT NULL CHECK (status IN ('paid', 'failed')),
    paid_at     DATETIME NOT NULL,
    FOREIGN KEY (order_id) REFERENCES Orders(order_id) ON DELETE RESTRICT
);

-- Week 11: an order can be paid only once.
-- Failed attempts can repeat, but only ONE row with status 'paid' per order is allowed,
-- even if the customer double-clicks "Pay" and two requests arrive at the same time.
CREATE UNIQUE INDEX one_paid_payment_per_order ON Payments(order_id) WHERE status = 'paid';

-- Payment attempts that match the test orders above
-- (order 3: failed first, then paid; order 4: no attempt yet = pending)
INSERT INTO Payments (order_id, amount, method, status, paid_at) VALUES
(1, 42500, 'card',  'paid',   '2026-10-01 10:15'),
(2, 28000, 'kaspi', 'paid',   '2026-10-03 12:40'),
(3, 57000, 'card',  'failed', '2026-10-05 09:05'),
(3, 57000, 'kaspi', 'paid',   '2026-10-05 09:12'),
(5, 24000, 'kaspi', 'paid',   '2026-10-12 18:30'),
(6, 45000, 'card',  'failed', '2026-10-15 20:02'),
(7, 14500, 'card',  'paid',   '2026-10-18 11:47');

-- =========================================================
-- Week 12: product features (owner: Shointay Aigerim)
-- One product has many features (1:M); the same feature cannot
-- appear twice for one product, e.g. two "Warranty" rows.
-- =========================================================
CREATE TABLE Product_Features (
    feature_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id    INTEGER NOT NULL,
    feature_name  VARCHAR(50)  NOT NULL,
    feature_value VARCHAR(100) NOT NULL,
    UNIQUE (product_id, feature_name COLLATE NOCASE),
    FOREIGN KEY (product_id) REFERENCES Products(product_id) ON DELETE CASCADE
);

INSERT INTO Product_Features (product_id, feature_name, feature_value) VALUES
(1, 'Connection', 'Bluetooth 5.1 + USB receiver'),
(1, 'Battery', 'up to 12 months (AA)'),
(1, 'Warranty', '12 months'),
(2, 'Ports', 'HDMI 4K, 2 x USB-A 3.0, USB-C PD 100 W'),
(2, 'Cable length', '15 cm'),
(2, 'Warranty', '6 months'),
(3, 'Switches', 'Red (linear)'),
(3, 'Layout', 'English / Russian / Kazakh'),
(3, 'Backlight', 'RGB'),
(3, 'Warranty', '24 months'),
(4, 'Capacity', '1 TB'),
(4, 'Speed', 'up to 1050 MB/s'),
(4, 'Connection', 'USB-C 3.2 Gen 2'),
(4, 'Warranty', '36 months'),
(5, 'Resolution', '2560 x 1440 (QHD)'),
(5, 'Refresh rate', '144 Hz'),
(5, 'Panel', 'IPS'),
(5, 'Warranty', '24 months');

-- =========================================================
-- Week 12: ratings and feedback (owner: Abenov Altair)
-- Only a customer with a PAID order of the product can write a review
-- (checked in reviews.py); one review per customer per product (UNIQUE).
-- =========================================================
CREATE TABLE Reviews (
    review_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id  INTEGER NOT NULL,
    customer_id INTEGER NOT NULL,
    rating      INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
    comment     VARCHAR(500),
    created_at  DATETIME NOT NULL,
    UNIQUE (product_id, customer_id),
    FOREIGN KEY (product_id)  REFERENCES Products(product_id)   ON DELETE CASCADE,
    FOREIGN KEY (customer_id) REFERENCES Customers(customer_id) ON DELETE CASCADE
);

-- Reviews from test customers who have a paid order of that product
INSERT INTO Reviews (product_id, customer_id, rating, comment, created_at) VALUES
(1, 1, 5, 'Light and quiet, the battery still works after a month.', '2026-10-08 19:20'),
(1, 3, 4, 'Good mouse, but the receiver is easy to lose.',             '2026-10-12 21:05'),
(1, 4, 5, 'Bought two for the office, both work perfectly.',          '2026-10-20 10:40'),
(2, 2, 3, 'Works, but gets warm when the monitor is connected.',      '2026-10-25 14:10'),
(3, 1, 4, 'Nice keys, a bit loud for night work.',                    '2026-10-09 22:30'),
(3, 2, 5, 'Great keyboard, the Kazakh layout is very useful.',        '2026-10-11 09:15'),
(4, 3, 5, 'Fast and small, copies a film in seconds.',                '2026-10-14 18:00');

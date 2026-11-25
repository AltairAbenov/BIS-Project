-- =========================================================
-- Week 13: staff accounts and roles (owner: Shointay Aigerim)
-- Customers stay in Customers. Shop workers are in Staff:
--   manager - sees all orders, payments and stock
--   courier - delivers paid orders
--   admin   - creates and disables staff accounts
-- One email can belong to only ONE account in the whole shop:
-- the triggers below stop a customer and a staff member with the same email.
-- =========================================================
CREATE TABLE Staff (
    staff_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name     VARCHAR(100) NOT NULL,
    email         VARCHAR(100) NOT NULL UNIQUE COLLATE NOCASE CHECK (email LIKE '%_@_%._%'),
    phone         VARCHAR(20),
    role          VARCHAR(10)  NOT NULL CHECK (role IN ('manager', 'courier', 'admin')),
    password_hash VARCHAR(200) NOT NULL,
    is_active     INTEGER      NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    created_at    DATETIME     NOT NULL
);

CREATE TRIGGER staff_email_not_customer
BEFORE INSERT ON Staff
WHEN EXISTS (SELECT 1 FROM Customers WHERE lower(email) = lower(NEW.email))
BEGIN
    SELECT RAISE(ABORT, 'UNIQUE constraint failed: this email belongs to a customer');
END;

CREATE TRIGGER customer_email_not_staff
BEFORE INSERT ON Customers
WHEN EXISTS (SELECT 1 FROM Staff WHERE lower(email) = lower(NEW.email))
BEGIN
    SELECT RAISE(ABORT, 'UNIQUE constraint failed: this email belongs to a staff account');
END;

-- Demo accounts (passwords are in README; stored only as hashes)
INSERT INTO Staff (full_name, email, phone, role, password_hash, created_at) VALUES
('Shop Admin',   'admin@onlineshop.kz',   '+7 701 000 00 01', 'admin',   'pbkdf2:sha256:1000000$TkQDVOE8NYxtpUuH$e6ab75bec24be3acb64601e17b77352c2857d91da16cc7a90f00e481924ca339',   '2026-11-25 10:00'),
('Main Manager', 'manager@onlineshop.kz', '+7 701 000 00 02', 'manager', 'pbkdf2:sha256:1000000$td6yAWxROqVBcBWp$8d66613d370748539b19520518ee298d5f836ae07d500acd6e735971441ecb1a', '2026-11-25 10:00'),
('Courier One',  'courier@onlineshop.kz', '+7 701 000 00 03', 'courier', 'pbkdf2:sha256:1000000$JGvDiHbVlh8CuG1a$e2093a054052b51ca74c8ed5ac3f820ce34f338ea0d9b17b4a2ddeeda51ab959', '2026-11-25 10:00');

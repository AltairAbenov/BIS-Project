-- =========================================================
-- Week 13: deliveries (owner: Abenov Altair - courier page)
-- A courier takes a PAID order and delivers it.
-- Orders 1 : 1 Deliveries - order_id is UNIQUE, so two couriers
-- can never take the same order.
-- An order without a row here is "waiting for a courier".
-- =========================================================
CREATE TABLE Deliveries (
    delivery_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id     INTEGER NOT NULL UNIQUE,
    courier_id   INTEGER NOT NULL,
    status       VARCHAR(12) NOT NULL DEFAULT 'on_the_way'
                 CHECK (status IN ('on_the_way', 'delivered')),
    taken_at     DATETIME NOT NULL,
    delivered_at DATETIME,
    CHECK ((status = 'on_the_way' AND delivered_at IS NULL)
        OR (status = 'delivered'  AND delivered_at IS NOT NULL)),
    FOREIGN KEY (order_id)   REFERENCES Orders(order_id) ON DELETE RESTRICT,
    FOREIGN KEY (courier_id) REFERENCES Staff(staff_id)  ON DELETE RESTRICT
);

-- Test deliveries by the demo courier (staff_id 3) for the paid test orders.
-- Orders 5 and 7 are paid and still wait for a courier.
INSERT INTO Deliveries (order_id, courier_id, status, taken_at, delivered_at) VALUES
(1, 3, 'delivered',  '2026-10-02 10:00', '2026-10-02 15:30'),
(2, 3, 'delivered',  '2026-10-04 09:40', '2026-10-04 13:10'),
(3, 3, 'on_the_way', '2026-10-06 11:00', NULL);

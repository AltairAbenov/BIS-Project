"""
Delivery rules (owner: Abenov Altair, week 13).

- only PAID orders can be delivered (pending, failed and cancelled cannot)
- one order - one courier: Deliveries.order_id is UNIQUE
- only the courier who took the order can mark it as delivered
- the courier sees the customer's name, phone and address only for orders
  to deliver - never emails or payment details
"""
import sqlite3
from datetime import datetime


class DeliveryError(Exception):
    """Raised when the courier action is not allowed; the message is shown on the page."""


ORDER_COLUMNS = (
    "o.order_id, o.order_date, o.total_amount, c.full_name, c.phone, c.address, "
    "(SELECT GROUP_CONCAT(p.name || ' x' || oi.quantity, ', ') FROM Order_Items oi "
    " JOIN Products p ON p.product_id = oi.product_id WHERE oi.order_id = o.order_id) AS products"
)


def waiting_orders(db):
    """Paid orders that no courier has taken yet (oldest first)."""
    return db.execute(
        f"SELECT {ORDER_COLUMNS} FROM Orders o JOIN Customers c ON c.customer_id = o.customer_id "
        "WHERE o.payment_status = 'paid' "
        "AND NOT EXISTS (SELECT 1 FROM Deliveries d WHERE d.order_id = o.order_id) "
        "ORDER BY o.order_id"
    ).fetchall()


def my_deliveries(db, courier_id, status):
    return db.execute(
        f"SELECT {ORDER_COLUMNS}, d.taken_at, d.delivered_at FROM Deliveries d "
        "JOIN Orders o ON o.order_id = d.order_id JOIN Customers c ON c.customer_id = o.customer_id "
        "WHERE d.courier_id = ? AND d.status = ? ORDER BY d.taken_at DESC",
        (courier_id, status),
    ).fetchall()


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def take_order(db, order_id, courier_id):
    """The courier takes a paid order: a new row in Deliveries with status 'on_the_way'."""
    order = db.execute("SELECT payment_status FROM Orders WHERE order_id = ?", (order_id,)).fetchone()
    if order is None:
        raise DeliveryError(f"Order #{order_id} does not exist.")
    if order[0] != "paid":
        raise DeliveryError(f"Order #{order_id} is {order[0]} - only paid orders can be delivered.")
    try:
        db.execute(
            "INSERT INTO Deliveries (order_id, courier_id, status, taken_at) VALUES (?, ?, 'on_the_way', ?)",
            (order_id, courier_id, now()),
        )
        db.commit()
    except sqlite3.IntegrityError as e:
        db.rollback()
        if "UNIQUE" in str(e):
            raise DeliveryError(f"Order #{order_id} was already taken by another courier.") from e
        raise DeliveryError(f"Order #{order_id} cannot be taken: {e}") from e


def mark_delivered(db, order_id, courier_id):
    """Only the courier who took the order can finish it."""
    cur = db.execute(
        "UPDATE Deliveries SET status = 'delivered', delivered_at = ? "
        "WHERE order_id = ? AND courier_id = ? AND status = 'on_the_way'",
        (now(), order_id, courier_id),
    )
    if cur.rowcount != 1:
        db.rollback()
        raise DeliveryError(f"Order #{order_id} is not on the way with you.")
    db.commit()


def delivery_status(db, order_id):
    """For the customer's order page: None (not paid), 'waiting', 'on_the_way' or 'delivered'."""
    row = db.execute(
        "SELECT o.payment_status, d.status, d.delivered_at, s.full_name FROM Orders o "
        "LEFT JOIN Deliveries d ON d.order_id = o.order_id "
        "LEFT JOIN Staff s ON s.staff_id = d.courier_id WHERE o.order_id = ?",
        (order_id,),
    ).fetchone()
    if row is None or row[0] != "paid":
        return None
    return {"status": row[1] or "waiting", "delivered_at": row[2], "courier": row[3]}

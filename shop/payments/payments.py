"""
Recording payment attempts and cancelling orders (owner: Khassanov Ramazan).
"""
import sqlite3
from datetime import datetime

from ..catalog.stock import return_to_stock

PAYMENT_METHODS = ("card", "kaspi", "cash")


class PaymentError(Exception):
    """Raised when the payment attempt or the cancellation cannot be done."""


def record_payment(db, order_id, method, success):
    """Record ONE payment attempt (paid or failed) for an order. Returns the new payment_id.

    Every attempt is saved in Payments, so the manager can see how many times
    a customer tried to pay (1:M - one order, many attempts).
    - the order must exist
    - an order that is already paid cannot be paid again (no double payment)
    - a cancelled order cannot be paid (week 12)
    - method must be card, kaspi or cash
    - the amount is taken from the order total, the customer cannot change it
    - success=True -> status 'paid'; success=False -> status 'failed' (can try again)
    The database also allows only one 'paid' row per order (unique index in schema.sql),
    so a double click cannot create two successful payments.
    """
    order = db.execute(
        "SELECT order_id, total_amount, payment_status FROM Orders WHERE order_id = ?",
        (order_id,),
    ).fetchone()
    if order is None:
        raise PaymentError(f"Order {order_id} does not exist.")
    if order[2] == "paid":
        raise PaymentError(f"Order {order_id} is already paid.")
    if order[2] == "cancelled":
        raise PaymentError(f"Order {order_id} is cancelled and cannot be paid.")
    if method not in PAYMENT_METHODS:
        raise PaymentError(f"Unknown payment method '{method}'. Use card, kaspi or cash.")

    status = "paid" if success else "failed"
    try:
        cur = db.execute(
            "INSERT INTO Payments (order_id, amount, method, status, paid_at) VALUES (?, ?, ?, ?, ?)",
            (order_id, order[1], method, status, datetime.now().strftime("%Y-%m-%d %H:%M")),
        )
        db.execute("UPDATE Orders SET payment_status = ? WHERE order_id = ?", (status, order_id))
        db.commit()
    except sqlite3.IntegrityError as e:
        db.rollback()
        if "UNIQUE" in str(e):
            raise PaymentError(f"Order {order_id} is already paid.") from e
        raise PaymentError(f"Payment could not be saved: {e}") from e
    return cur.lastrowid


def cancel_order(db, order_id, customer_id):
    """Week 12 - "if payment is cancelled": the customer cancels an unpaid order.

    In ONE transaction:
      1. Orders.payment_status -> 'cancelled'
      2. every item goes back to the warehouse (stock.return_to_stock)
    - only the owner of the order can cancel it
    - only 'pending' or 'failed' orders can be cancelled; a paid order cannot
      (that would be a refund, not part of this prototype)
    - earlier failed attempts stay in Payments, so the manager still sees them
    Returns the number of items returned to stock.
    """
    order = db.execute(
        "SELECT payment_status FROM Orders WHERE order_id = ? AND customer_id = ?",
        (order_id, customer_id),
    ).fetchone()
    if order is None:
        raise PaymentError(f"Order {order_id} does not exist.")
    if order[0] == "paid":
        raise PaymentError(f"Order {order_id} is already paid and cannot be cancelled.")
    if order[0] == "cancelled":
        raise PaymentError(f"Order {order_id} is already cancelled.")

    items = db.execute(
        "SELECT product_id, quantity FROM Order_Items WHERE order_id = ?", (order_id,)
    ).fetchall()
    try:
        cur = db.execute(
            "UPDATE Orders SET payment_status = 'cancelled' "
            "WHERE order_id = ? AND payment_status IN ('pending', 'failed')",
            (order_id,),
        )
        if cur.rowcount != 1:  # the status changed at the same moment (e.g. it was just paid)
            raise PaymentError(f"Order {order_id} cannot be cancelled now.")
        for product_id, qty in items:
            return_to_stock(db, product_id, qty)
        db.commit()
    except (PaymentError, sqlite3.Error):
        db.rollback()
        raise
    return sum(qty for _, qty in items)


def payment_history(db, order_id):
    return db.execute(
        "SELECT method, status, paid_at FROM Payments WHERE order_id = ? ORDER BY payment_id",
        (order_id,),
    ).fetchall()

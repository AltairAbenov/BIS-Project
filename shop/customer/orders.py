"""
Placing an order (owner: Abenov Altair).

place_order() saves one order as ONE transaction:
  1. INSERT INTO Orders       (status 'pending', total = quantity x price)
  2. INSERT INTO Order_Items  (unit_price = price at the moment of purchase)
  3. UPDATE Products          (stock_qty - quantity, see stock.py)
If any step fails, ROLLBACK undoes all of them.

Week 12: every order form carries a one-time order_token (see catalog.py).
If the same form is sent twice (double click), the second request gets
the order that already exists instead of a second order.
"""
import sqlite3
from datetime import date

from ..catalog.catalog import find_order_by_token
from ..catalog.stock import StockError, parse_quantity, take_from_stock


class OrderError(Exception):
    """Raised when the order cannot be placed; the message is shown to the customer."""


def get_product(db, product_id):
    return db.execute(
        "SELECT product_id, name, category, price, stock_qty FROM Products WHERE product_id = ?",
        (product_id,),
    ).fetchone()


def place_order(db, customer_id, product_id, raw_qty, token=None):
    """Create an order for one product.
    Returns (order_id, is_duplicate): is_duplicate is True when this form was already sent."""
    if token:
        existing = find_order_by_token(db, token, customer_id)
        if existing:
            return existing, True

    product = get_product(db, product_id)
    if product is None:
        raise OrderError("This product does not exist.")

    qty, error = parse_quantity(raw_qty, product["stock_qty"])
    if error:
        raise OrderError(error)

    total = qty * product["price"]
    try:
        cur = db.execute(
            "INSERT INTO Orders (customer_id, order_date, payment_status, total_amount, order_token) "
            "VALUES (?, ?, 'pending', ?, ?)",
            (customer_id, date.today().isoformat(), total, token),
        )
        order_id = cur.lastrowid
        db.execute(
            "INSERT INTO Order_Items (order_id, product_id, quantity, unit_price) "
            "VALUES (?, ?, ?, ?)",
            (order_id, product_id, qty, product["price"]),
        )
        take_from_stock(db, product_id, qty)
        db.commit()
    except StockError as e:
        db.rollback()
        raise OrderError(str(e)) from e
    except sqlite3.IntegrityError as e:
        db.rollback()
        # the same token arrived at the same moment: the database UNIQUE rule stopped it
        existing = token and find_order_by_token(db, token, customer_id)
        if existing:
            return existing, True
        raise OrderError("The order could not be saved. Please try again.") from e
    except sqlite3.Error as e:
        db.rollback()
        raise OrderError("The order could not be saved. Please try again.") from e
    return order_id, False


def get_order(db, order_id, customer_id):
    """Return (order, items) only if the order belongs to this customer, else (None, [])."""
    order = db.execute(
        "SELECT o.order_id, o.order_date, o.payment_status, o.total_amount, c.full_name, c.address "
        "FROM Orders o JOIN Customers c ON c.customer_id = o.customer_id "
        "WHERE o.order_id = ? AND o.customer_id = ?",
        (order_id, customer_id),
    ).fetchone()
    if order is None:
        return None, []
    items = db.execute(
        "SELECT oi.product_id, p.name, oi.quantity, oi.unit_price, oi.quantity * oi.unit_price AS line_total "
        "FROM Order_Items oi JOIN Products p ON p.product_id = oi.product_id "
        "WHERE oi.order_id = ?",
        (order_id,),
    ).fetchall()
    return order, items


def list_orders(db, customer_id):
    return db.execute(
        "SELECT o.order_id, o.order_date, o.payment_status, o.total_amount, "
        "       GROUP_CONCAT(p.name || ' x' || oi.quantity, ', ') AS products "
        "FROM Orders o "
        "JOIN Order_Items oi ON oi.order_id = o.order_id "
        "JOIN Products p ON p.product_id = oi.product_id "
        "WHERE o.customer_id = ? "
        "GROUP BY o.order_id ORDER BY o.order_id DESC",
        (customer_id,),
    ).fetchall()

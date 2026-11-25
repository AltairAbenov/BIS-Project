"""
Manager dashboard (owner: Shointay Aigerim, week 13 - manager account).
Only staff with the role "manager" can open these pages.
"""
from flask import abort, render_template, request

from ..auth import role_required
from ..db import get_db
from . import bp

STATUSES = ("pending", "failed", "paid", "cancelled")
LOW_STOCK = 10


def shop_summary(db):
    """Numbers for the top of the dashboard."""
    row = db.execute(
        "SELECT COUNT(*) AS orders, "
        "  SUM(payment_status IN ('pending', 'failed')) AS unpaid, "
        "  COALESCE(SUM(CASE WHEN payment_status IN ('pending', 'failed') THEN total_amount END), 0) AS unpaid_sum, "
        "  COALESCE(SUM(CASE WHEN payment_status = 'paid' THEN total_amount END), 0) AS revenue, "
        "  SUM(payment_status = 'cancelled') AS cancelled "
        "FROM Orders"
    ).fetchone()
    return dict(row)


@bp.route("/")
@role_required("manager")
def dashboard():
    db = get_db()
    status = request.args.get("status", "")
    q = request.args.get("q", "").strip()

    sql = (
        "SELECT o.order_id, o.order_date, o.payment_status, o.total_amount, "
        "       c.full_name, c.email, "
        "       (SELECT COUNT(*) FROM Payments p WHERE p.order_id = o.order_id) AS attempts, "
        "       (SELECT COUNT(*) FROM Payments p WHERE p.order_id = o.order_id AND p.status = 'failed') AS failed, "
        "       (SELECT GROUP_CONCAT(pr.name || ' x' || oi.quantity, ', ') "
        "          FROM Order_Items oi JOIN Products pr ON pr.product_id = oi.product_id "
        "         WHERE oi.order_id = o.order_id) AS products "
        "FROM Orders o JOIN Customers c ON c.customer_id = o.customer_id WHERE 1 = 1 "
    )
    params = []
    if status == "unpaid":
        sql += "AND o.payment_status IN ('pending', 'failed') "
    elif status in STATUSES:
        sql += "AND o.payment_status = ? "
        params.append(status)
    if q:
        sql += "AND (c.full_name LIKE ? OR c.email LIKE ?) "
        params += [f"%{q}%", f"%{q}%"]
    sql += "ORDER BY o.order_id DESC"

    low_stock = db.execute(
        "SELECT product_id, name, stock_qty FROM Products WHERE stock_qty < ? ORDER BY stock_qty", (LOW_STOCK,)
    ).fetchall()
    return render_template(
        "manager/dashboard.html", orders=db.execute(sql, params).fetchall(),
        summary=shop_summary(db), low_stock=low_stock, status=status, q=q,
        statuses=STATUSES, low_limit=LOW_STOCK,
    )


@bp.route("/orders/<int:order_id>")
@role_required("manager")
def order_view(order_id):
    """The manager can open any order (customers only their own)."""
    db = get_db()
    order = db.execute(
        "SELECT o.*, c.full_name, c.email, c.phone, c.address "
        "FROM Orders o JOIN Customers c ON c.customer_id = o.customer_id WHERE o.order_id = ?",
        (order_id,),
    ).fetchone()
    if order is None:
        abort(404)
    items = db.execute(
        "SELECT p.name, oi.quantity, oi.unit_price, oi.quantity * oi.unit_price AS line_total "
        "FROM Order_Items oi JOIN Products p ON p.product_id = oi.product_id WHERE oi.order_id = ?",
        (order_id,),
    ).fetchall()
    payments = db.execute(
        "SELECT method, status, amount, paid_at FROM Payments WHERE order_id = ? ORDER BY payment_id",
        (order_id,),
    ).fetchall()
    return render_template("manager/order.html", order=order, items=items, payments=payments)

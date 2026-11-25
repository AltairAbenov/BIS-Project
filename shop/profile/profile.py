"""
Profile rules and the manager's shop summary (owner: Yeleussizova Zhannur, week 13).

- a staff member can change their own name and phone (same rules as registration)
- password change: the current password must be correct; the new one has
  8+ characters with a letter and a digit, typed twice, and differs from the old one
- email and role cannot be changed here (only the admin manages accounts)
"""
import re
from datetime import date

from werkzeug.security import check_password_hash, generate_password_hash

from ..customer.routes import NAME_RE, normalize_phone


class ProfileError(Exception):
    """args[0] is {field: message}."""


def get_staff(db, staff_id):
    return db.execute(
        "SELECT staff_id, full_name, email, phone, role, created_at FROM Staff WHERE staff_id = ?",
        (staff_id,),
    ).fetchone()


def update_details(db, staff_id, full_name, phone):
    full_name = re.sub(r"\s+", " ", (full_name or "").strip())
    phone = (phone or "").strip()
    errors = {}
    if not (2 <= len(full_name) <= 100) or not NAME_RE.match(full_name):
        errors["full_name"] = "Letters only, for example Dana Manager."
    if phone:
        phone = normalize_phone(phone)
        if phone is None:
            errors["phone"] = "Kazakhstan number, e.g. +7 701 123 45 67."
    if errors:
        raise ProfileError(errors)
    db.execute("UPDATE Staff SET full_name = ?, phone = ? WHERE staff_id = ?", (full_name, phone or None, staff_id))
    db.commit()
    return full_name


def change_password(db, staff_id, current, new, repeat):
    row = db.execute("SELECT password_hash FROM Staff WHERE staff_id = ?", (staff_id,)).fetchone()
    errors = {}
    if row is None or not check_password_hash(row[0], current or ""):
        errors["current"] = "The current password is wrong."
    elif len(new) < 8 or not re.search(r"[^\W\d_]", new) or not re.search(r"\d", new):
        errors["new"] = "8+ characters with a letter and a digit."
    elif new == current:
        errors["new"] = "The new password must be different from the current one."
    elif new != repeat:
        errors["repeat"] = "Passwords do not match."
    if errors:
        raise ProfileError(errors)
    db.execute("UPDATE Staff SET password_hash = ? WHERE staff_id = ?", (generate_password_hash(new), staff_id))
    db.commit()


def manager_summary(db, today=None):
    """Numbers a manager checks every day."""
    today = today or date.today()
    month = today.strftime("%Y-%m")
    s = db.execute(
        "SELECT "
        "  SUM(order_date = ?) AS orders_today, "
        "  SUM(substr(order_date, 1, 7) = ?) AS orders_month, "
        "  COALESCE(SUM(CASE WHEN substr(order_date, 1, 7) = ? AND payment_status = 'paid' THEN total_amount END), 0) AS revenue_month, "
        "  SUM(payment_status IN ('pending', 'failed')) AS unpaid "
        "FROM Orders",
        (today.isoformat(), month, month),
    ).fetchone()
    failed = db.execute("SELECT COUNT(*) FROM Payments WHERE status = 'failed'").fetchone()[0]
    top = db.execute(
        "SELECT p.name, SUM(oi.quantity) AS sold FROM Order_Items oi "
        "JOIN Orders o ON o.order_id = oi.order_id JOIN Products p ON p.product_id = oi.product_id "
        "WHERE o.payment_status = 'paid' AND substr(o.order_date, 1, 7) = ? "
        "GROUP BY p.product_id ORDER BY sold DESC, p.name LIMIT 1",
        (month,),
    ).fetchone()
    return {
        "orders_today": s["orders_today"] or 0, "orders_month": s["orders_month"] or 0,
        "revenue_month": s["revenue_month"], "unpaid": s["unpaid"] or 0,
        "failed_attempts": failed, "top_product": top["name"] if top else None,
        "top_sold": top["sold"] if top else 0, "month": today.strftime("%B %Y"),
    }

"""
Staff account rules (owner: Bakyt Aiganym, week 13 - admin).

- the admin creates accounts for managers and couriers
  (new admin accounts are not created from the website)
- full name: letters only; email: valid and not used by any customer or staff member;
  temporary password: 8+ characters with a letter and a digit (stored only as a hash)
- the admin can disable and enable accounts; a disabled account cannot log in
  and loses access at once (see role_required in shop/auth.py)
- the admin cannot disable their own account (the shop must always have an admin)
"""
import re
import sqlite3
from datetime import datetime

from werkzeug.security import generate_password_hash

from ..customer.routes import EMAIL_RE, NAME_RE, normalize_phone

ROLES_ADMIN_CAN_CREATE = ("manager", "courier")


class AccountError(Exception):
    """Raised when the account cannot be created or changed; the message is shown on the page."""


def list_staff(db):
    return db.execute(
        "SELECT staff_id, full_name, email, phone, role, is_active, created_at FROM Staff "
        "ORDER BY is_active DESC, role, full_name"
    ).fetchall()


def check_form(form):
    """Returns {field: error}. Cleans the values in the form dict."""
    errors = {}
    form["full_name"] = re.sub(r"\s+", " ", form.get("full_name", "").strip())
    form["email"] = form.get("email", "").strip().lower()
    form["phone"] = form.get("phone", "").strip()
    if not (2 <= len(form["full_name"]) <= 100) or not NAME_RE.match(form["full_name"]):
        errors["full_name"] = "Letters only, for example Dana Manager."
    if not EMAIL_RE.match(form["email"]):
        errors["email"] = "Enter a valid email."
    if form["phone"]:
        phone = normalize_phone(form["phone"])
        if phone is None:
            errors["phone"] = "Kazakhstan number, e.g. +7 701 123 45 67."
        else:
            form["phone"] = phone
    if form.get("role") not in ROLES_ADMIN_CAN_CREATE:
        errors["role"] = "Choose manager or courier."
    pw = form.get("password", "")
    if len(pw) < 8 or not re.search(r"[^\W\d_]", pw) or not re.search(r"\d", pw):
        errors["password"] = "8+ characters with a letter and a digit."
    return errors


def create_staff(db, form):
    """Create a manager or courier account. Returns the new staff_id."""
    errors = check_form(form)
    if errors:
        raise AccountError(errors)
    try:
        cur = db.execute(
            "INSERT INTO Staff (full_name, email, phone, role, password_hash, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (form["full_name"], form["email"], form["phone"] or None, form["role"],
             generate_password_hash(form["password"]), datetime.now().strftime("%Y-%m-%d %H:%M")),
        )
        db.commit()
    except sqlite3.IntegrityError as e:
        db.rollback()
        if "UNIQUE" in str(e):
            raise AccountError({"email": "This email is already used by a customer or a staff account."}) from e
        raise AccountError({"email": f"The account breaks a database rule: {e}"}) from e
    return cur.lastrowid


def set_active(db, staff_id, active, admin_id):
    """Disable (active=False) or enable an account."""
    if staff_id == admin_id and not active:
        raise AccountError({"_": "You cannot disable your own account."})
    row = db.execute("SELECT full_name FROM Staff WHERE staff_id = ?", (staff_id,)).fetchone()
    if row is None:
        raise AccountError({"_": f"Account #{staff_id} does not exist."})
    db.execute("UPDATE Staff SET is_active = ? WHERE staff_id = ?", (1 if active else 0, staff_id))
    db.commit()
    return row[0]


def staff_counts(db):
    return {r[0]: r[1] for r in db.execute(
        "SELECT role, COUNT(*) FROM Staff WHERE is_active = 1 GROUP BY role")}

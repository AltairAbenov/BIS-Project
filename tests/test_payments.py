"""
Tests for record_payment() and cancel_order() in shop/payments/payments.py (owner: Khassanov Ramazan).
Every test uses a fresh in-memory copy of the database, so shop.db is not changed.
Run from the project folder:  python tests/test_payments.py

R1-R3 are the three required cases: successful payment, failed payment, non-existing order.
R4-R6 check what the manager needs: no double payment, and the number of attempts.
C1-C5 (week 12) check what happens if the payment is cancelled.
"""
import os
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from shop.db import schema_files  # noqa: E402
from shop.payments.payments import PaymentError, cancel_order, record_payment  # noqa: E402


def fresh_db():
    db = sqlite3.connect(":memory:")
    db.execute("PRAGMA foreign_keys = ON")
    for path in schema_files(ROOT):
        with open(path, encoding="utf-8") as f:
            db.executescript(f.read())
    return db


def attempts(db, order_id):
    return db.execute(
        "SELECT method, status FROM Payments WHERE order_id = ? ORDER BY payment_id", (order_id,)
    ).fetchall()


def order_status(db, order_id):
    return db.execute("SELECT payment_status FROM Orders WHERE order_id = ?", (order_id,)).fetchone()[0]


results = []


def check(test_id, name, ok, actual):
    results.append((test_id, name, "PASS" if ok else "FAIL", actual))


# R1 (required): successful payment of pending order 4 (95 000 KZT)
db = fresh_db()
pid = record_payment(db, 4, "kaspi", success=True)
row = db.execute("SELECT amount, status FROM Payments WHERE payment_id = ?", (pid,)).fetchone()
check("R1", "Successful payment (order 4)",
      row == (95000, "paid") and order_status(db, 4) == "paid",
      f"payment #{pid} saved: {row[0]:.0f} KZT, {row[1]}; order 4 is now {order_status(db, 4)}")

# R2 (required): failed payment of pending order 4
db = fresh_db()
pid = record_payment(db, 4, "card", success=False)
check("R2", "Failed payment (order 4)",
      attempts(db, 4) == [("card", "failed")] and order_status(db, 4) == "failed",
      f"payment #{pid} saved as failed; order 4 is {order_status(db, 4)}, the customer can try again")

# R3 (required): payment for an order that does not exist
db = fresh_db()
before = db.execute("SELECT COUNT(*) FROM Payments").fetchone()[0]
try:
    record_payment(db, 99, "card", success=True)
    check("R3", "Non-existing order 99", False, "accepted")
except PaymentError as e:
    after = db.execute("SELECT COUNT(*) FROM Payments").fetchone()[0]
    check("R3", "Non-existing order 99", before == after, f"rejected: {e} Nothing saved.")

# R4: the customer tries to pay an order that is already paid
db = fresh_db()
try:
    record_payment(db, 1, "card", success=True)
    check("R4", "Pay order 1 again (already paid)", False, "accepted - DOUBLE PAYMENT")
except PaymentError as e:
    check("R4", "Pay order 1 again (already paid)", len(attempts(db, 1)) == 1, f"rejected: {e}")

# R5: double click - a second 'paid' row arrives directly, past the function check
db = fresh_db()
try:
    db.execute("INSERT INTO Payments (order_id, amount, method, status, paid_at) "
               "VALUES (1, 42500, 'card', 'paid', '2026-11-11 10:00')")
    check("R5", "Double click: 2nd paid row for order 1", False, "accepted - DOUBLE PAYMENT")
except sqlite3.IntegrityError as e:
    check("R5", "Double click: 2nd paid row for order 1", True, f"rejected by the database: {e}")

# R6: manager view - how many times the customer tried to pay
db = fresh_db()
record_payment(db, 4, "card", success=False)
record_payment(db, 4, "card", success=False)
record_payment(db, 4, "kaspi", success=True)
hist = attempts(db, 4)
check("R6", "Manager sees the number of attempts", len(hist) == 3 and order_status(db, 4) == "paid",
      f"order 4: {len(hist)} attempts ({', '.join(m + ' ' + s for m, s in hist)})")


def stock(db, product_id):
    return db.execute("SELECT stock_qty FROM Products WHERE product_id = ?", (product_id,)).fetchone()[0]


# C1: the customer cancels a pending order -> cancelled, the monitor goes back to stock
db = fresh_db()
before = stock(db, 5)
returned = cancel_order(db, 4, customer_id=1)
check("C1", "Cancel pending order 4", order_status(db, 4) == "cancelled" and stock(db, 5) == before + 1,
      f"order 4 is {order_status(db, 4)}; {returned} item returned, monitor stock {before} -> {stock(db, 5)}")

# C2: a paid order cannot be cancelled
db = fresh_db()
try:
    cancel_order(db, 1, customer_id=1)
    check("C2", "Cancel paid order 1", False, "accepted")
except PaymentError as e:
    check("C2", "Cancel paid order 1", order_status(db, 1) == "paid", f"rejected: {e}")

# C3: payment failed, then the customer cancels -> the failed attempt stays for the manager
db = fresh_db()
record_payment(db, 4, "card", success=False)
cancel_order(db, 4, customer_id=1)
check("C3", "Failed payment, then cancel (order 4)",
      order_status(db, 4) == "cancelled" and attempts(db, 4) == [("card", "failed")],
      f"order 4 is {order_status(db, 4)}; attempts kept: {', '.join(m + ' ' + s for m, s in attempts(db, 4))}")

# C4: a cancelled order cannot be paid
db = fresh_db()
cancel_order(db, 4, customer_id=1)
try:
    record_payment(db, 4, "kaspi", success=True)
    check("C4", "Pay a cancelled order", False, "accepted")
except PaymentError as e:
    check("C4", "Pay a cancelled order", attempts(db, 4) == [], f"rejected: {e}")

# C5: another customer cannot cancel somebody else's order
db = fresh_db()
try:
    cancel_order(db, 4, customer_id=2)
    check("C5", "Customer 2 cancels order of customer 1", False, "accepted")
except PaymentError as e:
    check("C5", "Customer 2 cancels order of customer 1", order_status(db, 4) == "pending",
          f"rejected: {e} (looks like it does not exist for customer 2)")

print(f"{'test':<6}{'case':<42}{'result':<8}details")
for r in results:
    print(f"{r[0]:<6}{r[1]:<42}{r[2]:<8}{r[3]}")
print(f"\n{sum(r[2] == 'PASS' for r in results)} of {len(results)} tests passed")

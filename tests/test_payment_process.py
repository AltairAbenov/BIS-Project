"""
Whole payment process through the website (owner: Khassanov Ramazan, week 13).

Unlike tests/test_payments.py (which calls the functions directly), these tests
click through the real pages like a customer: register -> order -> pay page ->
declined -> try again -> paid, and the cancel path. Each test runs the website
on a fresh temporary database (shop.db is not changed).
Run from the project folder:  python tests/test_payment_process.py
"""
import atexit
import os
import re
import sqlite3
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from shop import create_app  # noqa: E402

results = []


def check(test_id, name, ok, actual):
    results.append((test_id, name, "PASS" if ok else "FAIL", actual))


def new_site():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    os.remove(path)
    atexit.register(lambda: os.path.exists(path) and os.remove(path))
    app = create_app(database=path)
    app.config["TESTING"] = True
    return app, path


def one(path, query, *args):
    con = sqlite3.connect(path)
    row = con.execute(query, args).fetchone()
    con.close()
    return row[0] if row else None


def customer(app, email):
    c = app.test_client()
    c.post("/register", data=dict(full_name="Test Buyer", email=email, phone="",
                                  address="Almaty, Abay ave 10", password="secret123", password2="secret123"))
    return c


def place(c, product_id, qty):
    """Open the product page, take the one-time token from the form and place the order."""
    page = c.get(f"/product/{product_id}").data.decode()
    token = re.search(r'name="order_token" value="([^"]+)"', page).group(1)
    r = c.post(f"/order/{product_id}", data={"quantity": str(qty), "order_token": token})
    return int(r.headers["Location"].rstrip("/").split("/")[-1])


def pay(c, order_id, method, answer, **extra):
    return c.post(f"/orders/{order_id}/pay", data={"method": method, "bank_answer": answer, **extra},
                  follow_redirects=True)


app, db = new_site()

# W1: a guest cannot pay
g = app.test_client()
r1 = g.get("/orders/1/pay")
r2 = g.post("/orders/1/pay", data={"method": "card", "bank_answer": "approved"})
check("W1", "Guest opens or sends the payment page", r1.status_code == 302 and "/login" in r1.headers["Location"]
      and one(db, "SELECT COUNT(*) FROM Payments WHERE order_id = 1") == 1, "sent to login, nothing saved")

# W2: register and order 2 x External SSD: order pending, stock reserved
c = customer(app, "buyer@example.com")
stock0 = one(db, "SELECT stock_qty FROM Products WHERE product_id = 4")
oid = place(c, 4, 2)
check("W2", "Order 2 × External SSD", one(db, "SELECT payment_status FROM Orders WHERE order_id = ?", oid) == "pending"
      and one(db, "SELECT total_amount FROM Orders WHERE order_id = ?", oid) == 90000
      and one(db, "SELECT stock_qty FROM Products WHERE product_id = 4") == stock0 - 2,
      f"order #{oid}: pending, 90 000 ₸, stock {stock0} → {stock0 - 2}")

# W3: the payment page shows the order total
page = c.get(f"/orders/{oid}/pay").data.decode()
check("W3", "Payment page shows the total", "Pay 90 000" in page and "Cancel order instead" in page,
      "button “Pay 90 000 ₸” and “Cancel order instead”")

# W4: the bank declines
page = pay(c, oid, "card", "declined").data.decode()
check("W4", "Bank declines the payment", "declined" in page and
      one(db, "SELECT payment_status FROM Orders WHERE order_id = ?", oid) == "failed" and
      one(db, "SELECT COUNT(*) FROM Payments WHERE order_id = ? AND status = 'failed'", oid) == 1 and
      one(db, "SELECT stock_qty FROM Products WHERE product_id = 4") == stock0 - 2,
      "status failed, 1 failed attempt saved, stock still reserved")

# W5: the customer tries to change the amount in the request -> ignored
page = pay(c, oid, "kaspi", "approved", amount="1").data.decode()
amount = one(db, "SELECT amount FROM Payments WHERE order_id = ? AND status = 'paid'", oid)
check("W5", "Try again (amount=1 sent in the request)", "Payment successful" in page and amount == 90000,
      f"paid {amount:.0f} ₸ — the amount comes from the order, not from the request")

# W6: two attempts are kept: failed, then paid
hist = [r for r in sqlite3.connect(db).execute(
    "SELECT method, status FROM Payments WHERE order_id = ? ORDER BY payment_id", (oid,))]
check("W6", "Attempt history after retry", hist == [("card", "failed"), ("kaspi", "paid")] and
      "Payment attempts" in c.get(f"/orders/{oid}").data.decode(), "card failed → kaspi paid, shown on the order page")

# W7: pay the same order again
page = pay(c, oid, "card", "approved").data.decode()
check("W7", "Pay an order that is already paid", "nothing to pay" in page and
      one(db, "SELECT COUNT(*) FROM Payments WHERE order_id = ?", oid) == 2, "no third attempt")

# W8: double click on "Pay": two requests at once for one pending order
oid2 = place(c, 1, 1)
pay(c, oid2, "card", "approved")
pay(c, oid2, "card", "approved")
check("W8", "Double click on “Pay”", one(db, "SELECT COUNT(*) FROM Payments WHERE order_id = ? AND status = 'paid'", oid2) == 1,
      "only one successful payment")

# W9: unknown payment method in a crafted request
oid3 = place(c, 3, 1)
page = pay(c, oid3, "bitcoin", "approved").data.decode()
check("W9", "Unknown payment method", "Unknown payment method" in page and
      one(db, "SELECT COUNT(*) FROM Payments WHERE order_id = ?", oid3) == 0, "rejected, nothing saved")

# W10: cancel instead of paying: stock comes back, cancelled order cannot be paid
k0 = one(db, "SELECT stock_qty FROM Products WHERE product_id = 3")
pay(c, oid3, "card", "declined")
c.post(f"/orders/{oid3}/cancel")
page = pay(c, oid3, "card", "approved").data.decode()
check("W10", "Declined, then cancel; then try to pay", one(db, "SELECT payment_status FROM Orders WHERE order_id = ?", oid3) == "cancelled"
      and one(db, "SELECT stock_qty FROM Products WHERE product_id = 3") == k0 + 1 and "nothing to pay" in page
      and one(db, "SELECT COUNT(*) FROM Payments WHERE order_id = ?", oid3) == 1,
      "cancelled, keyboard back in stock, failed attempt kept, payment blocked")

# W11: a paid order cannot be cancelled
page = c.post(f"/orders/{oid}/cancel", follow_redirects=True).data.decode()
check("W11", "Cancel a paid order", "cannot be cancelled" in page and
      one(db, "SELECT payment_status FROM Orders WHERE order_id = ?", oid) == "paid", "rejected, still paid")

# W12: another customer cannot see, pay or cancel my order
other = customer(app, "other@example.com")
oid4 = place(c, 2, 1)
v = other.get(f"/orders/{oid4}").status_code
p = other.post(f"/orders/{oid4}/pay", data={"method": "card", "bank_answer": "approved"}).status_code
other.post(f"/orders/{oid4}/cancel")
check("W12", "Another customer uses my order number", v == 404 and p == 404 and
      one(db, "SELECT payment_status FROM Orders WHERE order_id = ?", oid4) == "pending", "404 for view and pay; cancel rejected, order still pending")

# W13: the manager sees the attempts of this order
m = app.test_client()
m.post("/login", data={"email": "manager@onlineshop.kz", "password": "Manager123"})
page = m.get(f"/manager/orders/{oid}").data.decode()
check("W13", "Manager checks the order", "Payment attempts (2)" in page and "kaspi" in page, "2 attempts visible to the manager")

print(f"{'test':<6}{'case':<44}{'result':<8}details")
for t in results:
    print(f"{t[0]:<6}{t[1]:<44}{t[2]:<8}{t[3]}")
print(f"\n{sum(t[2] == 'PASS' for t in results)} of {len(results)} tests passed")

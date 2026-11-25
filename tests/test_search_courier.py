"""
Tests for search / sorting on the main page and the courier page
(owner: Abenov Altair, week 13).
Each test runs the real website on a fresh temporary database (shop.db is not changed).
Run from the project folder:  python tests/test_search_courier.py
"""
import atexit
import html
import os
import re
import sqlite3
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from shop import create_app  # noqa: E402
from werkzeug.security import generate_password_hash  # noqa: E402

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
    return app.test_client(), path


def names(client, url):
    page = client.get(url).data.decode()
    return [html.unescape(n) for n in re.findall(r"<h3>(.*?)</h3>", page)]


def login(client, email, password):
    return client.post("/login", data={"email": email, "password": password})


def one(path, query, *args):
    con = sqlite3.connect(path)
    row = con.execute(query, args).fetchone()
    con.close()
    return row[0] if row else None


def run(path, query, *args):
    con = sqlite3.connect(path)
    con.execute(query, args)
    con.commit()
    con.close()


COURIER = ("courier@onlineshop.kz", "Courier123")

# ---------- search and sorting ----------
c, db = new_site()
r = names(c, "/?q=bluetooth")
check("S1", "Search by a feature: “bluetooth”", r == ["Wireless Mouse"], f"found: {r}")

r = names(c, "/?q=usb-c+1tb")
check("S2", "Two words: “usb-c 1tb”", r == ["External SSD 1TB"], f"found: {r}")

r = names(c, "/?min_price=10000&max_price=30000&sort=price_asc")
check("S3", "Price 10 000 – 30 000, cheapest first", r == ["Wireless Mouse", "Mechanical Keyboard"], f"found: {r}")

page = c.get("/?min_price=30000&max_price=10000").data.decode()
check("S4", "Price “from” bigger than “to”", "swapped" in page and "Mechanical Keyboard" in page,
      "prices swapped, results shown")

r = names(c, "/?sort=bestsellers")
check("S5", "Sort: bestsellers", r[0] == "Wireless Mouse" and r[-1] == '27" Monitor',
      f"first {r[0]} (5 sold), last {r[-1]} (0 sold)")

run(db, "UPDATE Products SET stock_qty = 0 WHERE name = 'USB-C Adapter'")
r = names(c, "/?in_stock=1")
check("S6", "In stock only", "USB-C Adapter" not in r and len(r) == 4, f"{len(r)} products, adapter hidden")

r = names(c, "/?q=zzz")
check("S7", "Nothing found", r == [] and "Nothing found" in c.get("/?q=zzz").data.decode(), "message shown")

# ---------- courier ----------
c, db = new_site()
login(c, *COURIER)
page = c.get("/courier/").data.decode()
waiting = re.findall(r"Order #(\d+)</b>", page.split("Waiting for a courier")[1].split("Delivered by me")[0])
check("K1", "Courier sees paid orders waiting", waiting == ["5", "7"],
      f"waiting: {waiting} (4 pending, 6 failed are hidden)")

r = c.post("/courier/take/5", follow_redirects=True)
check("K2", "Courier takes order 5", one(db, "SELECT status FROM Deliveries WHERE order_id = 5") == "on_the_way",
      "order 5 is on the way")

run(db, "INSERT INTO Staff (full_name, email, role, password_hash, created_at) VALUES (?, ?, 'courier', ?, '2026-11-25')",
    "Courier Two", "courier2@onlineshop.kz", generate_password_hash("Courier234", method="pbkdf2:sha256"))
c2, _ = c, db
c2 = create_app(database=db).test_client()
login(c2, "courier2@onlineshop.kz", "Courier234")
r = c2.post("/courier/take/5", follow_redirects=True).data.decode()
check("K3", "Second courier takes the same order", "already taken" in r and
      one(db, "SELECT COUNT(*) FROM Deliveries WHERE order_id = 5") == 1, "rejected: already taken (UNIQUE)")

r = c.post("/courier/take/4", follow_redirects=True).data.decode()
check("K4", "Courier takes unpaid order 4", "only paid orders" in r and
      one(db, "SELECT COUNT(*) FROM Deliveries WHERE order_id = 4") == 0, "rejected: order is pending")

r = c2.post("/courier/delivered/5", follow_redirects=True).data.decode()
check("K5", "Another courier marks order 5 delivered", "not on the way with you" in r and
      one(db, "SELECT status FROM Deliveries WHERE order_id = 5") == "on_the_way", "rejected")

c.post("/courier/delivered/5")
check("K6", "Courier marks own order 5 delivered",
      one(db, "SELECT status FROM Deliveries WHERE order_id = 5") == "delivered" and
      one(db, "SELECT delivered_at FROM Deliveries WHERE order_id = 5") is not None, "delivered, time saved")

# the customer sees the delivery status on the order page
c3 = create_app(database=db).test_client()
c3.post("/register", data=dict(full_name="Test Buyer", email="buyer@example.com", phone="",
                               address="Almaty, Abay ave 10", password="secret123", password2="secret123"))
c3.post("/order/1", data={"quantity": "1", "order_token": "t-k7"})
oid = one(db, "SELECT MAX(order_id) FROM Orders")
c3.post(f"/orders/{oid}/pay", data={"method": "card", "bank_answer": "approved"})
before = c3.get(f"/orders/{oid}").data.decode()
c.post(f"/courier/take/{oid}")
after = c3.get(f"/orders/{oid}").data.decode()
check("K7", "Customer sees the delivery status", "waiting for a courier" in before and "on the way" in after,
      "paid: waiting for a courier → on the way")

r1 = c3.get("/courier/")
mgr = create_app(database=db).test_client()
login(mgr, "manager@onlineshop.kz", "Manager123")
r2 = mgr.get("/courier/")
check("K8", "Customer and manager open /courier", r1.status_code == 403 and r2.status_code == 403,
      f"customer {r1.status_code}, manager {r2.status_code}")

print(f"{'test':<6}{'case':<44}{'result':<8}details")
for t in results:
    print(f"{t[0]:<6}{t[1]:<44}{t[2]:<8}{t[3]}")
print(f"\n{sum(t[2] == 'PASS' for t in results)} of {len(results)} tests passed")

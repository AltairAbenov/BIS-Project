"""
Tests for staff accounts, roles and the manager dashboard
(owner: Shointay Aigerim, week 13 - manager account).
Each test runs the real website on a fresh temporary database (shop.db is not changed).
Run from the project folder:  python tests/test_manager_account.py
"""
import atexit
import os
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
    """A fresh copy of the website with its own database file."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    os.remove(path)
    atexit.register(lambda: os.path.exists(path) and os.remove(path))
    app = create_app(database=path)
    app.config["TESTING"] = True
    return app.test_client(), path


def login(client, email, password):
    return client.post("/login", data={"email": email, "password": password})


def sql(path, query, *args):
    con = sqlite3.connect(path)
    con.execute(query, args)
    con.commit()
    con.close()


MANAGER = ("manager@onlineshop.kz", "Manager123")
COURIER = ("courier@onlineshop.kz", "Courier123")

# M1: the manager logs in and lands on the dashboard
c, db = new_site()
r = login(c, *MANAGER)
page = c.get("/manager/")
check("M1", "Manager logs in", r.headers.get("Location", "").endswith("/manager/") and b"Manager dashboard" in page.data,
      f"redirect to {r.headers.get('Location')}, dashboard {page.status_code}")

# M2: wrong password
c, db = new_site()
r = login(c, MANAGER[0], "wrong-pass")
check("M2", "Manager with a wrong password", b"Wrong email or password" in r.data, "error shown, not logged in")

# M3: a guest opens the dashboard
c, db = new_site()
r = c.get("/manager/")
check("M3", "Guest opens /manager", r.status_code == 302 and "/login" in r.headers["Location"],
      f"{r.status_code} -> {r.headers.get('Location')}")

# M4: a customer opens the dashboard
c, db = new_site()
c.post("/register", data=dict(full_name="Test Buyer", email="buyer@example.com", phone="",
                              address="Almaty, Abay ave 10", password="secret123", password2="secret123"))
r = c.get("/manager/")
check("M4", "Customer opens /manager", r.status_code == 403 and b"Access denied" in r.data, f"HTTP {r.status_code}, Access denied")

# M5: a courier opens the dashboard
c, db = new_site()
login(c, *COURIER)
r = c.get("/manager/")
check("M5", "Courier opens /manager", r.status_code == 403, f"HTTP {r.status_code}")

# M6: filter "Unpaid only"
c, db = new_site()
login(c, *MANAGER)
html = c.get("/manager/?status=unpaid").data.decode()
shown = [n for n in range(1, 8) if f">#{n}<" in html]
check("M6", "Filter: unpaid only", shown == [4, 6], f"orders shown: {shown}")

# M7: the manager sees any order with its payment attempts
c, db = new_site()
login(c, *MANAGER)
html = c.get("/manager/orders/3").data.decode()
check("M7", "Manager opens order 3", "Payment attempts (2)" in html and "Customer Three" in html,
      "order of another customer is visible to the manager with 2 attempts")

# M8: a disabled manager cannot log in, and loses access at once
c, db = new_site()
login(c, *MANAGER)
sql(db, "UPDATE Staff SET is_active = 0 WHERE email = ?", MANAGER[0])
r1 = c.get("/manager/")
r2 = login(c, *MANAGER)
check("M8", "Account disabled by the admin", r1.status_code == 302 and b"disabled" in r2.data,
      "open page -> logged out; new login -> 'account is disabled'")

# M9: a customer cannot register with a staff email
c, db = new_site()
r = c.post("/register", data=dict(full_name="Fake Manager", email="manager@onlineshop.kz", phone="",
                                  address="Almaty, Abay ave 10", password="secret123", password2="secret123"))
check("M9", "Register with a staff email", b"already registered" in r.data, "rejected by the database trigger")

# M10: a manager cannot place an order
c, db = new_site()
login(c, *MANAGER)
r = c.post("/order/1", data={"quantity": "1"})
check("M10", "Manager tries to place an order", r.status_code == 302 and "/manager/" in r.headers["Location"],
      f"redirected to {r.headers.get('Location')}")

print(f"{'test':<6}{'case':<36}{'result':<8}details")
for t in results:
    print(f"{t[0]:<6}{t[1]:<36}{t[2]:<8}{t[3]}")
print(f"\n{sum(t[2] == 'PASS' for t in results)} of {len(results)} tests passed")

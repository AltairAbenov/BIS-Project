"""
Tests for the manager profile (owner: Yeleussizova Zhannur, week 13).
Each test runs the real website on a fresh temporary database (shop.db is not changed).
Run from the project folder:  python tests/test_manager_profile.py
"""
import atexit
import os
import sqlite3
import sys
import tempfile
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from shop import create_app  # noqa: E402
from shop.profile.profile import manager_summary  # noqa: E402

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


def client(app, email=None, password=None):
    c = app.test_client()
    if email:
        c.post("/login", data={"email": email, "password": password})
    return c


def one(path, query, *args):
    con = sqlite3.connect(path)
    row = con.execute(query, args).fetchone()
    con.close()
    return row[0] if row else None


MANAGER = ("manager@onlineshop.kz", "Manager123")
URL = "/manager/profile/"

# P1: the manager opens the profile with the shop summary
app, db = new_site()
m = client(app, *MANAGER)
page = m.get(URL).data.decode()
check("P1", "Manager opens the profile", "Main Manager" in page and "Orders today" in page and "Change password" in page,
      "details, shop summary and password form shown")

# P2: a courier opens their own profile - no shop summary
page = client(app, "courier@onlineshop.kz", "Courier123").get(URL).data.decode()
check("P2", "Courier opens own profile", "Courier One" in page and "Orders today" not in page,
      "own details only, no shop numbers")

# P3: change name and phone
r = m.post(URL + "details", data={"full_name": "Dana  Manager", "phone": "8 (702) 555-44-33"})
page = m.get(URL).data.decode()
check("P3", "Change name and phone", r.status_code == 302 and
      one(db, "SELECT full_name FROM Staff WHERE email = ?", MANAGER[0]) == "Dana Manager" and
      one(db, "SELECT phone FROM Staff WHERE email = ?", MANAGER[0]) == "+7 702 555 44 33" and "Hello, Dana Manager" in page,
      "saved; phone normalised; greeting in the top bar updated")

# P4: wrong name and phone
r = m.post(URL + "details", data={"full_name": "Dana123", "phone": "12345"})
check("P4", "Name with digits, wrong phone", r.status_code == 400 and b"Letters only" in r.data and b"Kazakhstan number" in r.data,
      "both errors shown, nothing saved")

# P5: wrong current password
r = m.post(URL + "password", data={"current": "nope", "new": "NewPass2026", "repeat": "NewPass2026"})
check("P5", "Wrong current password", r.status_code == 400 and b"current password is wrong" in r.data, "rejected")

# P6: weak new password
r = m.post(URL + "password", data={"current": MANAGER[1], "new": "short", "repeat": "short"})
check("P6", "Weak new password", r.status_code == 400 and b"8+ characters" in r.data, "rejected")

# P7: new passwords do not match
r = m.post(URL + "password", data={"current": MANAGER[1], "new": "NewPass2026", "repeat": "NewPass2025"})
check("P7", "New passwords do not match", r.status_code == 400 and b"do not match" in r.data, "rejected")

# P8: successful change: the old password stops working, the new one works
r = m.post(URL + "password", data={"current": MANAGER[1], "new": "NewPass2026", "repeat": "NewPass2026"})
old = client(app).post("/login", data={"email": MANAGER[0], "password": MANAGER[1]})
new = client(app).post("/login", data={"email": MANAGER[0], "password": "NewPass2026"})
check("P8", "Change the password", r.status_code == 302 and b"Wrong email or password" in old.data and new.status_code == 302,
      "old password rejected, new password works")

# P9: a guest and a customer cannot open the profile page
g = client(app).get(URL)
c = client(app)
c.post("/register", data=dict(full_name="Test Buyer", email="buyer@example.com", phone="",
                              address="Almaty, Abay ave 10", password="secret123", password2="secret123"))
check("P9", "Guest and customer open the profile", g.status_code == 302 and c.get(URL).status_code == 403,
      f"guest {g.status_code} (to login), customer 403")

# P10: the summary numbers are correct (test data of October 2026)
con = sqlite3.connect(db)
con.row_factory = sqlite3.Row
s = manager_summary(con, today=date(2026, 10, 15))
con.close()
expected = {"orders_month": 7, "revenue_month": 166000, "unpaid": 2, "failed_attempts": 2, "top_product": "Wireless Mouse"}
got = {k: s[k] for k in expected}
check("P10", "Summary numbers for October", got == expected,
      f"7 orders, 166 000 ₸ paid, 2 unpaid, 2 failed attempts, bestseller Wireless Mouse ({s['top_sold']} sold)")

print(f"{'test':<6}{'case':<36}{'result':<8}details")
for t in results:
    print(f"{t[0]:<6}{t[1]:<36}{t[2]:<8}{t[3]}")
print(f"\n{sum(t[2] == 'PASS' for t in results)} of {len(results)} tests passed")

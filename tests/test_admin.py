"""
Tests for the admin page and access by role (owner: Bakyt Aiganym, week 13 - admin).
Each test runs the real website on a fresh temporary database (shop.db is not changed).
Run from the project folder:  python tests/test_admin.py
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


ADMIN = ("admin@onlineshop.kz", "Admin123")
MANAGER = ("manager@onlineshop.kz", "Manager123")
NEW = dict(full_name="Dana Courier", email="dana@onlineshop.kz", phone="87017778899",
           role="courier", password="Start2026")

# AD1: the admin logs in and sees all staff accounts
app, db = new_site()
admin = client(app, *ADMIN)
page = admin.get("/admin/").data.decode()
check("AD1", "Admin opens the staff list", all(e in page for e in ("admin@onlineshop.kz", "manager@onlineshop.kz", "courier@onlineshop.kz")),
      "3 demo accounts listed")

# AD2: create a courier; the courier can log in with the temporary password
r = admin.post("/admin/staff/new", data=NEW)
courier = client(app)
r2 = courier.post("/login", data={"email": NEW["email"], "password": NEW["password"]})
check("AD2", "Create a courier account", r.status_code == 302 and
      one(db, "SELECT role FROM Staff WHERE email = ?", NEW["email"]) == "courier" and r2.status_code == 302 and
      one(db, "SELECT phone FROM Staff WHERE email = ?", NEW["email"]) == "+7 701 777 88 99",
      "saved, phone normalised, the new courier can log in")

# AD3: the same email again
r = admin.post("/admin/staff/new", data=NEW)
check("AD3", "Same staff email again", r.status_code == 400 and b"already used" in r.data, "rejected (UNIQUE)")

# AD4: an email that belongs to a customer
r = admin.post("/admin/staff/new", data={**NEW, "email": "user01@example.com"})
check("AD4", "Email of a customer", r.status_code == 400 and b"already used" in r.data, "rejected by the database trigger")

# AD5: wrong name and weak password
r = admin.post("/admin/staff/new", data={**NEW, "email": "x@onlineshop.kz", "full_name": "Dana 2", "password": "password"})
check("AD5", "Name with a digit, weak password", r.status_code == 400 and b"Letters only" in r.data and b"8+ characters" in r.data,
      "both errors shown, nothing saved")

# AD6: trying to create an admin with a crafted request
r = admin.post("/admin/staff/new", data={**NEW, "email": "boss@onlineshop.kz", "role": "admin"})
check("AD6", "Create an admin from the website", r.status_code == 400 and
      one(db, "SELECT COUNT(*) FROM Staff WHERE role = 'admin'") == 1, "rejected: only manager or courier")

# AD7: disable the manager -> cannot log in, a logged-in manager loses access
manager = client(app, *MANAGER)
mid = one(db, "SELECT staff_id FROM Staff WHERE email = ?", MANAGER[0])
admin.post(f"/admin/staff/{mid}/disable")
r1 = manager.get("/manager/")
r2 = client(app).post("/login", data={"email": MANAGER[0], "password": MANAGER[1]})
check("AD7", "Disable the manager", r1.status_code == 302 and b"disabled" in r2.data,
      "the open session is closed; new login: 'account is disabled'")

# AD8: enable again
admin.post(f"/admin/staff/{mid}/enable")
r = client(app).post("/login", data={"email": MANAGER[0], "password": MANAGER[1]})
check("AD8", "Enable the manager again", r.status_code == 302 and "/manager" in r.headers["Location"], "can log in again")

# AD9: the admin cannot disable their own account
aid = one(db, "SELECT staff_id FROM Staff WHERE role = 'admin'")
r = admin.post(f"/admin/staff/{aid}/disable", follow_redirects=True)
check("AD9", "Admin disables own account", b"cannot disable your own" in r.data and
      one(db, "SELECT is_active FROM Staff WHERE staff_id = ?", aid) == 1, "rejected")

# AD10: other roles cannot open the admin page
codes = {
    "guest": client(app).get("/admin/").status_code,
    "manager": client(app, *MANAGER).get("/admin/").status_code,
    "courier": client(app, "courier@onlineshop.kz", "Courier123").get("/admin/").status_code,
}
cust = client(app)
cust.post("/register", data=dict(full_name="Test Buyer", email="buyer@example.com", phone="",
                                 address="Almaty, Abay ave 10", password="secret123", password2="secret123"))
codes["customer"] = cust.get("/admin/").status_code
check("AD10", "Other roles open /admin", codes == {"guest": 302, "manager": 403, "courier": 403, "customer": 403},
      ", ".join(f"{k} {v}" for k, v in codes.items()))

# AD11: a customer cannot create staff accounts with a crafted request
r = cust.post("/admin/staff/new", data={**NEW, "email": "hack@onlineshop.kz"})
check("AD11", "Customer sends the admin form", r.status_code == 403 and
      one(db, "SELECT COUNT(*) FROM Staff WHERE email = 'hack@onlineshop.kz'") == 0, "403, nothing saved")

print(f"{'test':<6}{'case':<36}{'result':<8}details")
for t in results:
    print(f"{t[0]:<6}{t[1]:<36}{t[2]:<8}{t[3]}")
print(f"\n{sum(t[2] == 'PASS' for t in results)} of {len(results)} tests passed")

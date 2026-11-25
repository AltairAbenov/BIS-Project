"""
Tests for uniqueness rules and product features (owner: Shointay Aigerim, week 12).
Every test uses a fresh in-memory copy of the database, so shop.db is not changed.
Run from the project folder:  python tests/test_uniqueness.py
"""
import os
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from shop.db import schema_files  # noqa: E402
from shop.catalog.catalog import CatalogError, add_feature, add_product, get_features, new_order_token  # noqa: E402
from shop.customer.orders import place_order  # noqa: E402


def fresh_db():
    db = sqlite3.connect(":memory:")
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    for path in schema_files(ROOT):
        with open(path, encoding="utf-8") as f:
            db.executescript(f.read())
    return db


def count(db, sql, *args):
    return db.execute(sql, args).fetchone()[0]


results = []


def check(test_id, name, ok, actual):
    results.append((test_id, name, "PASS" if ok else "FAIL", actual))


# U1: the same product name again (different letter case)
db = fresh_db()
try:
    add_product(db, "wireless MOUSE", "Accessories", 9000, 10)
    check("U1", "Add 'wireless MOUSE' again", False, "accepted - duplicate product")
except CatalogError as e:
    check("U1", "Add 'wireless MOUSE' again", count(db, "SELECT COUNT(*) FROM Products") == 5, f"rejected: {e}")

# U2: a new product with a new name is accepted
db = fresh_db()
pid = add_product(db, "Laptop Stand", "Accessories", 9900, 20)
check("U2", "Add a new product 'Laptop Stand'", count(db, "SELECT COUNT(*) FROM Products") == 6,
      f"saved as product #{pid}")

# U3: the same feature twice for one product
db = fresh_db()
try:
    add_feature(db, 1, "warranty", "24 months")
    check("U3", "Second 'Warranty' for the mouse", False, "accepted - duplicate feature")
except CatalogError as e:
    check("U3", "Second 'Warranty' for the mouse", len(get_features(db, 1)) == 3, f"rejected: {e}")

# U4: the same feature name for ANOTHER product is fine
db = fresh_db()
add_feature(db, 2, "Colour", "Grey")
add_feature(db, 3, "Colour", "Black")
check("U4", "'Colour' for two different products", count(db, "SELECT COUNT(*) FROM Product_Features WHERE feature_name = 'Colour'") == 2,
      "both saved: the rule is per product")

# U5: double click - the same order form (same token) is sent twice
db = fresh_db()
token = new_order_token()
o1, dup1 = place_order(db, 1, 1, "2", token=token)
o2, dup2 = place_order(db, 1, 1, "2", token=token)
stock = count(db, "SELECT stock_qty FROM Products WHERE product_id = 1")
check("U5", "Same order form sent twice", o1 == o2 and not dup1 and dup2 and stock == 38,
      f"one order #{o1}, second request returned it again; stock 40 -> {stock} (reduced once)")

# U6: two different forms are two real orders
db = fresh_db()
a, _ = place_order(db, 1, 1, "1", token=new_order_token())
b, _ = place_order(db, 1, 1, "1", token=new_order_token())
check("U6", "Two different order forms", a != b and count(db, "SELECT stock_qty FROM Products WHERE product_id = 1") == 38,
      f"two orders #{a} and #{b}")

# U7: features are shown for every product
db = fresh_db()
n = [len(get_features(db, p)) for p in range(1, 6)]
check("U7", "Every product has features", all(x >= 3 for x in n), f"features per product: {n}")

print(f"{'test':<6}{'case':<36}{'result':<8}details")
for r in results:
    print(f"{r[0]:<6}{r[1]:<36}{r[2]:<8}{r[3]}")
print(f"\n{sum(r[2] == 'PASS' for r in results)} of {len(results)} tests passed")

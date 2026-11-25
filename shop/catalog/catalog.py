"""
Uniqueness rules and product features (owner: Shointay Aigerim, week 12).

- Product names are unique (UNIQUE COLLATE NOCASE in schema.sql):
  "Wireless Mouse" and "wireless mouse" cannot both exist.
- A feature cannot repeat for one product: UNIQUE (product_id, feature_name).
- One order form = one order: every form gets a one-time order_token,
  and Orders.order_token is UNIQUE, so a double click cannot create two orders.
"""
import sqlite3
import uuid


class CatalogError(Exception):
    """Raised when a product or a feature breaks a uniqueness rule."""


def get_features(db, product_id):
    """All features of one product, e.g. [("Warranty", "12 months"), ...]."""
    return db.execute(
        "SELECT feature_name, feature_value FROM Product_Features "
        "WHERE product_id = ? ORDER BY feature_id",
        (product_id,),
    ).fetchall()


def add_product(db, name, category, price, stock_qty):
    """Add a product to the catalog. A second product with the same name is rejected."""
    try:
        cur = db.execute(
            "INSERT INTO Products (name, category, price, stock_qty) VALUES (?, ?, ?, ?)",
            (name.strip(), category.strip(), price, stock_qty),
        )
        db.commit()
    except sqlite3.IntegrityError as e:
        db.rollback()
        if "UNIQUE" in str(e):
            raise CatalogError(f"A product called '{name.strip()}' already exists.") from e
        raise CatalogError(f"The product breaks a database rule: {e}") from e
    return cur.lastrowid


def add_feature(db, product_id, feature_name, feature_value):
    """Add one feature to a product. The same feature name twice is rejected."""
    try:
        cur = db.execute(
            "INSERT INTO Product_Features (product_id, feature_name, feature_value) VALUES (?, ?, ?)",
            (product_id, feature_name.strip(), feature_value.strip()),
        )
        db.commit()
    except sqlite3.IntegrityError as e:
        db.rollback()
        if "UNIQUE" in str(e):
            raise CatalogError(f"Product {product_id} already has the feature '{feature_name.strip()}'.") from e
        raise CatalogError(f"The feature breaks a database rule: {e}") from e
    return cur.lastrowid


def new_order_token():
    """A one-time token for one order form (a random UUID, 36 characters)."""
    return str(uuid.uuid4())


def find_order_by_token(db, token, customer_id):
    """The order already created from this form, or None."""
    row = db.execute(
        "SELECT order_id FROM Orders WHERE order_token = ? AND customer_id = ?",
        (token, customer_id),
    ).fetchone()
    return row[0] if row else None

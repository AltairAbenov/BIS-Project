"""
Ratings and feedback (owner: Abenov Altair, week 12).

Rules:
- rating is a whole number from 1 to 5 (CHECK in the database too)
- comment is optional, up to 500 characters
- only a customer who has a PAID order with this product can write a review
- one review per customer per product (UNIQUE (product_id, customer_id))
"""
import sqlite3
from datetime import datetime


class ReviewError(Exception):
    """Raised when the review cannot be saved; the message is shown to the customer."""


def rating_summary(db):
    """{product_id: (average rating, number of reviews)} for the catalog."""
    rows = db.execute(
        "SELECT product_id, ROUND(AVG(rating), 1), COUNT(*) FROM Reviews GROUP BY product_id"
    ).fetchall()
    return {r[0]: (r[1], r[2]) for r in rows}


def product_reviews(db, product_id):
    """Reviews of one product, newest first.
    The author is shown as first name + first letter of the surname ("Aigerim S.") for privacy."""
    rows = db.execute(
        "SELECT r.rating, r.comment, substr(r.created_at, 1, 10) AS day, c.full_name "
        "FROM Reviews r JOIN Customers c ON c.customer_id = r.customer_id "
        "WHERE r.product_id = ? ORDER BY r.created_at DESC",
        (product_id,),
    ).fetchall()
    return [
        {"rating": r["rating"], "comment": r["comment"], "day": r["day"], "author": short_name(r["full_name"])}
        for r in rows
    ]


def short_name(full_name):
    parts = full_name.split()
    return parts[0] + (f" {parts[1][0]}." if len(parts) > 1 else "")


def has_paid_purchase(db, customer_id, product_id):
    return db.execute(
        "SELECT 1 FROM Orders o JOIN Order_Items oi ON oi.order_id = o.order_id "
        "WHERE o.customer_id = ? AND oi.product_id = ? AND o.payment_status = 'paid' LIMIT 1",
        (customer_id, product_id),
    ).fetchone() is not None


def review_status(db, customer_id, product_id):
    """What the product page shows in the review block:
    'guest' - not logged in; 'not_bought' - no paid order with this product;
    'done' - already reviewed; 'can' - the review form is shown."""
    if customer_id is None:
        return "guest"
    if db.execute(
        "SELECT 1 FROM Reviews WHERE customer_id = ? AND product_id = ?", (customer_id, product_id)
    ).fetchone():
        return "done"
    if not has_paid_purchase(db, customer_id, product_id):
        return "not_bought"
    return "can"


def add_review(db, customer_id, product_id, raw_rating, comment):
    """Save one review. Returns the new review_id."""
    raw_rating = (raw_rating or "").strip()
    if raw_rating not in {"1", "2", "3", "4", "5"}:
        raise ReviewError("Choose a rating from 1 to 5 stars.")
    comment = (comment or "").strip()
    if len(comment) > 500:
        raise ReviewError("The comment can have at most 500 characters.")
    if not has_paid_purchase(db, customer_id, product_id):
        raise ReviewError("Only customers who bought and paid for this product can leave a review.")
    try:
        cur = db.execute(
            "INSERT INTO Reviews (product_id, customer_id, rating, comment, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (product_id, customer_id, int(raw_rating), comment or None,
             datetime.now().strftime("%Y-%m-%d %H:%M")),
        )
        db.commit()
    except sqlite3.IntegrityError as e:
        db.rollback()
        if "UNIQUE" in str(e):
            raise ReviewError("You have already reviewed this product.") from e
        raise ReviewError("The review could not be saved.") from e
    return cur.lastrowid

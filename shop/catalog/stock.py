"""
Quantity checks and warehouse stock (owner: Shointay Aigerim).

parse_quantity()  - checks what the customer typed in the "Quantity" field
take_from_stock() - reduces Products.stock_qty when an order is placed
return_to_stock() - week 12: puts items back when an order is cancelled
"""


class StockError(Exception):
    """Raised when the warehouse does not have enough items."""


def parse_quantity(raw, stock_qty):
    """Check the quantity typed by the customer.

    Returns (quantity, None) if it is correct, or (None, error message) if not.
    Rules:
      - must be a whole number (not empty, no letters, no 1.5, no -2)
      - must be at least 1
      - the product must be in stock
      - must not be more than the stock left in the warehouse
    """
    raw = (raw or "").strip()
    if stock_qty <= 0:
        return None, "This product is out of stock."
    if not raw.isdigit():
        return None, "Quantity must be a whole number, for example 1 or 2."
    qty = int(raw)
    if qty < 1:
        return None, "Quantity must be at least 1."
    if qty > stock_qty:
        return None, f"Only {stock_qty} left in stock. Choose a smaller quantity."
    return qty, None


def take_from_stock(db, product_id, qty):
    """Reduce the stock of one product by qty.

    The condition "stock_qty >= ?" is checked inside the same UPDATE,
    so two customers cannot buy the last item at the same time.
    The database CHECK (stock_qty >= 0) is a second safety net.
    """
    cur = db.execute(
        "UPDATE Products SET stock_qty = stock_qty - ? "
        "WHERE product_id = ? AND stock_qty >= ?",
        (qty, product_id, qty),
    )
    if cur.rowcount != 1:
        raise StockError("Not enough items in stock.")


def return_to_stock(db, product_id, qty):
    """Week 12: put items back into the warehouse when an order is cancelled.
    Used by cancel_order() in app.py; it runs inside the same transaction."""
    db.execute(
        "UPDATE Products SET stock_qty = stock_qty + ? WHERE product_id = ?",
        (qty, product_id),
    )

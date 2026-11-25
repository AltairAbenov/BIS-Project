"""
Search, filters and sorting on the main page (owner: Abenov Altair, week 13).

- every word of the search must be found in the product name, the category
  OR one of its features: "bluetooth" finds the mouse, "usb-c 1tb" finds the SSD
- price range "from - to" in tenge, "in stock only"
- sorting: best rated, bestsellers (units sold in paid orders), price, name
All values go into SQL as parameters (?), never glued into the query text.
"""

SORTS = {
    "popular": ("Best rated", "rating_avg DESC, rating_count DESC, p.name"),
    "bestsellers": ("Bestsellers", "sold DESC, rating_avg DESC, p.name"),
    "price_asc": ("Price: low to high", "p.price ASC, p.name"),
    "price_desc": ("Price: high to low", "p.price DESC, p.name"),
    "name": ("Name A–Z", "p.name"),
}


def parse_price(raw):
    """'12 000' -> 12000; empty or wrong -> None."""
    digits = "".join(ch for ch in (raw or "") if ch.isdigit())
    return int(digits) if digits else None


def read_filters(args):
    """Read the search form from the URL (request.args)."""
    f = {
        "q": args.get("q", "").strip(),
        "category": args.get("category", ""),
        "min_price": parse_price(args.get("min_price")),
        "max_price": parse_price(args.get("max_price")),
        "in_stock": args.get("in_stock") == "1",
        "sort": args.get("sort", "popular"),
        "note": None,
    }
    if f["sort"] not in SORTS:
        f["sort"] = "popular"
    if f["min_price"] is not None and f["max_price"] is not None and f["min_price"] > f["max_price"]:
        f["min_price"], f["max_price"] = f["max_price"], f["min_price"]
        f["note"] = "“From” was bigger than “to”, so the prices were swapped."
    return f


def search_products(db, f):
    sql = (
        "SELECT p.product_id, p.name, p.category, p.price, p.stock_qty, "
        "  COALESCE((SELECT ROUND(AVG(r.rating), 1) FROM Reviews r WHERE r.product_id = p.product_id), 0) AS rating_avg, "
        "  (SELECT COUNT(*) FROM Reviews r WHERE r.product_id = p.product_id) AS rating_count, "
        "  COALESCE((SELECT SUM(oi.quantity) FROM Order_Items oi JOIN Orders o ON o.order_id = oi.order_id "
        "            WHERE oi.product_id = p.product_id AND o.payment_status = 'paid'), 0) AS sold "
        "FROM Products p WHERE 1 = 1 "
    )
    params = []
    for word in f["q"].split():
        like = f"%{word}%"
        sql += ("AND (p.name LIKE ? OR p.category LIKE ? OR EXISTS ("
                "SELECT 1 FROM Product_Features pf WHERE pf.product_id = p.product_id "
                "AND (pf.feature_value LIKE ? OR pf.feature_name LIKE ?))) ")
        params += [like, like, like, like]
    if f["category"]:
        sql += "AND p.category = ? "
        params.append(f["category"])
    if f["min_price"] is not None:
        sql += "AND p.price >= ? "
        params.append(f["min_price"])
    if f["max_price"] is not None:
        sql += "AND p.price <= ? "
        params.append(f["max_price"])
    if f["in_stock"]:
        sql += "AND p.stock_qty > 0 "
    sql += "ORDER BY " + SORTS[f["sort"]][1]  # only texts from SORTS are used here
    return db.execute(sql, params).fetchall()


def matched_feature(db, product_id, q):
    """Why a product was found when the word is not in its name, e.g. 'Connection: Bluetooth 5.1'."""
    for word in q.split():
        row = db.execute(
            "SELECT feature_name, feature_value FROM Product_Features "
            "WHERE product_id = ? AND (feature_value LIKE ? OR feature_name LIKE ?) LIMIT 1",
            (product_id, f"%{word}%", f"%{word}%"),
        ).fetchone()
        if row:
            return f"{row[0]}: {row[1]}"
    return None

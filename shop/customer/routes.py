"""
Pages of the customer side (owner: Abenov Altair).
"""
import re
import sqlite3

from flask import abort, flash, redirect, render_template, request, session, url_for
from werkzeug.security import generate_password_hash

from ..auth import login_required, start_customer_session
from ..catalog.catalog import get_features, new_order_token
from ..db import get_db
from ..payments.payments import payment_history
from . import bp
from .orders import OrderError, get_order, get_product, list_orders, place_order
from .reviews import ReviewError, add_review, product_reviews, rating_summary, review_status

# ---------- main page: search, filter, sort (owner: Abenov Altair) ----------

SORTS = {
    "popular": "rating_avg DESC, rating_count DESC, p.name",
    "price_asc": "p.price ASC",
    "price_desc": "p.price DESC",
    "name": "p.name",
}


@bp.route("/")
def index():
    db = get_db()
    q = request.args.get("q", "").strip()
    category = request.args.get("category", "")
    sort = request.args.get("sort", "popular")
    if sort not in SORTS:
        sort = "popular"

    sql = (
        "SELECT p.product_id, p.name, p.category, p.price, p.stock_qty, "
        "       COALESCE(ROUND(AVG(r.rating), 1), 0) AS rating_avg, COUNT(r.review_id) AS rating_count "
        "FROM Products p LEFT JOIN Reviews r ON r.product_id = p.product_id WHERE 1 = 1 "
    )
    params = []
    if q:
        sql += "AND p.name LIKE ? "          # value is passed as a parameter, not glued into SQL
        params.append(f"%{q}%")
    if category:
        sql += "AND p.category = ? "
        params.append(category)
    sql += "GROUP BY p.product_id ORDER BY " + SORTS[sort]  # only names from SORTS are used

    products = db.execute(sql, params).fetchall()
    categories = [r[0] for r in db.execute("SELECT DISTINCT category FROM Products ORDER BY category")]
    return render_template("customer/index.html", products=products, categories=categories,
                           q=q, category=category, sort=sort)


# ---------- product page: features, rating, reviews, order form ----------

def render_product(product_id, error=None, qty="1", status=200):
    db = get_db()
    product = get_product(db, product_id)
    if product is None:
        abort(404)
    customer_id = session.get("customer_id")
    address = None
    token = None
    if customer_id:
        address = db.execute("SELECT address FROM Customers WHERE customer_id = ?",
                             (customer_id,)).fetchone()["address"]
        token = new_order_token()  # one form = one order (see catalog.py)
    avg, count = rating_summary(db).get(product_id, (0, 0))
    return render_template(
        "customer/product.html", product=product, features=get_features(db, product_id),
        reviews=product_reviews(db, product_id), rating_avg=avg, rating_count=count,
        review_state=review_status(db, customer_id, product_id),
        address=address, token=token, qty=qty, error=error,
    ), status


@bp.route("/product/<int:product_id>")
def product_page(product_id):
    return render_product(product_id)


@bp.route("/order/<int:product_id>", methods=["GET", "POST"])
@login_required
def order(product_id):
    if request.method == "GET":
        return redirect(url_for(".product_page", product_id=product_id))
    qty = request.form.get("quantity", "1")
    try:
        order_id, duplicate = place_order(get_db(), session["customer_id"], product_id, qty,
                                          token=request.form.get("order_token"))
    except OrderError as e:
        return render_product(product_id, error=str(e), qty=qty)
    if duplicate:
        flash(f"This form was already sent, so no second order was created. Here is order #{order_id}.", "info")
    else:
        flash(f"Order #{order_id} is placed. You can pay for it now.", "success")
    return redirect(url_for(".order_detail", order_id=order_id))


@bp.route("/product/<int:product_id>/review", methods=["POST"])
@login_required
def review(product_id):
    try:
        add_review(get_db(), session["customer_id"], product_id,
                   request.form.get("rating"), request.form.get("comment"))
    except ReviewError as e:
        flash(str(e), "error")
    else:
        flash("Thank you! Your review is published.", "success")
    return redirect(url_for(".product_page", product_id=product_id) + "#reviews")


# ---------- registration and login (owner: Abenov Altair) ----------

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
NAME_RE = re.compile(r"^[^\W\d_]+(?:[ '\-][^\W\d_]+)*$")  # letters of any alphabet, spaces, - and '


def normalize_phone(raw):
    """'87011234567' or '+7 (701) 123-45-67' -> '+7 701 123 45 67'; None if it is not a KZ number."""
    digits = re.sub(r"\D", "", raw)
    if len(digits) == 11 and digits[0] in "78":
        d = digits[1:]
        return f"+7 {d[:3]} {d[3:6]} {d[6:8]} {d[8:]}"
    return None


def validate(form):
    """Check the registration form before saving. Returns a dict {field: error message}."""
    errors = {}
    if not (2 <= len(form["full_name"]) <= 100) or not NAME_RE.match(form["full_name"]):
        errors["full_name"] = "Use letters only (Latin, Cyrillic or Kazakh), for example Aigerim Shointay."
    if not EMAIL_RE.match(form["email"]):
        errors["email"] = "Enter a valid email, for example name@example.com."
    if form["phone"]:
        phone = normalize_phone(form["phone"])
        if phone is None:
            errors["phone"] = "Enter a Kazakhstan number, for example +7 701 123 45 67."
        else:
            form["phone"] = phone
    if len(form["address"]) < 5:
        errors["address"] = "Enter your delivery address (city, street, house)."
    pw = form["password"]
    if len(pw) < 8 or not re.search(r"[^\W\d_]", pw) or not re.search(r"\d", pw):
        errors["password"] = "At least 8 characters, with at least one letter and one digit."
    elif pw != form["password2"]:
        errors["password2"] = "Passwords do not match."
    return errors


@bp.route("/register", methods=["GET", "POST"])
def register():
    fields = ["full_name", "email", "phone", "address", "password", "password2"]
    form = {f: request.form.get(f, "").strip() for f in fields}
    form["full_name"] = re.sub(r"\s+", " ", form["full_name"])
    errors = {}

    if request.method == "POST":
        form["email"] = form["email"].lower()
        errors = validate(form)
        if not errors:
            db = get_db()
            try:
                cur = db.execute(
                    "INSERT INTO Customers (full_name, email, phone, address, password_hash) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (form["full_name"], form["email"], form["phone"] or None,
                     form["address"], generate_password_hash(form["password"])),
                )
                db.commit()
            except sqlite3.IntegrityError as e:
                # The database rules (UNIQUE / CHECK) are the last line of defence
                if "UNIQUE" in str(e):
                    errors["email"] = "This email is already registered. Log in instead."
                else:
                    errors["email"] = "The data did not pass the database rules."
            else:
                start_customer_session(cur.lastrowid, form["full_name"])
                flash(f"Registration complete. Welcome, {form['full_name']}!", "success")
                return redirect(request.args.get("next") or url_for(".index"))

    form["password"] = form["password2"] = ""  # never send passwords back to the page
    return render_template("customer/register.html", form=form, errors=errors)


# ---------- orders ----------

@bp.route("/orders/<int:order_id>")
@login_required
def order_detail(order_id):
    db = get_db()
    order, items = get_order(db, order_id, session["customer_id"])
    if order is None:
        abort(404)  # the order does not exist or belongs to another customer
    return render_template("customer/order_detail.html", order=order, items=items,
                           payments=payment_history(db, order_id))


@bp.route("/orders")
@login_required
def my_orders():
    return render_template("customer/my_orders.html", orders=list_orders(get_db(), session["customer_id"]))

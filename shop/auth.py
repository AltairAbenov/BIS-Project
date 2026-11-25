"""
Log in, log out and access rules (week 10-12: customers only).
"""
from functools import wraps

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash

from .db import get_db

bp = Blueprint("auth", __name__)


def login_required(view):
    """Only logged-in customers can open the page."""
    @wraps(view)
    def wrapper(*args, **kwargs):
        if session.get("role") != "customer":
            flash("Please log in or register to continue.", "info")
            return redirect(url_for("auth.login", next=request.path))
        return view(*args, **kwargs)
    return wrapper


def start_customer_session(customer_id, name):
    session.clear()
    session["role"] = "customer"
    session["customer_id"] = customer_id
    session["name"] = name


@bp.route("/login", methods=["GET", "POST"])
def login():
    email = request.form.get("email", "").strip().lower()
    error = None
    if request.method == "POST":
        row = get_db().execute(
            "SELECT customer_id, full_name, password_hash FROM Customers WHERE email = ?", (email,)
        ).fetchone()
        if row and row["password_hash"] and check_password_hash(row["password_hash"], request.form.get("password", "")):
            start_customer_session(row["customer_id"], row["full_name"])
            flash(f"Welcome back, {row['full_name']}.", "success")
            return redirect(request.args.get("next") or url_for("customer.index"))
        error = "Wrong email or password."
    return render_template("auth/login.html", email=email, error=error)


@bp.route("/logout")
def logout():
    session.clear()
    flash("You have logged out.", "info")
    return redirect(url_for("customer.index"))

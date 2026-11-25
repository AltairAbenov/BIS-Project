"""
Log in, log out and access rules.
Week 10-12: customers only.
Week 13 (Shointay Aigerim - manager account): staff accounts with roles
(manager, courier, admin), one login page for everybody, role_required().
"""
from functools import wraps

from flask import (Blueprint, abort, flash, redirect, render_template, request, session,
                   url_for)
from werkzeug.routing import BuildError
from werkzeug.security import check_password_hash

from .db import get_db

bp = Blueprint("auth", __name__)

STAFF_ROLES = ("manager", "courier", "admin")

# where each role lands after logging in
HOME_BY_ROLE = {
    "customer": "customer.index",
    "manager": "manager.dashboard",
    "courier": "courier.deliveries",
    "admin": "admin.staff_list",
}


def home_url(role):
    try:
        return url_for(HOME_BY_ROLE.get(role, "customer.index"))
    except BuildError:  # that part of the site is not merged yet
        return url_for("customer.index")


def login_required(view):
    """Only logged-in customers can open the page (ordering, paying, reviews)."""
    @wraps(view)
    def wrapper(*args, **kwargs):
        role = session.get("role")
        if role in STAFF_ROLES:
            flash("This page is for customers. Staff accounts cannot place orders.", "info")
            return redirect(home_url(role))
        if role != "customer":
            flash("Please log in or register to continue.", "info")
            return redirect(url_for("auth.login", next=request.path))
        return view(*args, **kwargs)
    return wrapper


def role_required(*roles):
    """Only staff with one of these roles can open the page, e.g. @role_required("manager").
    The account is checked in the database on every request, so a disabled account
    loses access at once."""
    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            if session.get("role") == "customer":
                abort(403)
            if session.get("role") not in STAFF_ROLES:
                flash("Please log in with a staff account.", "info")
                return redirect(url_for("auth.login", next=request.path))
            row = get_db().execute(
                "SELECT role, is_active FROM Staff WHERE staff_id = ?", (session.get("staff_id"),)
            ).fetchone()
            if row is None or not row["is_active"]:
                session.clear()
                flash("This account is disabled. Contact the administrator.", "error")
                return redirect(url_for("auth.login"))
            if row["role"] not in roles:
                abort(403)
            return view(*args, **kwargs)
        return wrapper
    return decorator


def start_customer_session(customer_id, name):
    session.clear()
    session["role"] = "customer"
    session["customer_id"] = customer_id
    session["name"] = name


def start_staff_session(staff_id, name, role):
    session.clear()
    session["role"] = role
    session["staff_id"] = staff_id
    session["name"] = name


@bp.route("/login", methods=["GET", "POST"])
def login():
    email = request.form.get("email", "").strip().lower()
    error = None
    if request.method == "POST":
        password = request.form.get("password", "")
        db = get_db()
        customer = db.execute(
            "SELECT customer_id, full_name, password_hash FROM Customers WHERE email = ?", (email,)
        ).fetchone()
        staff = db.execute(
            "SELECT staff_id, full_name, role, password_hash, is_active FROM Staff WHERE email = ?", (email,)
        ).fetchone()
        if customer and customer["password_hash"] and check_password_hash(customer["password_hash"], password):
            start_customer_session(customer["customer_id"], customer["full_name"])
            flash(f"Welcome back, {customer['full_name']}.", "success")
            return redirect(request.args.get("next") or home_url("customer"))
        if staff and check_password_hash(staff["password_hash"], password):
            if not staff["is_active"]:
                error = "This account is disabled. Contact the administrator."
            else:
                start_staff_session(staff["staff_id"], staff["full_name"], staff["role"])
                flash(f"Welcome, {staff['full_name']} ({staff['role']}).", "success")
                return redirect(request.args.get("next") or home_url(staff["role"]))
        else:
            error = "Wrong email or password."
    return render_template("auth/login.html", email=email, error=error)


@bp.route("/logout")
def logout():
    session.clear()
    flash("You have logged out.", "info")
    return redirect(url_for("customer.index"))


@bp.app_errorhandler(403)
def forbidden(_e):
    return render_template("auth/403.html"), 403

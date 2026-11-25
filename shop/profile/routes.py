"""
Profile pages (owner: Yeleussizova Zhannur, week 13).
"""
from flask import flash, redirect, render_template, request, session, url_for

from ..auth import role_required
from ..db import get_db
from . import bp
from .profile import ProfileError, change_password, get_staff, manager_summary, update_details

STAFF = ("manager", "courier", "admin")


def render_profile(details_errors=None, password_errors=None, form=None, status=200):
    db = get_db()
    me = get_staff(db, session["staff_id"])
    summary = manager_summary(db) if me["role"] == "manager" else None
    return render_template(
        "profile/profile.html", me=me, summary=summary, form=form or {},
        details_errors=details_errors or {}, password_errors=password_errors or {},
    ), status


@bp.route("/")
@role_required(*STAFF)
def view():
    return render_profile()


@bp.route("/details", methods=["POST"])
@role_required(*STAFF)
def details():
    try:
        name = update_details(get_db(), session["staff_id"], request.form.get("full_name"), request.form.get("phone"))
    except ProfileError as e:
        return render_profile(details_errors=e.args[0], form=request.form, status=400)
    session["name"] = name
    flash("Your details are saved.", "success")
    return redirect(url_for(".view"))


@bp.route("/password", methods=["POST"])
@role_required(*STAFF)
def password():
    try:
        change_password(get_db(), session["staff_id"], request.form.get("current", ""),
                        request.form.get("new", ""), request.form.get("repeat", ""))
    except ProfileError as e:
        return render_profile(password_errors=e.args[0], status=400)
    flash("Your password is changed. Use the new password next time you log in.", "success")
    return redirect(url_for(".view"))

"""
Admin pages (owner: Bakyt Aiganym, week 13).
Only staff with the role "admin" can open them.
"""
from flask import flash, redirect, render_template, request, session, url_for

from ..auth import role_required
from ..db import get_db
from . import bp
from .accounts import ROLES_ADMIN_CAN_CREATE, AccountError, create_staff, list_staff, set_active, staff_counts


def render_page(form=None, errors=None, status=200):
    db = get_db()
    return render_template(
        "admin/staff.html", staff=list_staff(db), counts=staff_counts(db),
        form=form or {"role": "courier"}, errors=errors or {}, roles=ROLES_ADMIN_CAN_CREATE,
        me=session.get("staff_id"),
    ), status


@bp.route("/")
@role_required("admin")
def staff_list():
    return render_page()


@bp.route("/staff/new", methods=["POST"])
@role_required("admin")
def staff_new():
    form = {k: request.form.get(k, "") for k in ("full_name", "email", "phone", "role", "password")}
    try:
        create_staff(get_db(), form)
    except AccountError as e:
        form["password"] = ""
        return render_page(form, e.args[0], status=400)
    flash(f"Account for {form['full_name']} ({form['role']}) is created. Give them the temporary password.", "success")
    return redirect(url_for(".staff_list"))


@bp.route("/staff/<int:staff_id>/<action>", methods=["POST"])
@role_required("admin")
def staff_toggle(staff_id, action):
    if action not in ("disable", "enable"):
        return redirect(url_for(".staff_list"))
    try:
        name = set_active(get_db(), staff_id, action == "enable", session["staff_id"])
    except AccountError as e:
        flash(e.args[0]["_"], "error")
    else:
        flash(f"{name}: account {'enabled' if action == 'enable' else 'disabled'}.", "info")
    return redirect(url_for(".staff_list"))

"""
Courier page (owner: Abenov Altair, week 13).
Only staff with the role "courier" can open it.
"""
from flask import flash, redirect, render_template, session, url_for

from ..auth import role_required
from ..db import get_db
from . import bp
from .delivery import DeliveryError, mark_delivered, my_deliveries, take_order, waiting_orders


@bp.route("/")
@role_required("courier")
def deliveries():
    db = get_db()
    me = session["staff_id"]
    return render_template(
        "courier/deliveries.html",
        waiting=waiting_orders(db),
        on_the_way=my_deliveries(db, me, "on_the_way"),
        delivered=my_deliveries(db, me, "delivered")[:10],
    )


@bp.route("/take/<int:order_id>", methods=["POST"])
@role_required("courier")
def take(order_id):
    try:
        take_order(get_db(), order_id, session["staff_id"])
    except DeliveryError as e:
        flash(str(e), "error")
    else:
        flash(f"Order #{order_id} is yours. It is now on the way.", "success")
    return redirect(url_for(".deliveries"))


@bp.route("/delivered/<int:order_id>", methods=["POST"])
@role_required("courier")
def delivered(order_id):
    try:
        mark_delivered(get_db(), order_id, session["staff_id"])
    except DeliveryError as e:
        flash(str(e), "error")
    else:
        flash(f"Order #{order_id} is delivered. Thank you!", "success")
    return redirect(url_for(".deliveries"))

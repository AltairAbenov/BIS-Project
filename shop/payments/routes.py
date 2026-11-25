"""
Payment page and "Cancel order" button (owner: Khassanov Ramazan).
"""
from flask import abort, flash, redirect, render_template, request, session, url_for

from ..auth import login_required
from ..customer.orders import get_order
from ..db import get_db
from . import bp
from .payments import PAYMENT_METHODS, PaymentError, cancel_order, payment_history, record_payment

@bp.route("/orders/<int:order_id>/pay", methods=["GET", "POST"])
@login_required
def pay(order_id):
    db = get_db()
    order, items = get_order(db, order_id, session["customer_id"])
    if order is None:
        abort(404)
    if order["payment_status"] in ("paid", "cancelled"):
        flash(f"Order #{order_id} is {order['payment_status']}, there is nothing to pay.", "info")
        return redirect(url_for("customer.order_detail", order_id=order_id))

    error = None
    method = request.form.get("method", "card")
    if request.method == "POST":
        # No real bank in the prototype: the "bank answer" field lets us show both results.
        approved = request.form.get("bank_answer") == "approved"
        try:
            record_payment(db, order_id, method, success=approved)
        except PaymentError as e:
            flash(str(e), "error")
            return redirect(url_for("customer.order_detail", order_id=order_id))
        if approved:
            flash(f"Payment successful. Order #{order_id} is paid.", "success")
            return redirect(url_for("customer.order_detail", order_id=order_id))
        error = "The bank declined the payment. You can try again, choose another method or cancel the order."
        order, items = get_order(db, order_id, session["customer_id"])
    return render_template("payments/pay.html", order=order, items=items, error=error, method=method,
                           methods=PAYMENT_METHODS, payments=payment_history(db, order_id))


@bp.route("/orders/<int:order_id>/cancel", methods=["POST"])
@login_required
def cancel(order_id):
    try:
        returned = cancel_order(get_db(), order_id, session["customer_id"])
    except PaymentError as e:
        flash(str(e), "error")
    else:
        flash(f"Order #{order_id} is cancelled. {returned} item(s) went back to the warehouse.", "info")
    return redirect(url_for("customer.order_detail", order_id=order_id))

"""
Customer side of the site (owner: Abenov Altair):
main page with search, product page, ordering, ratings and feedback, registration.
"""
from flask import Blueprint

from ..nav import add_link

bp = Blueprint("customer", __name__)

add_link("My orders", "customer.my_orders", roles=("customer",))

from . import routes  # noqa: E402,F401  (routes use bp)

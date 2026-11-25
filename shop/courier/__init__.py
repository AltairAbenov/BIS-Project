"""
Courier page (owner: Abenov Altair, week 13).
"""
from flask import Blueprint

from ..nav import add_link

bp = Blueprint("courier", __name__, url_prefix="/courier")

add_link("Deliveries", "courier.deliveries", roles=("courier",))

from . import routes  # noqa: E402,F401

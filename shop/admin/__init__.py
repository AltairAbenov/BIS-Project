"""
Admin part of the site (owner: Bakyt Aiganym, week 13).
"""
from flask import Blueprint

from ..nav import add_link

bp = Blueprint("admin", __name__, url_prefix="/admin")

add_link("Staff accounts", "admin.staff_list", roles=("admin",))

from . import routes  # noqa: E402,F401

"""
Manager part of the site (week 13).
Manager account and dashboard - owner: Shointay Aigerim (routes.py)
"""
from flask import Blueprint

from ..nav import add_link

bp = Blueprint("manager", __name__, url_prefix="/manager")

add_link("Dashboard", "manager.dashboard", roles=("manager",))

from . import routes  # noqa: E402,F401

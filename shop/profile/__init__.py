"""
Manager profile (owner: Yeleussizova Zhannur, week 13).
Every staff member can open their own profile; the shop summary is shown to managers.
"""
from flask import Blueprint

from ..nav import add_link

bp = Blueprint("profile", __name__, url_prefix="/manager/profile")

add_link("My profile", "profile.view", roles=("manager", "courier", "admin"))

from . import routes  # noqa: E402,F401

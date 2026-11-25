"""
Payment and cancellation (owner: Khassanov Ramazan).
"""
from flask import Blueprint

bp = Blueprint("payments", __name__)

from . import routes  # noqa: E402,F401

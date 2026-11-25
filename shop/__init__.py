"""
Online Shop - Flask application (whole team).

Every folder inside shop/ is one part of the site with its own owner
(see .github/CODEOWNERS). A part that defines a Blueprint called `bp`
is registered automatically, so adding a new part never changes this file.
"""
import importlib
import os
import pkgutil

from flask import Flask, session

from . import db, nav

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def create_app(database=None):
    app = Flask(__name__)
    app.secret_key = os.environ.get("SECRET_KEY", "change-this-key-before-real-use")
    app.config["DATABASE"] = database or os.path.join(PROJECT_DIR, "shop.db")

    db.init_db(app.config["DATABASE"], PROJECT_DIR)
    app.teardown_appcontext(db.close_db)

    # register every part of the site (shop/auth.py, shop/customer/, shop/payments/, ...)
    for info in sorted(pkgutil.iter_modules(__path__), key=lambda m: m.name):
        module = importlib.import_module(f"{__name__}.{info.name}")
        if hasattr(module, "bp"):
            app.register_blueprint(module.bp)

    @app.context_processor
    def layout_context():
        role = session.get("role", "guest")
        return {"user_name": session.get("name"), "role": role, "nav_links": nav.links_for(role)}

    @app.template_filter("initial")
    def initial(name):
        """First letter of the product name for the picture placeholder ("27\\" Monitor" -> "M")."""
        return next((c for c in name if c.isalpha()), "?")

    @app.template_filter("kzt")
    def kzt(value):
        return "{:,.0f}".format(value or 0).replace(",", " ") + " \u20b8"

    return app

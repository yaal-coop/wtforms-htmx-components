"""Example app for wtforms-htmx-components, one composite per page."""

from __future__ import annotations

import os

from flask import Blueprint
from flask import Flask
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for

bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    return render_template("index.html")


@bp.route("/toggle-htmx", methods=["POST"])
def toggle_htmx():
    referer = request.form.get("referer") or url_for("main.index")
    enabled = "enabled" in request.form
    resp = redirect(referer)
    resp.set_cookie("htmx_enabled", "1" if enabled else "0", max_age=86400 * 30)
    return resp


from . import patterns  # noqa: E402, F401
from ._shared import _STATE  # noqa: E402


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "dev-only-not-secret"
    app.config.setdefault("HTMX_VERSION", int(os.environ.get("HTMX_VERSION", "4")))

    @app.context_processor
    def inject_htmx_enabled():
        htmx_on = request.cookies.get("htmx_enabled", "1") == "1"
        boost = htmx_on and not app.config.get("HTMX_BOOST_DISABLED", False)
        return {
            "htmx_enabled": htmx_on,
            "htmx_boost": boost,
            "htmx_version": app.config["HTMX_VERSION"],
        }

    app.register_blueprint(bp)
    return app


__all__ = ["_STATE", "create_app"]

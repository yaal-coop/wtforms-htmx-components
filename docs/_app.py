"""WSGI factory for ``sphinxcontrib-screenshot``."""

from __future__ import annotations

import pathlib
import sys


def create_app(sphinx_app):
    project_root = pathlib.Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    from examples import _STATE
    from examples import create_app as create_examples_app

    _STATE["combobox"].country = "CU"
    _STATE["combobox"].countries = ["CU", "PS"]

    app = create_examples_app()
    app.config["HTMX_BOOST_DISABLED"] = True
    return app

from __future__ import annotations

import sys
from importlib.metadata import version as _version
from pathlib import Path
from wsgiref.simple_server import WSGIRequestHandler

from pallets_sphinx_themes import ProjectLink

# Make ``_app`` importable by ``screenshot_apps`` below.
sys.path.insert(0, str(Path().resolve()))

WSGIRequestHandler.log_request = lambda *args, **kwargs: None

project = "wtforms-htmx-components"
author = "Éloi Rivard"
release = _version("wtforms-htmx-components")
version = ".".join(release.split(".")[:2])

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.extlinks",
    "sphinx.ext.intersphinx",
    "sphinx_issues",
    "pallets_sphinx_themes",
    "sphinxcontrib.screenshot",
    "_mdn_attr_role",
]

screenshot_apps = {"examples": "_app:create_app"}
screenshot_default_locator_padding = 10
screenshot_default_color_scheme = "auto"

intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
    "flask": ("https://flask.palletsprojects.com/en/stable/", None),
    "markupsafe": ("https://markupsafe.palletsprojects.com/en/stable/", None),
    "wtforms": ("https://wtforms.readthedocs.io/en/stable/", None),
    "wtforms-htmx": ("https://wtforms-htmx.readthedocs.io/en/stable/", None),
}

extlinks = {
    "htmx-attr": (
        "https://htmx.org/attributes/%s/",
        "%s",
    ),
    "htmx-header": (
        "https://htmx.org/reference/?h=%s#headers",
        "%s",
    ),
    "mdn-tag": (
        "https://developer.mozilla.org/en-US/docs/Web/HTML/Element/%s",
        "<%s>",
    ),
    "mdn-global-attr": (
        "https://developer.mozilla.org/en-US/docs/Web/HTML/Global_attributes/%s",
        "%s",
    ),
    "mdn-role": (
        "https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA/Reference/Roles/%s_role",
        'role="%s"',
    ),
}

issues_github_path = "yaal-coop/wtforms-htmx-components"

templates_path = ["_templates"]
exclude_patterns = ["_build"]

html_theme = "flask"
html_static_path = ["_static"]
html_css_files = ["color-scheme.css"]

html_context = {
    "project_links": [
        ProjectLink(
            "PyPI Releases", "https://pypi.org/project/wtforms-htmx-components/"
        ),
        ProjectLink(
            "Source Code", "https://github.com/yaal-coop/wtforms-htmx-components/"
        ),
        ProjectLink(
            "Issue Tracker",
            "https://github.com/yaal-coop/wtforms-htmx-components/issues/",
        ),
        ProjectLink("wtforms-htmx", "https://wtforms-htmx.readthedocs.io/"),
    ],
}
html_sidebars = {
    "index": ["project.html", "localtoc.html", "searchbox.html"],
    "**": ["home.html", "localtoc.html", "relations.html", "searchbox.html"],
}
html_show_sourcelink = False

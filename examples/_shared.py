"""Shared building blocks for the example feature modules."""

from __future__ import annotations

from copy import deepcopy

import pycountry
from flask import render_template
from flask import request
from wtforms import Form
from wtforms.fields import ButtonField
from wtforms.fields import SubmitField
from wtforms.validators import ValidationError
from wtforms_htmx import HtmxFormMixin
from wtforms_htmx import HtmxMeta

_STATE: dict = {}
_INITIAL_STATE: dict = {}


def reset_state():
    """Restore the example state to its seeded values."""
    _STATE.clear()
    _STATE.update(deepcopy(_INITIAL_STATE))


class ExampleForm(HtmxFormMixin, Form):
    """Base form of the examples."""

    def populate_obj(self, obj):
        for name, field in self._fields.items():
            if isinstance(field, (SubmitField, ButtonField)):
                continue

            field.populate_obj(obj, name)

    class Meta(HtmxMeta):
        def field_wrapper(self, field, render_kw):
            return render_template("_field.html", field=field, render_kw=render_kw)

        @property
        def htmx_endpoint(self):
            return request.path


COUNTRY_BY_CODE = sorted(
    ((c.alpha_2, c.name) for c in pycountry.countries),
    key=lambda pair: pair[1],
)
NAME_BY_CODE = dict(COUNTRY_BY_CODE)
_VALID_CODES = {code for code, _ in COUNTRY_BY_CODE}


def valid_country_code(form, field):
    """Ensure the final value is a valid ISO alpha-2 code."""
    if field.data and field.data.upper() not in _VALID_CODES:
        raise ValidationError("Please pick a country from the list.")

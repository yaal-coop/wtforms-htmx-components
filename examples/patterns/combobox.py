"""Comboboxes in one form: single and multi, strict and free.

======  =====================================================  ===========================
.       strict (catalog only)                                  ``allow_custom_value=True``
======  =====================================================  ===========================
single  :class:`~wtforms_htmx_components.ComboboxSingleField`  same + "create" option
multi   :class:`~wtforms_htmx_components.ComboboxMultiField`   same + "create" option
======  =====================================================  ===========================

The strict comboboxes accept only catalog values. The free ones add an
"Add ..." option when the query is not in the catalog. Picking it stores
the typed text. The last combobox has a short list of continents. With
``min_query_length=0``, it shows them all when its input gets the focus.

The example subclasses the widgets:

- ``FlaggedListboxWidget`` shows a country flag before each catalog
  option.
- ``StyledSingleChipWidget`` and ``StyledChipsWidget`` add the CSS
  classes of the example app, and a flag on catalog values.

.. screencast:: |examples|/patterns/combobox
   :locator: .demo-area
   :autoplay:
   :muted:
   :loop:
   :trim-start:
   :poster:
   :interactions:
     // Reserve room for the open listbox. ``demo-hover`` stands in for
     // ``:hover``, which synthetic clicks do not trigger.
     const style = document.createElement('style');
     style.textContent = `
       .demo-area { padding-bottom: 7rem; }
       [role="option"].demo-hover {
         background: var(--pico-primary-background);
         color: var(--pico-primary-inverse);
       }
     `;
     document.head.appendChild(style);
     const wait = (ms) => new Promise(r => setTimeout(r, ms));
     const $ = (s) => document.querySelector(s);
     const typeQuery = async (text) => {
       const q = $('#countries-query');
       q.focus();
       q.value = '';
       q.dispatchEvent(new Event('input', {bubbles: true}));
       await wait(200);
       for (const c of text) {
         const cur = $('#countries-query');
         cur.focus();
         cur.value = (cur.value || '') + c;
         cur.dispatchEvent(new Event('input', {bubbles: true}));
         await wait(180);
       }
       await wait(500);
     };
     const pickByCode = async (code) => {
       const opt = $(`#countries-suggestions [data-value="${code}"]`);
       opt.classList.add('demo-hover');
       await wait(700);
       opt.querySelector('button').click();
       await wait(700);
     };
     const removeChip = async (code) => {
       const btn = document.querySelector(
         `#countries-value .chip[data-value="${code}"] .chip-remove`
       );
       btn.click();
       await wait(700);
     };
     await wait(500);
     // Starts with FR and JP: add PS, remove PS, remove JP, add JP.
     await typeQuery('pal');
     await wait(300);
     await pickByCode('PS');
     await wait(500);
     await removeChip('PS');
     await wait(400);
     await removeChip('JP');
     await wait(400);
     await typeQuery('jap');
     await wait(300);
     await pickByCode('JP');
     $('#countries-query').blur();
     await wait(500);

   Multi-value combobox: type to filter the suggestions, click one to
   add a chip, click ``×`` to remove it. Picked values are left out of
   the suggestions.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from dataclasses import field as dc_field

from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask import Response
from flask import url_for
from markupsafe import escape
from markupsafe import Markup
from wtforms import SelectChoice
from wtforms import SubmitField
from wtforms.widgets import html_params

from wtforms_htmx_components import ChipsWidget
from wtforms_htmx_components import ComboboxMultiField
from wtforms_htmx_components import ComboboxSingleField
from wtforms_htmx_components import ListboxWidget
from wtforms_htmx_components import SingleChipWidget

from .. import bp
from .._shared import _INITIAL_STATE
from .._shared import _STATE
from .._shared import COUNTRY_BY_CODE
from .._shared import ExampleForm
from .._shared import NAME_BY_CODE
from .._shared import valid_country_code


@dataclass
class ComboboxData:
    country: str = "FR"
    country_free: str = ""
    countries: list[str] = dc_field(default_factory=lambda: ["FR", "JP"])
    countries_free: list[str] = dc_field(default_factory=list)
    continents: list[str] = dc_field(default_factory=list)


_STATE["combobox"] = ComboboxData()
_INITIAL_STATE["combobox"] = deepcopy(_STATE["combobox"])


def _flag_img(code: str) -> Markup:
    return Markup(
        '<img class="flag"'
        f' src="https://cdn.jsdelivr.net/npm/country-flag-icons/3x2/{code}.svg"'
        ' alt="" width="24" height="16">'
    )


def _label_for_country(code: str) -> str:
    """Return the country name of a code, or the code itself for free values."""
    return NAME_BY_CODE.get(code, code)


class FlaggedListboxWidget(ListboxWidget):
    """Listbox with a country flag before each catalog option."""

    def render_option(self, opt, button):
        label = opt.choice.label
        if opt.choice.value in NAME_BY_CODE:
            label = _flag_img(opt.choice.value) + label

        li_attrs = html_params(role="option", data_value=opt.choice.value)
        return f"<li {li_attrs}>{button(label=label)}</li>"


class StyledChipMixin:
    """Chips with the example CSS classes and a flag on catalog values."""

    def render_chip(self, field, value, label, remove):
        flag = _flag_img(value) if value in NAME_BY_CODE else ""
        button = (
            ""
            if remove is None
            else remove(
                value=value,
                label="×",
                id=False,
                class_="chip-remove",
                aria_label=f"Remove {label}",
            )
        )
        hidden = html_params(type="hidden", name=field.name, value=value)
        return (
            f"<span {html_params(class_='chip', data_value=value)}>"
            f'<span class="chip-label">{flag}{escape(label)}</span>'
            f"{button}"
            f"<input {hidden}>"
            "</span>"
        )


class StyledSingleChipWidget(StyledChipMixin, SingleChipWidget):
    """Single chip with the example CSS classes."""


class StyledChipsWidget(StyledChipMixin, ChipsWidget):
    """Chips with the example CSS classes."""


def suggest_countries(query, _form):
    """Match ISO countries by name substring or alpha-2 code."""
    q = query.lower()
    return (
        SelectChoice(c, n)
        for c, n in COUNTRY_BY_CODE
        if q in n.lower() or q == c.lower()
    )


CONTINENTS = [
    "Africa",
    "Antarctica",
    "Asia",
    "Europe",
    "North America",
    "Oceania",
    "South America",
]


def suggest_continents(query, _form):
    """Match continents by name substring."""
    q = query.lower()
    return (SelectChoice(name, name) for name in CONTINENTS if q in name.lower())


def _add_label(query: str) -> str:
    return f'Add "{query}"'


class ComboboxForm(ExampleForm):
    """Combobox declarations in one form: single/multi × strict/free."""

    country = ComboboxSingleField(
        "Country (strict)",
        suggest=suggest_countries,
        label_for=_label_for_country,
        validators=[valid_country_code],
        placeholder="Type a country…",
        listbox_widget=FlaggedListboxWidget(),
        value_widget=StyledSingleChipWidget(label_for=_label_for_country),
        value_render_kw={"class": "single-value"},
    )
    country_free = ComboboxSingleField(
        "Country (allow custom)",
        suggest=suggest_countries,
        label_for=_label_for_country,
        placeholder="Type any value…",
        allow_custom_value=True,
        custom_value_label=_add_label,
        listbox_widget=FlaggedListboxWidget(),
        value_widget=StyledSingleChipWidget(label_for=_label_for_country),
        value_render_kw={"class": "single-value"},
    )
    countries = ComboboxMultiField(
        "Countries (strict)",
        suggest=suggest_countries,
        label_for=_label_for_country,
        placeholder="Type a country…",
        listbox_widget=FlaggedListboxWidget(multi=True),
        chips_widget=StyledChipsWidget(),
        chips_render_kw={"class": "chips"},
    )
    countries_free = ComboboxMultiField(
        "Countries (allow custom)",
        suggest=suggest_countries,
        label_for=_label_for_country,
        placeholder="Type any value…",
        allow_custom_value=True,
        custom_value_label=_add_label,
        listbox_widget=FlaggedListboxWidget(multi=True),
        chips_widget=StyledChipsWidget(),
        chips_render_kw={"class": "chips"},
    )
    continents = ComboboxMultiField(
        "Continents",
        suggest=suggest_continents,
        placeholder="Pick continents…",
        min_query_length=0,
        chips_widget=StyledChipsWidget(),
        chips_render_kw={"class": "chips"},
    )
    save = SubmitField("Save")


@bp.route("/patterns/combobox", methods=["GET", "POST"])
def combobox():
    state = _STATE["combobox"]
    form = ComboboxForm(request.form or None, obj=state, headers=request.headers)
    if result := form.partial():
        return Response(result.body, headers=result.headers)

    if form.submitter is not form.save:
        return render_template("patterns/combobox.html", form=form)

    if not form.validate():
        flash("Please fix the errors below.", "error")
        return render_template("patterns/combobox.html", form=form)

    form.populate_obj(state)
    flash(
        f"Saved: country={state.country!r}, country_free={state.country_free!r}, "
        f"countries={state.countries!r}, countries_free={state.countries_free!r}, "
        f"continents={state.continents!r}.",
        "success",
    )
    return redirect(url_for("main.combobox"))

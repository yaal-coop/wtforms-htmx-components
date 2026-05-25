"""Unit tests for ComboboxSingleField / ComboboxMultiField."""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field as dc_field
from types import SimpleNamespace

import pytest
from werkzeug.datastructures import MultiDict
from wtforms import SelectChoice
from wtforms.validators import DataRequired
from wtforms.validators import Disabled
from wtforms.validators import ReadOnly
from wtforms.validators import ValidationError
from wtforms_htmx import HtmxForm

from wtforms_htmx_components import ComboboxField
from wtforms_htmx_components import ComboboxMultiField
from wtforms_htmx_components import ComboboxSingleField
from wtforms_htmx_components import MaxItems

NAME_BY_CODE = {"FR": "France", "DE": "Germany", "JP": "Japan"}
CODES = list(NAME_BY_CODE)


def _formdata(data):
    """Build request form data where a list value posts several values."""
    return MultiDict(
        [(k, x) for k, v in data.items() for x in (v if isinstance(v, list) else [v])]
    )


def _suggest(query, _form):
    q = query.lower()
    return [
        SelectChoice(c, n)
        for c, n in NAME_BY_CODE.items()
        if q in n.lower() or q == c.lower()
    ]


def _label(code):
    return NAME_BY_CODE.get(code, code)


@dataclass
class _State:
    country: str = ""


@dataclass
class _MultiState:
    countries: list[str] = dc_field(default_factory=list)


class _SingleForm(HtmxForm):
    class Meta:
        csrf = False

    country = ComboboxSingleField("Country", suggest=_suggest, label_for=_label)


def test_single_data_is_scalar_not_dict():
    """Without data, the single field's data is None."""
    form = _SingleForm()
    assert form.country.data is None


def test_single_initial_render_from_obj_seeds_label():
    """A stored value fills the query input with its label."""
    form = _SingleForm(obj=_State(country="FR"))
    assert form.country.data == "FR"
    assert form.country.query.data == "France"
    assert form.country.value.data == "FR"


def test_single_populate_obj_writes_scalar():
    """populate_obj writes the stored value, not a dict."""
    state = _State(country="FR")
    form = _SingleForm(obj=state)
    form.populate_obj(state)
    assert state.country == "FR"
    assert not isinstance(state.country, dict)


def test_single_pick_mutation_dispatches_via_nested_resolve():
    """Clicking a suggestion stores its value and shows its label."""
    form = _SingleForm(
        _formdata(
            {"country-value": "FR", "country-query": "ger", "country-suggestions": "DE"}
        ),
        obj=_State(country="FR"),
    )
    form.mutate()
    assert form.country.value.data == "DE"
    assert form.country.query.data == "Germany"


def test_single_choices_empty_on_empty_query():
    """An empty query gives no suggestions."""
    form = _SingleForm(obj=_State(country=""))
    assert form.country.suggestions.choices == []


def test_single_choices_close_on_match_collapses_listbox():
    """No suggestions when the query is the label of the stored value."""
    form = _SingleForm(obj=_State(country="FR"))
    assert form.country.suggestions.choices == []


def test_single_close_on_match_disabled_keeps_listbox():
    """With close_listbox_on_match=False, the stored value stays suggested."""

    class F(HtmxForm):
        class Meta:
            csrf = False

        country = ComboboxSingleField(
            "Country",
            suggest=_suggest,
            label_for=_label,
            close_listbox_on_match=False,
        )

    form = F(obj=_State(country="FR"))
    values = [c.value for c in form.country.suggestions.choices]
    assert "FR" in values


def test_single_validators_forwarded_to_storage():
    """The field's validators apply to the stored value."""

    class F(HtmxForm):
        class Meta:
            csrf = False

        country = ComboboxSingleField(
            "Country", suggest=_suggest, validators=[DataRequired()]
        )

    form = F()
    assert form.validate() is False
    assert form.country.errors


def test_single_search_label_none_omits_button():
    """search_label=None removes the search button."""

    class F(HtmxForm):
        class Meta:
            csrf = False

        country = ComboboxSingleField("Country", suggest=_suggest, search_label=None)

    form = F()
    assert "search" not in form.country.form._fields


def _single_form_class(**kwargs):
    class F(HtmxForm):
        class Meta:
            csrf = False

        country = ComboboxSingleField(
            "Country", suggest=_suggest, label_for=_label, **kwargs
        )

    return F


def test_single_allow_custom_value_appends_synthetic_when_no_match():
    """A query that matches no catalog entry surfaces an "Add" option."""
    Form = _single_form_class(allow_custom_value=True)
    form = Form(_formdata({"country-query": "Atlantis", "country-value": ""}))
    values = [c.value for c in form.country.suggestions.choices]
    assert values == ["Atlantis"]


def test_single_allow_custom_value_appends_synthetic_alongside_suggestions():
    """A query matching some catalog entries still gets the create option."""
    Form = _single_form_class(allow_custom_value=True)
    form = Form(_formdata({"country-query": "fra", "country-value": ""}))
    values = [c.value for c in form.country.suggestions.choices]
    assert "FR" in values
    assert "fra" in values


def test_single_allow_custom_value_skips_synthetic_when_label_matches():
    """Typing the exact label of a catalog match: no synthetic duplicate."""
    Form = _single_form_class(allow_custom_value=True, close_listbox_on_match=False)
    form = Form(_formdata({"country-query": "France", "country-value": ""}))
    values = [c.value for c in form.country.suggestions.choices]
    assert values == ["FR"]


def test_single_allow_custom_value_pick_synthetic_commits_query():
    """Picking the synthetic option fires the standard pick triggers."""
    Form = _single_form_class(allow_custom_value=True)
    form = Form(
        _formdata(
            {
                "country-query": "Atlantis",
                "country-value": "",
                "country-suggestions": "Atlantis",
            }
        ),
    )
    form.mutate()
    assert form.country.value.data == "Atlantis"
    assert form.country.query.data == "Atlantis"


def test_single_custom_value_label_formats_synthetic_label():
    """``custom_value_label`` controls the visible label of the create option."""
    Form = _single_form_class(
        allow_custom_value=True,
        custom_value_label=lambda q: f"Add « {q} »",
    )
    form = Form(_formdata({"country-query": "Atlantis", "country-value": ""}))
    labels = [c.label for c in form.country.suggestions.choices]
    assert labels == ["Add « Atlantis »"]


def test_single_allow_custom_value_default_false_no_synthetic():
    """Without ``allow_custom_value``, off-catalog queries yield no options."""
    form = _SingleForm(_formdata({"country-query": "Atlantis", "country-value": ""}))
    assert form.country.suggestions.choices == []


def test_single_chip_mode_renders_chip_when_value_set():
    """The value widget emits a chip when value is set."""
    form = _SingleForm(obj=_State(country="FR"))
    html = str(form.country.value())
    assert 'id="country-value"' in html
    assert 'data-value="FR"' in html
    assert "France" in html
    assert 'name="country-remove"' in html
    assert 'name="country-value"' in html
    assert 'value="FR"' in html


def test_single_chip_mode_renders_empty_wrapper_when_value_empty():
    """Without a value, the value widget renders an empty hidden input."""
    form = _SingleForm()
    html = str(form.country.value())
    assert 'id="country-value"' in html
    assert "data-value=" not in html
    assert 'name="country-remove"' not in html
    assert 'name="country-value"' in html


def test_single_remove_clears_value_and_query():
    """Clicking the chip's × clears both value and query."""
    form = _SingleForm(
        _formdata(
            {
                "country-value": "FR",
                "country-query": "France",
                "country-remove": "FR",
            }
        ),
        obj=_State(country="FR"),
    )
    form.mutate()
    assert form.country.value.data == ""
    assert form.country.query.data == ""


def test_single_max_suggestions_truncates():
    """max_suggestions caps the number of suggestions."""

    def _wide(_q, _f):
        return [SelectChoice(str(i), str(i)) for i in range(100)]

    class F(HtmxForm):
        class Meta:
            csrf = False

        x = ComboboxSingleField("X", suggest=_wide, max_suggestions=3)

    form = F(_formdata({"x-query": "anything", "x-value": ""}))
    assert len(form.x.suggestions.choices) == 3


class _MultiForm(HtmxForm):
    class Meta:
        csrf = False

    countries = ComboboxMultiField("Countries", suggest=_suggest, label_for=_label)


def test_multi_data_is_list():
    """The multi field's data is not a dict."""
    form = _MultiForm()
    assert not isinstance(form.countries.data, dict)


def test_multi_initial_render_from_obj_populates_value():
    """The object's list fills the stored values."""
    form = _MultiForm(obj=_MultiState(countries=["FR", "JP"]))
    assert form.countries.data == ["FR", "JP"]
    assert form.countries.value.data == ["FR", "JP"]


def test_multi_populate_obj_writes_list():
    """populate_obj writes the list of stored values."""
    state = _MultiState(countries=["FR"])
    form = _MultiForm(obj=state)
    form.populate_obj(state)
    assert state.countries == ["FR"]


def test_multi_choices_filter_out_picked():
    """Picked values are left out of the suggestions."""
    form = _MultiForm(
        _formdata({"countries-query": "fr", "countries-value": "FR"}),
        obj=_MultiState(countries=["FR"]),
    )
    values = [c.value for c in form.countries.suggestions.choices]
    assert "FR" not in values


def test_multi_add_via_value_add():
    """Clicking a suggestion adds its value and clears the query."""
    form = _MultiForm(
        _formdata(
            {
                "countries-query": "ger",
                "countries-value": "FR",
                "countries-suggestions": "DE",
            }
        ),
        obj=_MultiState(countries=["FR"]),
    )
    form.mutate()
    assert form.countries.value.data == ["FR", "DE"]
    assert form.countries.query.data == ""


def _multi_form_class(**kwargs):
    class F(HtmxForm):
        class Meta:
            csrf = False

        countries = ComboboxMultiField(
            "Countries", suggest=_suggest, label_for=_label, **kwargs
        )

    return F


def test_multi_allow_custom_value_appends_synthetic_when_no_match():
    """An off-catalog query surfaces an "Add" option in the listbox."""
    Form = _multi_form_class(allow_custom_value=True)
    form = Form(_formdata({"countries-query": "Atlantis", "countries-value": "JP"}))
    values = [c.value for c in form.countries.suggestions.choices]
    assert values == ["Atlantis"]


def test_multi_allow_custom_value_appends_synthetic_alongside_suggestions():
    """Synthetic option coexists with catalog matches in the multi listbox."""
    Form = _multi_form_class(allow_custom_value=True)
    form = Form(_formdata({"countries-query": "fra", "countries-value": ""}))
    values = [c.value for c in form.countries.suggestions.choices]
    assert "FR" in values
    assert "fra" in values


def test_multi_allow_custom_value_skips_synthetic_when_picked_label_matches():
    """When the query equals the label of an already-picked value, no synthetic."""
    Form = _multi_form_class(allow_custom_value=True)
    form = Form(
        _formdata({"countries-query": "France", "countries-value": "FR"}),
        obj=_MultiState(countries=["FR"]),
    )
    values = [c.value for c in form.countries.suggestions.choices]
    assert values == []


def test_multi_allow_custom_value_pick_synthetic_appends_and_clears_query():
    """Picking the synthetic option appends to value and clears the query."""
    Form = _multi_form_class(allow_custom_value=True)
    form = Form(
        _formdata(
            {
                "countries-query": "Atlantis",
                "countries-value": "FR",
                "countries-suggestions": "Atlantis",
            }
        ),
        obj=_MultiState(countries=["FR"]),
    )
    form.mutate()
    assert form.countries.value.data == ["FR", "Atlantis"]
    assert form.countries.query.data == ""


def test_multi_custom_value_label_formats_synthetic_label():
    """custom_value_label sets the label of the create option."""
    Form = _multi_form_class(
        allow_custom_value=True,
        custom_value_label=lambda q: f"Add « {q} »",
    )
    form = Form(
        _formdata({"countries-query": "Atlantis", "countries-value": ""}),
    )
    labels = [c.label for c in form.countries.suggestions.choices]
    assert labels == ["Add « Atlantis »"]


def test_multi_allow_custom_value_default_false_no_synthetic():
    """Without ``allow_custom_value``, off-catalog queries yield no options."""
    form = _MultiForm(
        _formdata({"countries-query": "Atlantis", "countries-value": "JP"}),
        obj=_MultiState(countries=["JP"]),
    )
    assert form.countries.suggestions.choices == []


def test_multi_max_items_caps_validation():
    """MaxItems fails when the list is over the cap."""

    class F(HtmxForm):
        class Meta:
            csrf = False

        countries = ComboboxMultiField(
            "Countries",
            suggest=_suggest,
            label_for=_label,
            validators=[MaxItems(max=2)],
        )

    form = F(obj=_MultiState(countries=["FR", "DE", "JP"]))
    assert form.validate() is False
    assert any("at most 2" in e for e in form.countries.errors)


def test_multi_max_items_under_cap_validates():
    """A list under the MaxItems cap validates."""

    class F(HtmxForm):
        class Meta:
            csrf = False

        countries = ComboboxMultiField(
            "Countries",
            suggest=_suggest,
            label_for=_label,
            validators=[MaxItems(max=2)],
        )

    form = F(obj=_MultiState(countries=["FR"]))
    assert form.validate() is True


def test_multi_max_items_choices_capped_at_max():
    """At the MaxItems cap, there are no suggestions."""

    class F(HtmxForm):
        class Meta:
            csrf = False

        countries = ComboboxMultiField(
            "Countries",
            suggest=_suggest,
            label_for=_label,
            validators=[MaxItems(max=2)],
        )

    form = F(
        _formdata({"countries-query": "ger", "countries-value": ["FR", "JP"]}),
        obj=_MultiState(countries=["FR", "JP"]),
    )
    assert form.countries.suggestions.choices == []


def test_multi_max_items_choices_unaffected_under_cap():
    """Under the MaxItems cap, suggestions still show."""

    class F(HtmxForm):
        class Meta:
            csrf = False

        countries = ComboboxMultiField(
            "Countries",
            suggest=_suggest,
            label_for=_label,
            validators=[MaxItems(max=3)],
        )

    form = F(
        _formdata({"countries-query": "ger", "countries-value": ["FR"]}),
        obj=_MultiState(countries=["FR"]),
    )
    values = [c.value for c in form.countries.suggestions.choices]
    assert "DE" in values


def test_multi_max_items_caps_synthetic_too():
    """At the MaxItems cap, the create option is gone too."""

    class F(HtmxForm):
        class Meta:
            csrf = False

        countries = ComboboxMultiField(
            "Countries",
            suggest=_suggest,
            label_for=_label,
            allow_custom_value=True,
            validators=[MaxItems(max=2)],
        )

    form = F(
        _formdata({"countries-query": "Atlantis", "countries-value": ["FR", "JP"]}),
        obj=_MultiState(countries=["FR", "JP"]),
    )
    assert form.countries.suggestions.choices == []


def test_multi_remove_via_value_remove():
    """Clicking a chip's × removes its value."""
    form = _MultiForm(
        _formdata(
            {
                "countries-query": "",
                "countries-value": ["FR", "DE"],
                "countries-remove": "FR",
            }
        ),
        obj=_MultiState(countries=["FR", "DE"]),
    )
    form.mutate()
    assert form.countries.value.data == ["DE"]


def test_widget_renders_div_wrapper_with_inner_fields():
    """The field renders its inner fields in a div."""
    form = _SingleForm(obj=_State(country="FR"))
    html = str(form.country())
    assert html.startswith("<div")
    assert 'role="combobox"' in html
    assert 'role="listbox"' in html
    assert 'name="country-value"' in html


def test_widget_renders_the_search_button():
    """The field renders its search button after the query input."""
    html = str(_SingleForm().country())
    assert html.index('name="country-query"') < html.index('name="country-search"')


def test_widget_without_search_label_renders_no_search_button():
    """With search_label=None, the field renders no search button."""
    html = str(_multi_form_class(search_label=None)().countries())
    assert "countries-search" not in html


def test_widget_aria_controls_points_to_listbox():
    """aria-controls points to the listbox."""
    form = _SingleForm()
    html = str(form.country())
    assert 'aria-controls="country-suggestions"' in html


def test_widget_aria_expanded_reflects_choices():
    """aria-expanded is true only when there are suggestions."""
    empty_form = _SingleForm()
    assert 'aria-expanded="false"' in str(empty_form.country())

    populated = _SingleForm(
        _formdata({"country-query": "fra", "country-value": ""}),
    )
    assert populated.country.suggestions.choices
    assert 'aria-expanded="true"' in str(populated.country())


def test_widget_listbox_emits_role_option_with_data_value():
    """Each suggestion is a role=option with its value."""
    form = _SingleForm(
        _formdata({"country-query": "ger", "country-value": ""}),
    )
    html = str(form.country.suggestions())
    assert 'role="option"' in html
    assert 'data-value="DE"' in html


def test_single_allow_custom_value_skips_synthetic_when_value_matches():
    """A query equal to a suggestion's value adds no create option."""

    class F(HtmxForm):
        class Meta:
            csrf = False

        country = ComboboxSingleField(
            "Country", suggest=_suggest, label_for=_label, allow_custom_value=True
        )

    form = F(_formdata({"country-query": "DE", "country-value": ""}))
    assert [c.value for c in form.country.suggestions.choices] == ["DE"]


def test_query_gets_autofocus_after_a_pick():
    """After a click on a suggestion, the query input has autofocus."""
    form = _SingleForm(
        _formdata({"country-query": "ger", "country-suggestions": "DE"}),
    )
    form.mutate()
    assert "autofocus" in str(form.country.query())


def test_query_has_no_autofocus_while_typing():
    """Without a pick, the query input has no autofocus."""
    form = _SingleForm(_formdata({"country-query": "ger", "country-value": ""}))
    assert "autofocus" not in str(form.country.query())


def test_multi_renders_chips_and_a_multiselectable_listbox():
    """The multi field renders one chip per value and a multiselectable listbox."""
    form = _MultiForm(
        _formdata({"countries-query": "ger", "countries-value": ["FR", "JP"]}),
    )
    html = str(form.countries())
    assert 'aria-multiselectable="true"' in html
    assert 'aria-label="Remove France"' in html
    assert 'aria-label="Remove Japan"' in html


def test_multi_choices_empty_on_empty_query():
    """An empty query gives no multi suggestions."""
    form = _MultiForm(_formdata({"countries-query": "", "countries-value": "FR"}))
    assert form.countries.suggestions.choices == []


def test_multi_search_label_none_omits_button():
    """search_label=None removes the search button of a multi field."""
    form = _multi_form_class(search_label=None)()
    assert "search" not in form.countries.form


def test_max_items_rejects_a_negative_cap():
    """MaxItems refuses a negative cap."""
    with pytest.raises(ValueError, match="non-negative"):
        MaxItems(max=-1)


def test_max_items_accepts_empty_data():
    """MaxItems lets empty data pass."""
    form = _multi_form_class(validators=[MaxItems(max=0)])()
    assert form.validate() is True


def test_max_items_formats_a_custom_message():
    """A custom MaxItems message gets the cap."""
    form = _multi_form_class(validators=[MaxItems(max=1, message="Max %(max)d.")])(
        _formdata({"countries-value": ["FR", "JP"]}),
    )
    assert form.validate() is False
    assert form.countries.errors == ["Max 1."]


_XSS = '"><img src=x onerror=alert(1)>'


def test_single_chip_escapes_the_posted_value():
    """The single chip escapes a posted value in its label and attributes."""
    form = _SingleForm(_formdata({"country-value": _XSS}))
    html = str(form.country())
    assert "<img" not in html
    assert "&lt;img" in html


def test_multi_chips_escape_the_posted_values():
    """The multi chips escape posted values in their labels and attributes."""
    form = _MultiForm(_formdata({"countries-value": [_XSS]}))
    html = str(form.countries())
    assert "<img" not in html
    assert "&lt;img" in html


def test_listbox_escapes_the_create_option():
    """The listbox escapes the value and label of the create option."""
    form = _multi_form_class(allow_custom_value=True)(
        _formdata({"countries-query": _XSS})
    )
    html = str(form.countries.suggestions())
    assert "<img" not in html
    assert "&lt;img" in html


def test_multi_remove_label_is_configurable():
    """remove_label gives the text of the chips' remove buttons."""
    form = _multi_form_class(remove_label=lambda label: f"Retirer {label}")(
        _formdata({"countries-value": ["FR"]})
    )
    assert 'aria-label="Retirer France"' in str(form.countries())


def test_single_remove_label_is_configurable():
    """remove_label gives the text of the single chip's remove button."""
    form = _single_form_class(remove_label=lambda label: f"Retirer {label}")(
        _formdata({"country-value": "FR"})
    )
    assert 'aria-label="Retirer France"' in str(form.country())


class _PrefixTranslations:
    def ngettext(self, singular, plural, n):
        return f"T: {singular if n == 1 else plural}"


def test_max_items_default_message_goes_through_translations():
    """The default MaxItems message goes through the form's translations."""

    class F(HtmxForm):
        class Meta:
            csrf = False

            def get_translations(self, form):
                return _PrefixTranslations()

        countries = ComboboxMultiField(
            "Countries",
            suggest=_suggest,
            label_for=_label,
            validators=[MaxItems(max=1)],
        )

    form = F(_formdata({"countries-value": ["FR", "JP"]}))
    assert not form.validate()
    assert form.countries.errors == ["T: Pick at most 1 item."]


def test_validators_get_the_outer_form_and_the_field_data():
    """A validator gets the form that holds the combobox, and its data."""
    seen = {}

    def keep_one(form, field):
        seen["form"] = form
        seen["data"] = field.data
        raise ValidationError("Keep at least one.")

    class F(HtmxForm):
        class Meta:
            csrf = False

        countries = ComboboxMultiField(
            "Countries", suggest=_suggest, label_for=_label, validators=[keep_one]
        )

    form = F(_formdata({"countries-value": ["FR"]}))
    assert not form.validate()
    assert seen == {"form": form, "data": ["FR"]}
    assert form.countries.errors == ["Keep at least one."]


@dataclass(frozen=True)
class _Country:
    code: str


def _country(code):
    if code not in NAME_BY_CODE:
        raise ValueError(code)

    return _Country(code)


def _coerced_multi_form_class():
    return _multi_form_class(coerce=_country, value_for=lambda country: country.code)


def test_multi_coerce_turns_values_into_objects():
    """With coerce, the multi field's data is a list of objects."""
    form = _coerced_multi_form_class()(_formdata({"countries-value": ["FR", "JP"]}))
    assert form.countries.data == [_Country("FR"), _Country("JP")]


def test_multi_value_for_reads_objects_from_any_iterable():
    """value_for turns the initial objects into values, from any iterable."""
    obj = SimpleNamespace(countries=(_Country("FR"), _Country("JP")))
    form = _coerced_multi_form_class()(obj=obj)
    html = str(form.countries())
    assert 'data-value="FR"' in html
    assert 'data-value="JP"' in html


def test_multi_populate_obj_writes_objects():
    """populate_obj writes the coerced objects."""
    form = _coerced_multi_form_class()(_formdata({"countries-value": ["FR"]}))
    obj = SimpleNamespace(countries=[])
    form.populate_obj(obj)
    assert obj.countries == [_Country("FR")]


def test_multi_unknown_value_is_an_error():
    """A value that coerce refuses gives an error and is left out of data."""
    form = _coerced_multi_form_class()(_formdata({"countries-value": ["FR", "XX"]}))
    assert form.countries.data == [_Country("FR")]
    assert not form.validate()
    assert form.countries.errors == ["Not a valid choice."]


def test_single_coerce_turns_the_value_into_an_object():
    """With coerce, the single field's data is an object."""
    form = _single_form_class(coerce=_country, value_for=lambda country: country.code)(
        obj=SimpleNamespace(country=_Country("FR"))
    )
    assert form.country.data == _Country("FR")
    assert 'data-value="FR"' in str(form.country())


def test_single_unknown_value_is_an_error():
    """A value that coerce refuses gives an error and None as data."""
    form = _single_form_class(coerce=_country, value_for=lambda country: country.code)(
        _formdata({"country-value": "XX"})
    )
    assert form.country.data is None
    assert not form.validate()
    assert form.country.errors == ["Not a valid choice."]


def test_multi_reads_a_single_string_as_one_value():
    """A string as initial data is one value, not a list of characters."""
    form = _multi_form_class()(obj=SimpleNamespace(countries="FR"))
    assert form.countries.data == ["FR"]


def test_multi_part_render_kw_survives_a_rerender():
    """The render_kw of each part shows on the page and in the re-rendered part."""
    form_class = _multi_form_class(
        query_render_kw={"class": "prompt"},
        listbox_render_kw={"class": "menu"},
        chips_render_kw={"class": "labels"},
        placeholder="Type",
    )
    html = str(form_class().countries())
    assert 'class="prompt"' in html
    assert 'placeholder="Type"' in html
    assert 'class="menu"' in html
    assert 'class="labels"' in html

    form = form_class(
        _formdata({"countries-query": "fra", "countries-value": []}),
        headers={"HX-Request": "true", "HX-Source": "ul#countries-suggestions"},
    )
    assert 'class="menu"' in form.partial().body


def test_single_value_render_kw():
    """value_render_kw reaches the single field's chip wrapper."""
    form = _single_form_class(value_render_kw={"class": "chip-box"})(
        _formdata({"country-value": "FR"})
    )
    assert 'class="chip-box"' in str(form.country())


def test_combobox_field_is_the_common_base():
    """Both combobox fields are instances of ComboboxField."""
    form = _SingleForm()
    multi = _multi_form_class()()
    assert isinstance(form.country, ComboboxField)
    assert isinstance(multi.countries, ComboboxField)


class _Opaque:
    """A model without equality, like an object loaded twice from a database."""

    def __init__(self, code):
        self.code = code


def _readonly_multi_form_class(**kwargs):
    return _multi_form_class(validators=[ReadOnly()], **kwargs)


def test_readonly_sets_the_flag_and_renders_only_the_chips():
    """ReadOnly makes the field read-only: chips without remove button, no search."""
    form = _readonly_multi_form_class()(obj=SimpleNamespace(countries=["FR"]))
    assert form.countries.flags.readonly
    html = str(form.countries())
    assert 'data-value="FR"' in html
    assert "countries-remove" not in html
    assert "countries-query" not in html
    assert "countries-suggestions" not in html


def test_readonly_accepts_the_unchanged_values():
    """A read-only field validates when the posted values are the initial ones."""
    form = _readonly_multi_form_class()(
        _formdata({"countries-value": ["FR"]}), obj=SimpleNamespace(countries=["FR"])
    )
    assert form.validate()


def test_readonly_rejects_a_forged_value():
    """A read-only field rejects posted values that differ from the initial ones."""
    form = _readonly_multi_form_class()(
        _formdata({"countries-value": ["FR", "JP"]}),
        obj=SimpleNamespace(countries=["FR"]),
    )
    assert not form.validate()
    assert form.countries.errors == ["This field cannot be edited."]


def test_readonly_rejects_a_forged_remove_click():
    """A remove click posted to a read-only field does not pass validation."""
    form = _readonly_multi_form_class()(
        _formdata({"countries-value": ["FR"], "countries-remove": "FR"}),
        obj=SimpleNamespace(countries=["FR"]),
    )
    assert not form.validate()


def test_readonly_compares_the_stored_values_not_the_objects():
    """With coerce, an unchanged read-only field validates even if objects differ."""
    form = _readonly_multi_form_class(coerce=_Opaque, value_for=lambda obj: obj.code)(
        _formdata({"countries-value": ["FR"]}),
        obj=SimpleNamespace(countries=[_Opaque("FR")]),
    )
    assert form.validate()


def test_readonly_can_be_set_at_request_time():
    """Setting the flag and the validator on a bound field makes it read-only."""
    form = _multi_form_class()(obj=SimpleNamespace(countries=["FR"]))
    form.countries.flags.readonly = True
    form.countries.validators.append(ReadOnly())
    assert "countries-remove" not in str(form.countries())


def test_disabled_renders_disabled_hidden_inputs():
    """Disabled renders the chips with disabled hidden inputs and no remove button."""
    form = _multi_form_class(validators=[Disabled()])(
        obj=SimpleNamespace(countries=["FR"])
    )
    html = str(form.countries())
    assert form.countries.flags.disabled
    assert "countries-remove" not in html
    assert 'disabled name="countries-value"' in html


def test_disabled_rejects_a_posted_value():
    """A disabled field rejects any posted value."""
    form = _multi_form_class(validators=[Disabled()])(
        _formdata({"countries-value": ["FR"]})
    )
    assert not form.validate()
    assert form.countries.errors == ["This field is disabled and cannot have a value."]


def test_single_readonly_renders_the_chip_without_remove_button():
    """A read-only single field renders its chip without remove button."""
    form = _single_form_class(validators=[ReadOnly()])(
        obj=SimpleNamespace(country="FR")
    )
    html = str(form.country())
    assert 'data-value="FR"' in html
    assert "country-remove" not in html
    assert "country-query" not in html


def test_disabled_accepts_no_posted_value():
    """A disabled field validates when the browser sends nothing for it."""
    form = _multi_form_class(validators=[Disabled()])(
        _formdata({"countries-query": ""}), obj=SimpleNamespace(countries=["FR"])
    )
    assert form.validate()


def test_readonly_reads_initial_values_given_as_a_dict():
    """Initial data given as the storage dict counts as the read-only values."""
    form = _readonly_multi_form_class()(
        _formdata({"countries-value": ["FR"]}), data={"countries": {"value": ["FR"]}}
    )
    assert form.validate()


def test_flag_set_after_construction_reaches_the_storage_field():
    """A flag set on the bound field shows on its storage field, for custom layouts."""
    form = _multi_form_class()(obj=SimpleNamespace(countries=["FR"]))
    form.countries.flags.readonly = True
    assert form.countries.value.flags.readonly
    assert "countries-remove" not in str(form.countries.value())


def test_combobox_inherits_the_htmx_settings_of_its_form():
    """The combobox parts use the endpoint and inline validation of their form."""

    class F(HtmxForm):
        class Meta:
            csrf = False
            htmx_inline_validation = False

        country = ComboboxSingleField("Country", suggest=_suggest, label_for=_label)

    html = str(F(meta={"htmx_endpoint": "/merge"}).country())
    assert 'hx-post=""' not in html
    assert html.count('hx-post="/merge"') == 2
    assert "blur changed" not in html


def test_combobox_parts_have_no_inline_validation_of_their_own():
    """The combobox parts never validate inline, whatever the trigger of their form."""

    class F(HtmxForm):
        class Meta:
            csrf = False
            htmx_validation_trigger = "input changed delay:500ms"

        countries = ComboboxMultiField("Countries", suggest=_suggest, label_for=_label)

    html = str(F(_formdata({"countries-value": ["FR"]})).countries())
    assert "input changed delay:500ms" not in html
    assert "blur changed" not in html

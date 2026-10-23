"""Composite combobox fields.

Each combobox field is a FormField with its own inner form: a query
input, a search button, a suggestion listbox and a storage field. The
field's data is the stored value (single) or list (multi).
"""

from __future__ import annotations

import functools
import itertools
from collections.abc import Callable
from collections.abc import Iterable
from types import SimpleNamespace
from typing import Any

from markupsafe import escape
from markupsafe import Markup
from wtforms import ButtonField
from wtforms import FormField
from wtforms import HiddenField
from wtforms import SelectChoice
from wtforms import SelectField
from wtforms import SelectMultipleField
from wtforms import StringField
from wtforms.utils import unset_value
from wtforms.validators import Disabled
from wtforms.validators import ReadOnly
from wtforms.validators import ValidationError
from wtforms.widgets import Button
from wtforms.widgets import html_params
from wtforms_htmx import HtmxForm
from wtforms_htmx.mutations import value_add
from wtforms_htmx.mutations import value_remove
from wtforms_htmx.mutations import value_set

from .validators import MaxItems


class QueryInputWidget:
    """Render the search ``<input>`` with the ARIA combobox attributes.

    ``aria-expanded`` is true when the listbox has choices. After a
    click on a suggestion, the input gets ``autofocus``, so a no-JS page
    reload puts the focus back on it.
    """

    def __call__(self, field: Any, **kwargs: Any) -> Markup:
        listbox = field._form.suggestions
        autofocus = kwargs.pop("autofocus", False) or bool(listbox.raw_data)
        attrs: dict[str, Any] = {
            "type": "text",
            "name": field.name,
            "id": field.id,
            "value": field._value(),
            "role": "combobox",
            "aria-autocomplete": "list",
            "aria-haspopup": "listbox",
            "aria-controls": listbox.id,
            "aria-expanded": "true" if listbox.choices else "false",
            "autocomplete": "off",
        }
        if autofocus:
            attrs["autofocus"] = True

        attrs.update(kwargs)
        return Markup(f"<input {html_params(**attrs)}>")


class ListboxWidget:
    """Render the suggestions as a ``<ul role="listbox">``.

    Each suggestion is a ``<li role="option">`` holding a submit button
    rendered by the field's ``option_widget``. ``multi=True`` sets
    ``aria-multiselectable="true"``. Override :meth:`render_option` to
    change the markup of a suggestion.
    """

    def __init__(self, *, multi: bool = False) -> None:
        self._multi = multi

    def __call__(self, field: Any, **kwargs: Any) -> Markup:
        attrs: dict[str, Any] = {"role": "listbox", "id": field.id}
        if self._multi:
            attrs["aria-multiselectable"] = "true"

        attrs.update(kwargs)
        items: list[str] = []
        for opt in field:
            button = functools.partial(opt, **opt._form.htmx_submit_attrs(opt))
            items.append(self.render_option(opt, button))

        return Markup(f"<ul {html_params(**attrs)}>{''.join(items)}</ul>")

    def render_option(self, opt: Any, button: Callable[..., Markup]) -> str:
        """Render one suggestion.

        ``button`` renders the submit button that picks the suggestion.
        It takes the button's ``label`` and HTML attributes.
        """
        li_attrs = html_params(role="option", data_value=opt.choice.value)
        return f"<li {li_attrs}>{button(label=opt.choice.label)}</li>"


def _locked(field: Any) -> bool:
    """Tell whether a storage field is read-only or disabled."""
    return bool(field.flags.readonly or field.flags.disabled)


def _render_chip(
    *,
    name: str,
    value: Any,
    label: Any,
    remove_button: Markup | str,
    disabled: bool = False,
) -> str:
    """Render one chip: a label, a remove button and a hidden input."""
    hidden = html_params(type="hidden", name=name, value=value, disabled=disabled)
    return (
        f"<span {html_params(data_value=value)}>"
        f"<span>{escape(label)}</span>"
        f"{remove_button}"
        f"<input {hidden}>"
        f"</span>"
    )


def _default_remove_label(label: Any) -> str:
    return f"Remove {label}"


class _ChipRenderer:
    _remove_label: Callable[[Any], str]

    def render_chip(self, field: Any, value: Any, label: Any, remove: Any) -> str:
        """Render one chip.

        ``remove`` is the button field that removes the value. Call it with
        ``value`` and the button's ``label`` and HTML attributes. It is
        ``None`` when the field is read-only or disabled.
        """
        button = (
            ""
            if remove is None
            else remove(
                value=value,
                label="×",
                id=False,
                aria_label=self._remove_label(label),
            )
        )
        return _render_chip(
            name=field.name,
            value=value,
            label=label,
            remove_button=button,
            disabled=bool(field.flags.disabled),
        )


class ChipsWidget(_ChipRenderer):
    """Render the stored values of a multi combobox as chips.

    Each chip has a label, a ``×`` remove button and a hidden input
    that sends the value with the form. ``remove_label`` gives the
    accessible name of the remove button from the chip's label. With the
    ``readonly`` or ``disabled`` flag, the chips have no remove button,
    and a disabled field does not send its values. Override
    :meth:`render_chip` to change the markup of a chip.
    """

    def __init__(self, remove_label: Callable[[Any], str] | None = None) -> None:
        self._remove_label = remove_label or _default_remove_label

    def __call__(self, field: Any, **kwargs: Any) -> Markup:
        attrs: dict[str, Any] = {"id": field.id}
        attrs.update(kwargs)
        remove = None if _locked(field) else field._form.remove
        chips = [
            self.render_chip(field, opt.data, opt.label.text, remove) for opt in field
        ]
        return Markup(f"<div {html_params(**attrs)}>{''.join(chips)}</div>")


class SingleChipWidget(_ChipRenderer):
    """Render the value of a single combobox as one removable chip.

    Without a value, it renders an empty hidden input. The chip's ``×``
    clears the value. ``remove_label`` gives the accessible name of the
    remove button from the chip's label. The library ships no CSS: hiding
    the query input while a chip is shown is up to the application.
    Override :meth:`render_chip` to change the markup of the chip.
    """

    def __init__(
        self,
        label_for: Callable[[Any], str],
        remove_label: Callable[[Any], str] | None = None,
    ) -> None:
        self._label_for = label_for
        self._remove_label = remove_label or _default_remove_label

    def __call__(self, field: Any, **kwargs: Any) -> Markup:
        attrs: dict[str, Any] = {"id": field.id}
        attrs.update(kwargs)
        if not field.data:
            hidden = html_params(type="hidden", name=field.name, value="")
            return Markup(f"<div {html_params(**attrs)}><input {hidden}></div>")

        remove = None if _locked(field) else field._form.remove
        chip = self.render_chip(field, field.data, self._label_for(field.data), remove)
        return Markup(f"<div {html_params(**attrs)}>{chip}</div>")


class ComboboxWidget:
    """Render the parts of a combobox in a ``<div>``.

    The order is: the stored values, the query input, the search button
    and the listbox. The chips of a multi combobox show before the query
    input. Without ``search_label``, the search button is left out. A
    read-only or disabled field renders its stored values only.
    """

    def __call__(self, field: Any, **kwargs: Any) -> Markup:
        if field.flags.readonly or field.flags.disabled:
            return Markup(f"<div {html_params(**kwargs)}>{field.value()}</div>")

        search = field.search() if "search" in field.form else ""
        return Markup(
            f"<div {html_params(**kwargs)}>"
            f"{field.value()}"
            f"{field.query()}"
            f"{search}"
            f"{field.suggestions()}"
            f"</div>"
        )


def _pick_value(_form: Any, source: Any, target: Any) -> None:
    """Write the source button's submitted value into the target."""
    target.data = source.raw_data[0]


def _make_pick_label(label_for: Callable[[Any], str]) -> Callable[..., None]:
    """Build a callback that writes the label of the source's value into the target."""

    def _pick(_form: Any, source: Any, target: Any) -> None:
        target.data = label_for(source.raw_data[0])

    return _pick


def _make_single_choices(
    suggest: Callable[[str, Any], Iterable[SelectChoice]],
    label_for: Callable[[Any], str],
    max_n: int,
    close_on_match: bool,
    allow_custom_value: bool,
    custom_value_label: Callable[[str], str] | None,
) -> Callable[..., list[SelectChoice]]:
    """Build the choices callable of the single combobox suggestions.

    No suggestions for an empty query, nor with close_on_match when the
    query is the label of the stored value. With allow_custom_value, a
    "create" choice for the raw query comes last.
    """

    def _choices(form: Any, _field: Any) -> list[SelectChoice]:
        query = (form.query.data or "").strip()
        if not query:
            return []

        if close_on_match and (value := form.value.data) and query == label_for(value):
            return []

        choices = list(itertools.islice(suggest(query, form._parent_form), max_n))
        if allow_custom_value:
            choices = _maybe_append_create(
                choices, query, custom_value_label, extra_existing_labels=()
            )

        return choices

    return _choices


def _make_multi_choices(
    suggest: Callable[[str, Any], Iterable[SelectChoice]],
    label_for: Callable[[Any], str],
    max_n: int,
    cap: int | None,
    allow_custom_value: bool,
    custom_value_label: Callable[[str], str] | None,
) -> Callable[..., list[SelectChoice]]:
    """Build the choices callable of the multi combobox suggestions.

    Picked values are left out, and an empty query or a reached MaxItems
    cap gives no suggestions. With allow_custom_value, a "create" choice
    for the raw query comes last unless the query is already picked.
    """

    def _choices(form: Any, _field: Any) -> list[SelectChoice]:
        query = (form.query.data or "").strip()
        if not query:
            return []

        picked = list(form.value.data or [])
        if cap is not None and len(picked) >= cap:
            return []

        gen = (c for c in suggest(query, form._parent_form) if c.value not in picked)
        choices = list(itertools.islice(gen, max_n))
        if allow_custom_value and query not in picked:
            picked_labels = tuple(str(label_for(v)).lower() for v in picked)
            choices = _maybe_append_create(
                choices, query, custom_value_label, picked_labels
            )

        return choices

    return _choices


def _maybe_append_create(
    choices: list[SelectChoice],
    query: str,
    custom_value_label: Callable[[str], str] | None,
    extra_existing_labels: tuple[str, ...],
) -> list[SelectChoice]:
    """Append a "create" choice for the query.

    Skip it when the query matches the value or label of a choice, or one
    of extra_existing_labels.
    """
    existing_values = {c.value for c in choices}
    existing_labels = {str(c.label).lower() for c in choices}
    if query in existing_values:
        return choices

    lower = query.lower()
    if lower in existing_labels or lower in extra_existing_labels:
        return choices

    label = custom_value_label(query) if custom_value_label else query
    return [*choices, SelectChoice(query, label)]


def _make_value_choices(
    label_for: Callable[[Any], str],
) -> Callable[..., list[SelectChoice]]:
    """Build the choices callable of the chips: one choice per stored value."""

    def _choices(_form: Any, field: Any) -> list[SelectChoice]:
        return [SelectChoice(v, label_for(v)) for v in (field.data or [])]

    return _choices


class ComboboxField(FormField):
    """Base class of :class:`ComboboxSingleField` and :class:`ComboboxMultiField`.

    Use it to recognize a combobox, for example in a field wrapper:
    ``isinstance(field, ComboboxField)``.

    :class:`~wtforms.validators.ReadOnly` and
    :class:`~wtforms.validators.Disabled` work on the whole field: it
    renders its stored values only, and the validation checks the stored
    values, not the objects that ``coerce`` returns.
    """

    _storage_name: str = "value"

    def _stored_values(self) -> list[str]:
        return _values_list(self.form.value.data)

    def _try_coerce(self, value: str) -> tuple[Any, bool]:
        try:
            return self._coerce(value), True
        except (ValueError, TypeError):
            return None, False

    def process(
        self,
        formdata: Any,
        data: Any = unset_value,
        extra_filters: Any = None,
    ) -> None:
        # Resolve the default here so a scalar default gets wrapped too.
        if data is unset_value:
            try:
                data = self.default()
            except TypeError:
                data = self.default

        if isinstance(data, dict):
            stored = data.get(self._storage_name)
        elif data is not None:
            stored = self._to_storage(data)
            data = SimpleNamespace(**{self._storage_name: stored})
        else:
            stored = None

        self._initial_values = _values_list(stored)
        super().process(formdata, data, extra_filters)
        # The storage widget reads the readonly and disabled flags, even when
        # they are set on this field after construction.
        getattr(self.form, self._storage_name).flags = self.flags

    def populate_obj(self, obj: Any, name: str) -> None:
        setattr(obj, name, self.data)

    @property
    def errors(self) -> list[str]:
        return self._combobox_errors

    def validate(self, form: Any, extra_validators: Iterable[Any] = ()) -> bool:
        """Validate the inner form, then run the validators with the outer form."""
        self._combobox_errors = []
        valid = self.form.validate()
        if not all(self._try_coerce(v)[1] for v in self._stored_values()):
            self._combobox_errors.append(self.gettext("Not a valid choice."))

        validators = itertools.chain(self.validators, extra_validators)
        self._run_validation_chain(form, map(_composite_validator, validators))
        return valid and not self._combobox_errors


def _values_list(stored: Any) -> list[str]:
    """Return stored data as a list of values: one value, a list, or none."""
    if not stored:
        return []

    if isinstance(stored, str):
        return [stored]

    return list(stored)


def _check_unchanged(_form: Any, field: ComboboxField) -> None:
    if field._stored_values() != field._initial_values:
        raise ValidationError(field.gettext("This field cannot be edited."))


def _check_not_posted(_form: Any, field: ComboboxField) -> None:
    if getattr(field.form, field._storage_name).raw_data:
        raise ValidationError(
            field.gettext("This field is disabled and cannot have a value.")
        )


def _composite_validator(validator: Any) -> Any:
    """Replace ReadOnly and Disabled with checks on the stored values.

    The originals compare ``data`` and ``object_data``, which a composite
    field does not keep comparable.
    """
    if isinstance(validator, ReadOnly):
        return _check_unchanged

    if isinstance(validator, Disabled):
        return _check_not_posted

    return validator


class _InnerMeta:
    """Meta of the inner forms: their fields have no validators to show inline.

    The other htmx settings come from the form that holds the combobox.
    """

    htmx_inline_validation = False


def _query_render_kw(
    placeholder: str | None, render_kw: dict[str, Any] | None
) -> dict[str, Any] | None:
    """Merge the placeholder into the query input's render_kw."""
    if placeholder:
        return {**(render_kw or {}), "placeholder": placeholder}

    return render_kw


def _build_single_inner_form(
    *,
    choices_cb: Callable[..., list[SelectChoice]],
    pick_label: Callable[..., None],
    label_for: Callable[[Any], str],
    placeholder: str | None,
    search_label: str | None,
    query_widget: Any,
    listbox_widget: Any,
    value_widget: Any,
    query_render_kw: dict[str, Any] | None,
    listbox_render_kw: dict[str, Any] | None,
    value_render_kw: dict[str, Any] | None,
) -> type[HtmxForm]:
    """Construct the inner form class for a single combobox."""
    query_render_kw = _query_render_kw(placeholder, query_render_kw)

    attrs: dict[str, Any] = {
        "query": StringField(render_kw=query_render_kw, widget=query_widget).triggers(
            "suggestions"
        ),
        "suggestions": (
            SelectField(
                choices=choices_cb,
                option_widget=Button(),
                widget=listbox_widget,
                validate_choice=False,
                render_kw=listbox_render_kw,
            )
            .triggers("value", _pick_value)
            .triggers("query", pick_label)
            .triggers("suggestions")
        ),
        "value": HiddenField(widget=value_widget, render_kw=value_render_kw),
        "remove": (
            ButtonField("×")
            .triggers("value", value_set(""))
            .triggers("query", value_set(""))
            .triggers("suggestions")
        ),
    }
    if search_label is not None:
        attrs["search"] = ButtonField(search_label).triggers("suggestions")

    def post_process(self: Any, formdata: Any = None) -> None:
        # Seed the query before the choices callables run again.
        if not self.query.data and self.value.data:
            self.query.data = label_for(self.value.data)

        HtmxForm.post_process(self, formdata)

    attrs["post_process"] = post_process

    attrs["Meta"] = _InnerMeta
    return type("_ComboboxSingleInnerForm", (HtmxForm,), attrs)


class ComboboxSingleField(ComboboxField):
    """Single-value combobox.

    Typing in the query input refreshes the suggestions. Clicking a
    suggestion stores its value and shows its label. ``.data`` is the
    stored value, for example ``"FR"``, or what ``coerce`` makes of it.
    The validators get the form that holds the field, and their errors
    show on the field.

    See :doc:`/how-to/combobox` for the constructor parameters.
    """

    _storage_name = "value"

    def _to_storage(self, data: Any) -> Any:
        return self._value_for(data)

    @property
    def data(self) -> Any:
        raw = self.form.value.data
        if not raw:
            return raw

        return self._try_coerce(raw)[0]

    def __init__(
        self,
        label: str | None = None,
        *,
        suggest: Callable[[str, Any], Iterable[SelectChoice]],
        label_for: Callable[[Any], str] = str,
        coerce: Callable[[str], Any] = str,
        value_for: Callable[[Any], str] = str,
        validators: list | None = None,
        placeholder: str | None = None,
        search_label: str | None = "Search",
        max_suggestions: int = 10,
        close_listbox_on_match: bool = True,
        allow_custom_value: bool = False,
        custom_value_label: Callable[[str], str] | None = None,
        remove_label: Callable[[Any], str] | None = None,
        query_widget: Any = None,
        listbox_widget: Any = None,
        value_widget: Any = None,
        widget: Any = None,
        query_render_kw: dict[str, Any] | None = None,
        listbox_render_kw: dict[str, Any] | None = None,
        value_render_kw: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        inner_form_class = _build_single_inner_form(
            choices_cb=_make_single_choices(
                suggest,
                label_for,
                max_suggestions,
                close_listbox_on_match,
                allow_custom_value,
                custom_value_label,
            ),
            pick_label=_make_pick_label(label_for),
            label_for=label_for,
            placeholder=placeholder,
            search_label=search_label,
            query_widget=query_widget or QueryInputWidget(),
            listbox_widget=listbox_widget or ListboxWidget(),
            value_widget=value_widget
            or SingleChipWidget(label_for=label_for, remove_label=remove_label),
            query_render_kw=query_render_kw,
            listbox_render_kw=listbox_render_kw,
            value_render_kw=value_render_kw,
        )
        super().__init__(inner_form_class, label=label, **kwargs)
        self.validators = list(validators or [])
        for validator in self.validators:
            for flag, value in getattr(validator, "field_flags", {}).items():
                setattr(self.flags, flag, value)

        self._combobox_errors: list[str] = []
        self._coerce = coerce
        self._value_for = value_for
        self._label_for = label_for
        self.widget = widget or ComboboxWidget()


def _build_multi_inner_form(
    *,
    choices_cb: Callable[..., list[SelectChoice]],
    value_choices_cb: Callable[..., list[SelectChoice]],
    placeholder: str | None,
    search_label: str | None,
    query_widget: Any,
    listbox_widget: Any,
    chips_widget: Any,
    query_render_kw: dict[str, Any] | None,
    listbox_render_kw: dict[str, Any] | None,
    chips_render_kw: dict[str, Any] | None,
) -> type[HtmxForm]:
    """Construct the inner form class for a multi combobox."""
    query_render_kw = _query_render_kw(placeholder, query_render_kw)

    attrs: dict[str, Any] = {
        "query": StringField(render_kw=query_render_kw, widget=query_widget).triggers(
            "suggestions"
        ),
        "value": SelectMultipleField(
            choices=value_choices_cb,
            widget=chips_widget,
            validate_choice=False,
            render_kw=chips_render_kw,
        ),
        "suggestions": (
            SelectField(
                choices=choices_cb,
                option_widget=Button(),
                widget=listbox_widget,
                validate_choice=False,
                render_kw=listbox_render_kw,
            )
            .triggers("value", value_add)
            .triggers("query", value_set(""))
            .triggers("suggestions")
        ),
        "remove": ButtonField("×").triggers("value", value_remove),
    }
    if search_label is not None:
        attrs["search"] = ButtonField(search_label).triggers("suggestions")

    attrs["Meta"] = _InnerMeta
    return type("_ComboboxMultiInnerForm", (HtmxForm,), attrs)


class ComboboxMultiField(ComboboxField):
    """Multi-value combobox.

    Clicking a suggestion adds a chip, and a chip's ``×`` removes it.
    Picked values are left out of the suggestions. ``.data`` is a list,
    for example ``["FR", "JP"]``, or what ``coerce`` makes of each value.
    The validators get the form that holds the field, and their errors
    show on the field.

    See :doc:`/how-to/combobox` for the constructor parameters.
    """

    _storage_name = "value"

    def _to_storage(self, data: Any) -> Any:
        if isinstance(data, str):
            data = [data]

        return [self._value_for(item) for item in data]

    @property
    def data(self) -> Any:
        raw = self.form.value.data
        if not raw:
            return raw

        coerced = (self._try_coerce(value) for value in raw)
        return [item for item, ok in coerced if ok]

    def __init__(
        self,
        label: str | None = None,
        *,
        suggest: Callable[[str, Any], Iterable[SelectChoice]],
        label_for: Callable[[Any], str] = str,
        coerce: Callable[[str], Any] = str,
        value_for: Callable[[Any], str] = str,
        validators: list | None = None,
        placeholder: str | None = None,
        search_label: str | None = "Search",
        max_suggestions: int = 10,
        allow_custom_value: bool = False,
        custom_value_label: Callable[[str], str] | None = None,
        remove_label: Callable[[Any], str] | None = None,
        query_widget: Any = None,
        listbox_widget: Any = None,
        chips_widget: Any = None,
        widget: Any = None,
        query_render_kw: dict[str, Any] | None = None,
        listbox_render_kw: dict[str, Any] | None = None,
        chips_render_kw: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        inner_form_class = _build_multi_inner_form(
            choices_cb=_make_multi_choices(
                suggest,
                label_for,
                max_suggestions,
                MaxItems.tightest_cap(validators),
                allow_custom_value,
                custom_value_label,
            ),
            value_choices_cb=_make_value_choices(label_for),
            placeholder=placeholder,
            search_label=search_label,
            query_widget=query_widget or QueryInputWidget(),
            listbox_widget=listbox_widget or ListboxWidget(multi=True),
            chips_widget=chips_widget or ChipsWidget(remove_label=remove_label),
            query_render_kw=query_render_kw,
            listbox_render_kw=listbox_render_kw,
            chips_render_kw=chips_render_kw,
        )
        super().__init__(inner_form_class, label=label, **kwargs)
        self.validators = list(validators or [])
        for validator in self.validators:
            for flag, value in getattr(validator, "field_flags", {}).items():
                setattr(self.flags, flag, value)

        self._combobox_errors: list[str] = []
        self._coerce = coerce
        self._value_for = value_for
        self._label_for = label_for
        self.widget = widget or ComboboxWidget()

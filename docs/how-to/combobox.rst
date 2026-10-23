Combobox
========

A combobox lets users pick a value from a server-filtered list of
suggestions. wtforms-htmx-components ships two composite fields,
:class:`~wtforms_htmx_components.ComboboxSingleField` and
:class:`~wtforms_htmx_components.ComboboxMultiField`. Each one packages the
whole recipe in a single declaration, with no JavaScript required. With
htmx, typing in the search input refreshes the suggestions. Without
JavaScript, a click on the search button refreshes them, and a click on a
suggestion picks it.

The two fields differ in what they store:

- **single value**: one value, shown as a chip and stored in a hidden
  field;
- **multi value**: a list of values, shown as chips with a remove button
  each and stored in a :class:`~wtforms.fields.SelectMultipleField`.

The :ref:`pattern-combobox-recipe` section shows what the fields build
internally, for needs beyond the constructor parameters.

Example
-------

.. automodule:: examples.patterns.combobox
   :no-members:
   :no-index:

The example app declares the four variants in a single
:class:`~wtforms_htmx.HtmxForm`: single and multi, each in strict and
``allow_custom_value`` modes. The four declarations share the same
``suggest`` and ``label_for`` callbacks, and the same custom widgets: a
listbox with flags and chips styled for the example app.

Single, strict
~~~~~~~~~~~~~~

.. code-block:: python

    from wtforms import SelectChoice, SubmitField
    from wtforms_htmx import HtmxForm
    from wtforms_htmx_components import ComboboxSingleField

    class CountryForm(HtmxForm):
        country = ComboboxSingleField(
            "Country",
            suggest=lambda q, _form: (
                SelectChoice(c, n) for c, n in NAME_BY_CODE.items()
                if q.lower() in n.lower()
            ),
            label_for=lambda code: NAME_BY_CODE.get(code, code),
            validators=[valid_country_code],
        )
        save = SubmitField("Save")

``form.country.data`` is the picked value, for example ``"FR"``.
:meth:`~wtforms.Form.populate_obj` writes it to the ``country``
attribute. The validators get the form that holds the field, as for any
field, and ``field.data`` is the picked value. Their errors show in
``form.country.errors``.

Single, allow custom values
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    country = ComboboxSingleField(
        "Country",
        suggest=catalog_search,
        label_for=lambda v: NAME_BY_CODE.get(v, v),
        allow_custom_value=True,
        custom_value_label=lambda q: f'Add "{q}"',
    )

When the query matches no suggestion, the listbox ends with a *create*
option. A click on it stores the query itself. See
:ref:`pattern-combobox-custom-value` for the details.

Multi, strict
~~~~~~~~~~~~~

.. code-block:: python

    from wtforms_htmx_components import ComboboxMultiField

    class CountriesForm(HtmxForm):
        countries = ComboboxMultiField(
            "Countries",
            suggest=catalog_search,
            label_for=lambda code: NAME_BY_CODE.get(code, code),
        )
        save = SubmitField("Save")

``form.countries.data`` is a list, for example ``["FR", "JP"]``. Picked
values do not show in the suggestions. A click on a suggestion adds a chip
and clears the query. A click on a chip's ``×`` removes it.

Multi, allow custom values
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    countries = ComboboxMultiField(
        "Countries",
        suggest=catalog_search,
        label_for=lambda v: NAME_BY_CODE.get(v, v),
        allow_custom_value=True,
        custom_value_label=lambda q: f'Add "{q}"',
    )

A click on the create option adds the query as a chip and clears the
input, like any other suggestion.

View
----

The view is the same as for any other wtforms-htmx form. It returns
:meth:`~wtforms_htmx.HtmxFormMixin.partial` when there is one, and saves
on a click on ``save``:

.. code-block:: python

    @app.route("/combobox", methods=["GET", "POST"])
    def combobox():
        form = CountryForm(request.form or None, obj=state, headers=request.headers)
        if result := form.partial():
            return Response(result.body, headers=result.headers)

        if form.submitter is form.save and form.validate():
            form.populate_obj(state)
            return redirect(url_for("combobox"))

        return render_template("combobox.html", form=form)

Render the field
----------------

``{{ form.country() }}`` renders the chips, the query input, the search
button and the listbox, in this order. To lay them out another way,
render each part on its own, as the example app does:

.. code-block:: jinja

    <div class="combobox-wrap">
      {{ form.country.label }}
      {{ form.country.query() }}
      {{ form.country.search() }}
      {{ form.country.value() }}
      {{ form.country.suggestions() }}
    </div>

Constructor parameters
----------------------

Both fields take the same parameters, except ``close_listbox_on_match``,
which is for the single field only.

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Parameter
     - Purpose
   * - ``suggest``
     - Callable ``(query, form) -> Iterable[SelectChoice]``. Returns the
       options that match the query. ``form`` is the form that holds the
       field, as for validators.
   * - ``label_for``
     - Callable ``(value) -> str``. Returns the label of a stored value,
       shown on the chips and, for the single field, in the query input.
       It gets the value as a string, before ``coerce``. Default:
       :class:`str`.
   * - ``coerce``
     - Callable ``(value) -> object``. Turns a stored value into the
       field's data, for example an identifier into a model. A
       :exc:`ValueError` or :exc:`TypeError` marks the value invalid: the
       field shows "Not a valid choice." and leaves it out of the data.
       Default: :class:`str`.
   * - ``value_for``
     - Callable ``(object) -> str``. Turns the initial data, from ``obj=``
       or ``data=``, into stored values. The multi field accepts any
       iterable. Default: :class:`str`.
   * - ``validators``
     - Validators of the field. They get the form that holds the field.
       Their errors show on the field.
   * - ``placeholder``
     - ``placeholder`` attribute of the query input.
   * - ``search_label``
     - Label of the search button. Default ``"Search"``. ``None`` removes
       the button, so the field needs htmx.
   * - ``max_suggestions``
     - Maximum number of options in the listbox. Default ``10``.
   * - ``close_listbox_on_match`` (single only)
     - When ``True`` (default), the listbox is empty when the query is
       the label of the stored value.
   * - ``allow_custom_value``
     - When ``True``, the listbox ends with a *create* option for the
       query. Default ``False``: only suggested values can be stored. See
       :ref:`pattern-combobox-custom-value`.
   * - ``custom_value_label``
     - Optional ``(query) -> str`` for the label of the create option,
       for example ``lambda q: f'Add "{q}"'``. Default ``None``: the label
       is the query.
   * - ``remove_label``
     - Optional ``(label) -> str`` for the accessible name of a chip's
       remove button, for example ``lambda label: f"Retirer {label}"``.
       Default: ``"Remove <label>"``.
   * - ``query_widget`` / ``listbox_widget`` /
       ``value_widget`` (single) / ``chips_widget`` (multi)
     - Widgets of the parts. Defaults:
       :class:`~wtforms_htmx_components.QueryInputWidget`,
       :class:`~wtforms_htmx_components.ListboxWidget`,
       :class:`~wtforms_htmx_components.SingleChipWidget`,
       :class:`~wtforms_htmx_components.ChipsWidget`.
   * - ``query_render_kw`` / ``listbox_render_kw`` /
       ``value_render_kw`` (single) / ``chips_render_kw`` (multi)
     - HTML attributes of each part, such as CSS classes. They stay on a
       part that htmx re-renders, unlike attributes passed at the call.
   * - ``widget``
     - Widget of the whole field. Default:
       :class:`~wtforms_htmx_components.ComboboxWidget`, for both fields.

Cap the multi selection
-----------------------

:class:`~wtforms_htmx_components.MaxItems` caps the number of picked
values:

.. code-block:: python

    from wtforms_htmx_components import ComboboxMultiField, MaxItems

    countries = ComboboxMultiField(
        "Countries",
        suggest=catalog_search,
        validators=[MaxItems(max=5, message="Pick at most %(max)d countries.")],
    )

This one validator does two things:

- **Validation**: ``form.validate()`` fails with 6 or more picked values,
  and the error shows in ``form.countries.errors``.
- **Listbox cap**: once 5 values are picked, the listbox shows no more
  suggestions. The user cannot pick a sixth value.

Make the field read-only
------------------------

Add :class:`~wtforms.validators.ReadOnly` to the validators. The field
renders its chips only, without remove button, search input or listbox.
The validation fails when the posted values differ from the initial
ones, so a forged request cannot change them:

.. code-block:: python

    from wtforms.validators import ReadOnly

    countries = ComboboxMultiField("Countries", suggest=catalog_search, validators=[ReadOnly()])

To decide per request, set the flag and the validator on the bound
field before rendering:

.. code-block:: python

    form = CountriesForm(request.form or None, obj=user, headers=request.headers)
    if not user.can_edit_countries:
        form.countries.flags.readonly = True
        form.countries.validators.append(ReadOnly())

:class:`~wtforms.validators.Disabled` works the same way, and the field
does not send its values. A custom chips widget reads
``field.flags.readonly`` and ``field.flags.disabled`` on the stored
field, as the default widgets do.

.. _pattern-combobox-custom-value:

Accept free-form values
-----------------------

By default, a combobox is strict: only values returned by ``suggest`` end
up in ``.data``. With ``allow_custom_value=True``, the listbox ends with a
*create* option whose value is the query. A click on it stores the typed
text, like a click on any suggestion:

- The create option shows next to the matching suggestions. The user can
  pick either one.
- The create option is left out when the query is already the value or
  label of a suggestion, so "France" and "Add 'France'" never show
  together. In the multi field, it is also left out when the query is the
  label of a picked value.
- ``label_for`` must accept values outside the catalog. The default
  :class:`str` returns the value as is. For a dict catalog, use
  ``lambda v: NAME_BY_CODE.get(v, v)``.
- The search button only refreshes the listbox. Without JavaScript, the
  create option shows in the listbox like any suggestion.

Customize the rendering
-----------------------

Each widget can be replaced on its own. To change one, subclass it. The
example app's ``FlaggedListboxWidget`` adds a flag to each option of
:class:`~wtforms_htmx_components.ListboxWidget`:

.. code-block:: python

    from markupsafe import Markup
    from wtforms.widgets import html_params
    from wtforms_htmx_components import ListboxWidget

    class FlaggedListboxWidget(ListboxWidget):
        def __call__(self, field, **kwargs):
            attrs = {"role": "listbox", "id": field.id, **kwargs}
            items = []
            for opt in field:
                submit_attrs = opt._form.htmx_submit_attrs(opt)
                label = Markup(flag_img(opt.choice.value)) + opt.choice.label
                button = opt(label=label, **submit_attrs)
                li_attrs = html_params(role="option", data_value=opt.choice.value)
                items.append(f"<li {li_attrs}>{button}</li>")

            return Markup(f"<ul {html_params(**attrs)}>{''.join(items)}</ul>")

Values and labels can come from the request. Build attributes with
:func:`~wtforms.widgets.html_params` and pass text through
:func:`markupsafe.escape`.

Pass it to the constructor:

.. code-block:: python

    country = ComboboxSingleField(
        "Country",
        suggest=...,
        listbox_widget=FlaggedListboxWidget(),
    )

The default widgets set no CSS classes, and the library ships no CSS. They
set the ARIA attributes: ``role="combobox"``, ``role="listbox"``,
``role="option"``, ``aria-controls`` and ``aria-expanded``.

A CSS framework whose components need a strict nesting cannot be applied
as is. The chips live in their own container, which htmx swaps alone, so
they are never direct children of the query input's parent. Reproduce
the look of the component with the application's own classes. The chips container can
take ``display: contents`` to join the flex layout around it.

.. _pattern-combobox-recipe:

What the fields build
---------------------

:class:`~wtforms_htmx_components.ComboboxSingleField` is a
:class:`~wtforms.FormField`. Its inner form holds these fields:

- ``query``: a :class:`~wtforms.StringField` for the search input;
- ``search``: a :class:`~wtforms.ButtonField` that refreshes the
  suggestions without JavaScript;
- ``suggestions``: a :class:`~wtforms.SelectField`. Its ``choices``
  callable calls ``suggest`` on each request. Its ``option_widget`` is
  :class:`~wtforms.widgets.Button`, so each option is a ``<button>``;
- ``value``: a :class:`~wtforms.HiddenField` that stores the picked
  value, shown as a chip;
- ``remove``: a :class:`~wtforms.ButtonField`, the chip's ``×``. It clears
  the value and the query.

The triggers are:

- ``query.triggers("suggestions")``: typing refreshes the listbox;
- ``search.triggers("suggestions")``: same, on a click on the search
  button;
- ``suggestions.triggers("value", pick_value)``: a click on an option
  stores its value;
- ``suggestions.triggers("query", pick_label)``: it also writes the
  option's label in the query input;
- ``suggestions.triggers("suggestions")``: it also refreshes the listbox,
  which is now empty.

The listbox is empty after a pick because the query is the label of the
stored value (``close_listbox_on_match``).

The multi field has the same shape, with these differences:

- ``value`` is a :class:`~wtforms.SelectMultipleField`, shown as chips by
  :class:`~wtforms_htmx_components.ChipsWidget`;
- a click on an option adds its value with
  :func:`~wtforms_htmx.mutations.value_add` and clears the query with
  :func:`~wtforms_htmx.mutations.value_set`;
- ``remove`` removes one value with
  :func:`~wtforms_htmx.mutations.value_remove`.

Build a single combobox by hand
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For a state the fields do not support, build the combobox from plain
fields:

.. code-block:: python

    from wtforms import (
        ButtonField, HiddenField, SelectChoice, SelectField, StringField,
        SubmitField,
    )
    from wtforms.widgets import Button
    from wtforms_htmx import HtmxForm

    def suggest(form, _field):
        q = (form.query.data or "").lower()
        if not q:
            return []

        return [
            SelectChoice(c, n) for c, n in NAME_BY_CODE.items() if q in n.lower()
        ][:10]

    def pick_value(form, source, target):
        target.data = source.raw_data[0]

    def pick_label(form, source, target):
        target.data = NAME_BY_CODE.get(source.raw_data[0], "")

    class CountryForm(HtmxForm):
        query = StringField("Country").triggers("suggestions")
        search = ButtonField("Search").triggers("suggestions")
        suggestions = (SelectField(
            choices=suggest, option_widget=Button(), validate_choice=False,
        )
            .triggers("country", pick_value)
            .triggers("query", pick_label)
            .triggers("suggestions"))
        country = HiddenField()
        save = SubmitField("Save")

:class:`~wtforms_htmx_components.ComboboxSingleField` builds about the
same form. It adds the chip, the ``remove`` button, and the label of the
stored value in the query input on the first render.

ARIA semantics
--------------

The query input follows the ARIA 1.2 combobox pattern:

- ``role="combobox"``;
- ``aria-controls`` set to the listbox id;
- ``aria-autocomplete="list"`` and ``aria-haspopup="listbox"``;
- ``aria-expanded`` set to ``true`` when the listbox has options.

The listbox has ``role="listbox"`` and its children have
``role="option"``. Each option holds a submit button, so a click and the
keyboard both submit it. :kbd:`Tab` moves the focus through the
suggestions, and :kbd:`Enter` activates the focused button. Arrow keys
need JavaScript: see :ref:`pattern-combobox-keyboard`.

Close the listbox on blur
-------------------------

This CSS rule hides the listbox when the focus leaves the wrapper, with no
JavaScript:

.. code-block:: css

    .combobox-wrap:not(:focus-within) [role="listbox"] {
      display: none;
    }

A click on a suggestion still works: the button gets the focus during the
click, so the listbox stays visible until the swap.

Without JavaScript
------------------

Every interaction is a regular form submit:

- a click on the search button refreshes the suggestions;
- a click on a suggestion submits its value;
- a click on a chip's ``×`` submits the remove button with the chip's
  value;
- a click on ``Save`` submits the form and validates it.

Each submit returns the whole page. With htmx, only the field is
swapped. After a pick, the query input gets ``autofocus``, so the focus
comes back to it when the page loads.

.. _pattern-combobox-keyboard:

Add keyboard navigation
-----------------------

The library ships no JavaScript. The example app's
``combobox-enhance.js`` adds these keys on top of :kbd:`Tab` and
:kbd:`Enter`: arrows, :kbd:`Home` and :kbd:`End`, :kbd:`Esc` to close,
:kbd:`Backspace` to remove the last chip, and :kbd:`Enter` to pick the
first suggestion. To use it, copy it to the application's static
directory and load it on the combobox page.

The script finds its elements with these selectors: ``.combobox-wrap``
around the field, ``[role="combobox"]`` for the query input,
``[role="option"] > button`` for the suggestions, ``.chip`` and
``.chip-remove`` for the chips. With custom widgets or another layout,
adapt them in the copy.

It is plain JavaScript. Its handlers sit on the document, so they keep
working after each htmx swap:

.. literalinclude:: ../../examples/static/combobox-enhance.js
   :language: javascript
   :linenos:

Load it with a ``defer`` script tag:

.. code-block:: jinja

    <script src="{{ url_for('static', filename='combobox-enhance.js') }}" defer></script>

:kbd:`Esc` sets a ``data-combobox-closed`` attribute on the wrapper. Add
a CSS rule so that this attribute hides the listbox, even while
``:focus-within`` matches:

.. code-block:: css

    .combobox-wrap:not(:focus-within) [role="listbox"],
    .combobox-wrap[data-combobox-closed="true"] [role="listbox"] {
      display: none;
    }

The keys:

================================ =============================================
Key                              Action
================================ =============================================
:kbd:`↓` in search input         Focus the first suggestion
:kbd:`↓` on a suggestion         Focus the next one (loops to the first)
:kbd:`↑` on a suggestion         Focus the previous one, or the search input
:kbd:`Home` on a suggestion      Focus the first suggestion
:kbd:`End` on a suggestion       Focus the last suggestion
:kbd:`Esc` anywhere in wrapper   Close the listbox and focus the input.
                                 Typing opens it again.
:kbd:`Enter` in search input     Pick the first suggestion, if any. Otherwise,
                                 do nothing, so the form's first button (for
                                 example a chip's ``×``) is not clicked.
:kbd:`Enter` on a suggestion     Activate the submit button (native)
:kbd:`Backspace` in empty input  Remove the last chip (multi field)
================================ =============================================

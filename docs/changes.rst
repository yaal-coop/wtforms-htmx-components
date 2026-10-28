Changes
=======

Unreleased
----------

- The listbox is a ``<div role="listbox">``, and each suggestion is the
  submit button itself, with ``role="option"`` and ``data-value``.
  Before, a ``<li role="option">`` held the button, and screen readers
  announced a button instead of an option. An override of
  ``ListboxWidget.render_option`` now returns ``button(label=...)``
  instead of a ``<li>``.
- ``combobox.js`` keeps the focus in the query input while an option is
  pressed, so a click on a suggestion works in Safari.
- ``combobox.js``: a click in an element with ``data-combobox-field``,
  such as a chip, focuses the query input and opens the listbox.

Version 0.2.0
-------------

Released 2026-10-27

- ``ComboboxWidget`` renders its ``<div>`` with ``data-combobox``, and
  each chip's ``×`` has ``data-combobox-remove``. The example script and
  CSS use these attributes instead of the CSS classes of the example
  app. A template that renders the parts one by one must put
  ``data-combobox`` on the element that holds them.
- The npm package ``wtforms-htmx-components`` ships the combobox script,
  as ``combobox.js``, and the CSS rules it needs, as ``combobox.css``.

Version 0.1.2
-------------

Released 2026-10-27

- After a click on a chip's ``×``, the focus goes back to the query
  input.
- In the example script, a closed listbox opens again on a click on the
  query input, or when the focus comes back to the combobox. Before, it
  stayed hidden until the user typed.

Version 0.1.1
-------------

Released 2026-10-25

- ``min_query_length`` sets the query length from which the listbox
  shows options. With ``0``, a short list shows all its options when
  the query input gets the focus.

Version 0.1.0
-------------

Released 2026-10-23

- Initial release.

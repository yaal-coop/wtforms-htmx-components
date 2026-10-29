<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://wtforms-htmx-components.readthedocs.io/en/latest/_static/logo-dark.svg">
    <img src="https://wtforms-htmx-components.readthedocs.io/en/latest/_static/logo-light.svg" alt="wtforms-htmx">
  </picture>
</p>

# wtforms-htmx-components

Ready-made interactive [WTForms](https://wtforms.readthedocs.io/) fields
built on [wtforms-htmx](https://wtforms-htmx.readthedocs.io/).

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://wtforms-htmx-components.readthedocs.io/en/latest/_static/screencasts/combobox-dark.webp">
    <img src="https://wtforms-htmx-components.readthedocs.io/en/latest/_static/screencasts/combobox-light.webp" width="700" alt="Typing in a combobox shows suggestions. Picking one adds a chip.">
  </picture>
</p>

**Status: alpha, work in progress.**

Each field packages a recipe of several triggers (typing, suggestions,
pick, store, chip) into a single `FormField` declaration. Available now:
the combobox, single and multi value, strict or with free-form values.

## Installation

```sh
pip install wtforms-htmx-components
```

## Example

```python
from wtforms import SelectChoice
from wtforms import SubmitField
from wtforms_htmx import HtmxForm
from wtforms_htmx_components import ComboboxMultiField


def suggest(query, form):
    q = query.lower()
    return [SelectChoice(tag, tag) for tag in CATALOG if q in tag.lower()]


class TagsForm(HtmxForm):
    tags = ComboboxMultiField("Tags", suggest=suggest)
    save = SubmitField()
```

Keyboard navigation is optional. The npm package of the same name
ships the script and its CSS:

```sh
npm install wtforms-htmx-components
```

See the
[combobox guide](https://wtforms-htmx-components.readthedocs.io/en/stable/how-to/combobox/#add-keyboard-navigation).

Run the example app:

```sh
uv sync --group example
uv run python -m examples
```

Then open <http://127.0.0.1:5000/>.

## Links

- Source: <https://github.com/yaal-coop/wtforms-htmx-components>
- Issues: <https://github.com/yaal-coop/wtforms-htmx-components/issues>

## License

BSD-3-Clause. See `LICENSE.rst`.

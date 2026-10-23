# wtforms-htmx-components

Ready-made interactive [WTForms](https://wtforms.readthedocs.io/) fields
built on [wtforms-htmx](https://github.com/yaal-coop/wtforms-htmx).

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

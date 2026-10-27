# wtforms-htmx-components

Keyboard navigation for the combobox of the
[wtforms-htmx-components](https://pypi.org/project/wtforms-htmx-components/)
Python package, per the ARIA combobox pattern.

The combobox works without JavaScript. This package adds:

- arrow keys, <kbd>Home</kbd> and <kbd>End</kbd> to move through the
  suggestions;
- <kbd>Esc</kbd> to close the listbox;
- <kbd>Enter</kbd> in the input to pick the first suggestion;
- <kbd>Backspace</kbd> in an empty input to remove the last chip;
- the focus back on the input after an htmx swap.

## Installation

```sh
npm install wtforms-htmx-components
```

Use the same version as the Python package. The script relies on the
markup that this version renders.

## Usage

Copy `combobox.js` and `combobox.css` to the static directory of the
application, and load them on the pages with a combobox:

```html
<link rel="stylesheet" href="/static/combobox.css">
<script src="/static/combobox.js" defer></script>
```

The files need no build step. jsDelivr also serves them:

```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/wtforms-htmx-components@<VERSION>/combobox.css">
<script src="https://cdn.jsdelivr.net/npm/wtforms-htmx-components@<VERSION>/combobox.js" defer></script>
```

`{{ form.field() }}` renders the markup that the script needs. When the
parts of the field are rendered one by one, put `data-combobox` on the
element that holds them:

```jinja
<div data-combobox>
  {{ form.countries.label }}
  {{ form.countries.value() }}
  {{ form.countries.query() }}
  {{ form.countries.suggestions() }}
</div>
```

## Links

- Documentation: <https://wtforms-htmx-components.readthedocs.io/en/stable/how-to/combobox/>
- Source: <https://github.com/yaal-coop/wtforms-htmx-components>
- Issues: <https://github.com/yaal-coop/wtforms-htmx-components/issues>

## License

BSD-3-Clause.

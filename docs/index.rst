wtforms-htmx-components
=======================

.. image:: _static/logo-light.svg
   :align: center
   :alt: wtforms-htmx

Ready-made interactive :external+wtforms:doc:`WTForms <index>` fields
built on :external+wtforms-htmx:doc:`wtforms-htmx <index>`.

.. screencast:: |examples|/patterns/combobox
   :locator: .demo-area .combobox-search
   :locator-padding: 5 10 60 10
   :viewport-height: 1200
   :autoplay:
   :muted:
   :loop:
   :trim-start:
   :poster:
   :alias: combobox
   :interactions:
     const wait = (ms) => new Promise(r => setTimeout(r, ms));
     const press = (key) => document.activeElement.dispatchEvent(
       new KeyboardEvent('keydown', {key, bubbles: true}));
     const query = document.querySelector('#countries-query');
     // Hide the other comboboxes that show under the listbox.
     for (const cell of document.querySelectorAll('.combobox-cell:not(.demo-area)')) {
       cell.style.visibility = 'hidden';
     }
     await wait(800);
     query.focus();
     for (const c of 'ukr') {
       query.value += c;
       query.dispatchEvent(new Event('input', {bubbles: true}));
       await wait(250);
     }
     await wait(900);
     press('ArrowDown');
     await wait(800);
     document.activeElement.click();
     await wait(1200);
     document.querySelector(
       '#countries-value .chip[data-value="CU"] .chip-remove').click();
     await wait(1500);
     document.activeElement.blur();
     await wait(500);

Each field packages a recipe of several triggers (typing, suggestions,
pick, store, chip) into a single ``FormField`` declaration. It needs no
custom widget and no JavaScript.

.. toctree::
    :caption: How-to guides
    :maxdepth: 1

    how-to/combobox

.. toctree::
    :caption: Reference
    :maxdepth: 1

    api
    combobox-js

.. toctree::
    :caption: Changelog
    :maxdepth: 1

    changes

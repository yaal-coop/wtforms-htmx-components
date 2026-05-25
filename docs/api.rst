API
===

.. module:: wtforms_htmx_components

Composite fields
----------------

.. autoclass:: ComboboxSingleField

.. autoclass:: ComboboxMultiField

.. autoclass:: ComboboxField

Sub-widgets
-----------

Subclass these widgets to change the rendering. Pass an instance to the
field constructor with the ``query_widget=`` / ``listbox_widget=`` /
``value_widget=`` / ``chips_widget=`` / ``widget=`` parameters.

.. autoclass:: QueryInputWidget

.. autoclass:: ListboxWidget

.. autoclass:: ChipsWidget

.. autoclass:: SingleChipWidget

.. autoclass:: ComboboxWidget

Validators
----------

.. autoclass:: MaxItems

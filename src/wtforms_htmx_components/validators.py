"""Validators for list fields."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from wtforms.validators import ValidationError


class MaxItems:
    """Check that a list field has at most ``max`` items.

    Works with any field whose data supports :func:`len`, such as
    :class:`~wtforms.fields.SelectMultipleField` or
    :class:`~wtforms.fields.FieldList`. Empty data passes: add
    :class:`~wtforms.validators.DataRequired` to require a value.
    ``message`` can use the ``%(max)d`` placeholder. The default message
    goes through the translations of the form.

    :class:`~wtforms_htmx_components.ComboboxMultiField` also reads this
    validator and shows no more suggestions once the cap is reached.
    """

    def __init__(self, max: int, message: str | None = None) -> None:
        if max < 0:
            raise ValueError("MaxItems(max=…) must be non-negative")

        self.max = max
        self.message = message

    def __call__(self, form: Any, field: Any) -> None:
        data = field.data
        if not data:
            return

        if len(data) <= self.max:
            return

        message = self.message
        if message is None:
            message = field.ngettext(
                "Pick at most %(max)d item.", "Pick at most %(max)d items.", self.max
            )

        message = message % {"max": self.max}

        raise ValidationError(message)

    @classmethod
    def tightest_cap(cls, validators: Iterable[Any] | None) -> int | None:
        """Return the smallest ``max`` across all ``MaxItems`` in ``validators``, or ``None``."""
        caps = [v.max for v in validators or [] if isinstance(v, cls)]
        return min(caps) if caps else None

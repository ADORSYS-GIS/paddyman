"""CasingRule — converts raw entity names to PascalCase canonical identifiers.

Handles all common name formats encountered across parsers:

- ``"Payment Initiation"``     → ``"PaymentInitiation"``
- ``"payment_initiation"``     → ``"PaymentInitiation"``
- ``"payment-initiation"``     → ``"PaymentInitiation"``
- ``"paymentInitiation"``      → ``"PaymentInitiation"``
- ``"PAYMENT_INITIATION"``     → ``"PaymentInitiation"``
- ``"PaymentAPIController"``   → ``"PaymentApiController"``
- ``"PaymentController"``      → ``"PaymentController"`` (already correct)
"""
from __future__ import annotations

import re

# Split on whitespace, underscores, hyphens, dots, slashes, backslashes, pipes
_SEPARATOR = re.compile(r"[\s_\-./\\|]+")

# Insert space before an uppercase letter that immediately follows a lowercase
# letter or digit — e.g. "paymentController" → "payment Controller"
_LOWER_TO_UPPER = re.compile(r"([a-z\d])([A-Z])")

# Insert space before an uppercase letter that starts a word after an uppercase
# letter — e.g. "APIController" → "API Controller"
_UPPER_SEQ = re.compile(r"([A-Z])([A-Z][a-z])")


def to_pascal_case(name: str) -> str:
    """Convert *name* to PascalCase.

    Splits on explicit separators and on camelCase/ALLCAPS transitions, then
    title-cases each segment and joins without separator.
    """
    if not name or not name.strip():
        return ""
    # Expand camelCase / ALLCAPS transitions to space-separated segments
    spaced = _LOWER_TO_UPPER.sub(r"\1 \2", name)
    spaced = _UPPER_SEQ.sub(r"\1 \2", spaced)
    # Split on separators (now including the injected spaces)
    parts = _SEPARATOR.split(spaced.strip())
    return "".join(p.capitalize() for p in parts if p)


class CasingRule:
    """Normalise entity names to PascalCase."""

    def apply(
        self,
        name: str,
        entity_type: str,
        source_parser: str,
    ) -> str | None:
        """Return the PascalCase form of *name*, or ``None`` when name is empty."""
        _ = (entity_type, source_parser)
        result = to_pascal_case(name)
        return result if result else None

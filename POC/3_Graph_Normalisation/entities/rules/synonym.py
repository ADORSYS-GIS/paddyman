"""SynonymRule — map normalised names to a canonical representative.

Synonyms are defined as groups: each group has a canonical name (the key) and
a list of equivalent names that resolve to that canonical name.  Lookup is
case-insensitive.

The default table covers XS2A / PSD2 / Berlin Group domain concepts and is
intentionally minimal.  Extend it by passing a custom ``synonyms`` dict to
:class:`SynonymRule` at construction time.
"""
from __future__ import annotations

# Default synonym groups for the XS2A / PSD2 / Berlin Group domain.
# Key   → canonical name (returned when any alias in the list matches).
# Value → list of equivalent names (including the canonical name itself).
DEFAULT_SYNONYMS: dict[str, list[str]] = {
    "PaymentInitiation": [
        "Payment",
        "PaymentController",
        "InitiatePayment",
        "PaymentService",
        "PostPayments",
        "PostPayment",
        "PaymentRequest",
        "PaymentInitiationService",
        "PaymentInitiation",
    ],
    "AccountInformation": [
        "Account",
        "AccountController",
        "AccountInformationService",
        "GetAccounts",
        "GetAccount",
        "AccountService",
        "AccountInformation",
    ],
    "ConsentManagement": [
        "Consent",
        "ConsentController",
        "ConsentService",
        "ConsentManagementService",
        "CreateConsent",
        "PostConsents",
        "ConsentManagement",
    ],
    "FundsConfirmation": [
        "Funds",
        "FundsController",
        "FundsConfirmationService",
        "CheckFunds",
        "FundsConfirmation",
    ],
    "TransactionHistory": [
        "Transaction",
        "TransactionController",
        "GetTransactions",
        "TransactionService",
        "TransactionHistory",
    ],
}


class SynonymRule:
    """Map normalised names to their canonical synonym."""

    def __init__(self, synonyms: dict[str, list[str]] | None = None) -> None:
        table = synonyms if synonyms is not None else DEFAULT_SYNONYMS
        # Build reverse lookup: alias_lower → canonical_name
        self._lookup: dict[str, str] = {}
        for canonical, aliases in table.items():
            self._lookup[canonical.lower()] = canonical
            for alias in aliases:
                self._lookup[alias.lower()] = canonical

    def apply(
        self,
        name: str,
        entity_type: str,
        source_parser: str,
    ) -> str | None:
        """Return the canonical name if *name* is a known synonym, else ``None``."""
        _ = (entity_type, source_parser)
        if not name:
            return None
        return self._lookup.get(name.lower())

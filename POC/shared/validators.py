"""Validation helpers used across pipeline stages.

Currently provides bundle contract validation used by loaders and
aggregators to ensure parser/normalized bundles advertise the expected
contract before being processed.
"""
from __future__ import annotations

from typing import Any, Mapping


class BundleValidationError(ValueError):
    """Raised when a bundle fails validation."""


def _get_contract(bundle: Any) -> str | None:
    """Return the contract string from a bundle dict-like object, or None."""
    if bundle is None:
        return None
    # Accept either a mapping (raw json) or an object with attribute
    try:
        if isinstance(bundle, Mapping):
            vm = bundle.get("version_metadata") or {}
        else:
            vm = getattr(bundle, "version_metadata", None) or {}
        return vm.get("contract")
    except Exception:
        return None


def validate_bundle_contract(bundle: Any, expected_contract: str) -> None:
    """Validate that *bundle* advertises the *expected_contract*.

    - *bundle* may be a dict (parsed JSON) or an object exposing
      a `version_metadata` attribute (e.g. `NormalizedJson`).
    - Raises `BundleValidationError` if contract is missing or mismatched.
    """
    contract = _get_contract(bundle)
    if contract is None:
        raise BundleValidationError("Missing version_metadata.contract in bundle")
    if str(contract) != expected_contract:
        raise BundleValidationError(f"Unexpected bundle contract '{contract}', expected '{expected_contract}'")

"""Unit tests for shared.validators.validate_bundle_contract."""
from __future__ import annotations

import pytest

from shared.validators import validate_bundle_contract, BundleValidationError


def test_validate_accepts_matching_contract() -> None:
    bundle = {"version_metadata": {"contract": "parser-json", "version": "1.0"}}
    # Should not raise
    validate_bundle_contract(bundle, "parser-json")


def test_validate_raises_on_missing_contract() -> None:
    bundle = {}
    with pytest.raises(BundleValidationError):
        validate_bundle_contract(bundle, "parser-json")


def test_validate_raises_on_mismatch() -> None:
    bundle = {"version_metadata": {"contract": "normalized-json", "version": "1.0"}}
    with pytest.raises(BundleValidationError):
        validate_bundle_contract(bundle, "parser-json")

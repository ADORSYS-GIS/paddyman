"""Configurable regex rules for content-based version detection.

Rules are applied in priority order — most-specific patterns first.
To add a new rule, append a :class:`VersionRule` entry to
:data:`CONTENT_RULES`; no other file needs to change.
"""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class VersionRule:
    """A single regex-based version detection rule.

    Attributes:
        name:    Unique rule identifier used as the ``version_source`` label.
        pattern: Compiled regex whose **first capture group** contains the raw
                 version digits (optional leading ``v``/``V`` is stripped).
        prefix:  String prepended to the captured digits (default ``"v"``).
    """

    name: str
    pattern: re.Pattern[str]
    prefix: str = "v"

    def extract(self, text: str) -> str | None:
        """Return a normalised version tag if *pattern* matches in *text*.

        Returns ``None`` when no match is found or the captured group is empty.
        """
        m = self.pattern.search(text)
        if m is None:
            return None
        groups = [g for g in m.groups() if g is not None]
        if not groups:
            return None
        raw = groups[0].lstrip("vV")
        return self.prefix + raw if raw else None


# ---------------------------------------------------------------------------
# Built-in rules — ordered from most-specific to least-specific.
# Extend by appending entries; do not reorder existing entries.
# ---------------------------------------------------------------------------
CONTENT_RULES: list[VersionRule] = [
    # PSD2 v1.3.16 / psd2 1.3 — \b prevents matching inside NextGenPSD2
    VersionRule(
        name="psd2",
        pattern=re.compile(r"\bPSD2\s+[Vv]?(\d+(?:\.\d+)+)", re.IGNORECASE),
    ),
    # Berlin Group V2 / Berlin Group 1.3
    VersionRule(
        name="berlin_group",
        pattern=re.compile(
            r"Berlin\s+Group\s+[Vv]?(\d+(?:\.\d+)*)", re.IGNORECASE
        ),
    ),
    # NextGenPSD2 1.3 / NextGenPSD2 v2
    VersionRule(
        name="nextgenpsd2",
        pattern=re.compile(
            r"NextGenPSD2\s+[Vv]?(\d+(?:\.\d+)*)", re.IGNORECASE
        ),
    ),
    # openapi: 3.0.1 / OpenAPI 3.0
    VersionRule(
        name="openapi",
        pattern=re.compile(
            r"openapi[:\s]+[Vv]?(\d+(?:\.\d+)+)", re.IGNORECASE
        ),
    ),
    # v1.3.16, V2.0 — prefixed semantic
    VersionRule(
        name="version_prefix_semantic",
        pattern=re.compile(r"\b[Vv](\d+\.\d+(?:\.\d+)*)\b"),
    ),
    # V2, v3 — prefixed major-only
    VersionRule(
        name="version_prefix_major",
        pattern=re.compile(r"\b[Vv](\d+)\b"),
    ),
    # 1.3.16, 3.0.1 — bare semantic (lowest priority, prone to false positives)
    VersionRule(
        name="semantic_version",
        pattern=re.compile(r"\b(\d+\.\d+(?:\.\d+)*)\b"),
    ),
]

"""Convert relationship model objects to NormalizedJson-compatible dicts.

This module provides conversion functions that transform JavaRelationship and
DependencyRelationship objects into plain dict representations suitable for
inclusion in `NormalizedJson.relationships`.
"""
from __future__ import annotations

from java_parser.relationships.models import JavaRelationship
from java_parser.di.models import DependencyRelationship


def java_rel_to_dict(rel: JavaRelationship) -> dict:
    """Convert a single JavaRelationship into the normalised relationship dict.

    Produces a stable `source` and attempts a best-effort `target` resolution.
    When resolution is not possible the original receiver text is preserved
    and ``target_resolved`` is set to ``False``.
    """
    # Source identifier: package.Class#method (or Class#method)
    src_method = rel.source_method or ""
    if rel.package:
        source_id = f"{rel.package}.{rel.source}#{src_method}" if src_method else f"{rel.package}.{rel.source}"
    else:
        source_id = f"{rel.source}#{src_method}" if src_method else f"{rel.source}"

    # Target resolution: best-effort heuristics
    target_resolved = True
    if rel.target_class is None:
        # Self-call without explicit receiver
        if rel.package:
            target_id = f"{rel.package}.{rel.source}#{rel.target_method}"
        else:
            target_id = f"{rel.source}#{rel.target_method}"
    else:
        tc = rel.target_class
        # Fully-qualified receiver (contains a dot)
        if "." in tc:
            target_id = f"{tc}#{rel.target_method}" if rel.target_method else tc
        # Likely a type name (PascalCase) — assume same package
        elif tc and tc[0].isupper():
            target_id = f"{rel.package}.{tc}#{rel.target_method}" if rel.package else f"{tc}#{rel.target_method}"
        # Receiver equals source simple name
        elif tc == rel.source:
            target_id = f"{rel.package}.{tc}#{rel.target_method}" if rel.package else f"{tc}#{rel.target_method}"
        else:
            # Unresolved receiver (field/variable) — keep original textual form
            target_id = rel.target
            target_resolved = False

    d: dict = {
        "type": rel.relationship_type,
        "source": source_id,
        "target": target_id,
        "repository": rel.repository,
        "module": rel.module,
        "package": rel.package,
        "file_path": rel.file_path,
        "source_method": rel.source_method,
        "target_method": rel.target_method,
        "target_class": rel.target_class,
    }
    if not target_resolved:
        d["target_resolved"] = False
    return d


def struct_rel_to_dict(rel: JavaRelationship, name_map: dict) -> dict:
    """Convert EXTENDS / IMPLEMENTS relationship into dict with module resolution."""
    # Fully-qualified source
    source_fq = f"{rel.package}.{rel.source}" if rel.package else rel.source

    # Resolve target to fqname if possible
    target = rel.target
    target_fq = target
    target_module: str | None = None
    if "." not in target:
        candidates = name_map.get(target, [])
        if len(candidates) == 1:
            target_fq, target_module = candidates[0]
        elif len(candidates) > 1:
            # Prefer same package
            pref = [c for c in candidates if c[0].startswith(f"{rel.package}.")]
            if pref:
                target_fq, target_module = pref[0]
            else:
                target_fq = candidates[0][0]
                target_module = candidates[0][1]
        else:
            target_module = None

    d = {
        "type": rel.relationship_type,
        "source": source_fq,
        "target": target_fq,
        "repository": rel.repository,
        "module": rel.module,
        "package": rel.package,
        "file_path": rel.file_path,
    }
    d["target_module"] = target_module
    return d


def di_rel_to_dict(rel: DependencyRelationship, name_map: dict) -> dict:
    """Convert DependencyRelationship into output dict. Map type -> INJECTS.

    Attempts to fully qualify source and target classes when possible.
    """
    source_fq = f"{rel.package}.{rel.source}" if rel.package else rel.source
    target = rel.target
    target_fq = target
    target_module: str | None = None
    if "." not in target:
        candidates = name_map.get(target, [])
        if candidates:
            target_fq, target_module = candidates[0]
    else:
        target_fq = target

    d = {
        "type": "INJECTS",
        "source": source_fq,
        "target": target_fq,
        "injection_type": rel.injection_type,
        "field_name": rel.field_name,
        "repository": rel.repository,
        "module": rel.module,
        "package": rel.package,
        "file_path": rel.file_path,
    }
    d["target_module"] = target_module
    return d

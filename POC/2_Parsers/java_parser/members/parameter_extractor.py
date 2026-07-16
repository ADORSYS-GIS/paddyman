"""Parameter extraction from formal parameter lists.

Shared by both :mod:`method_extractor` and :mod:`constructor_extractor`.
"""
from __future__ import annotations

import logging
from tree_sitter import Node

from java_parser.java_ast.node_helpers import node_text
from java_parser.java_ast.annotation_value_extractor import extract_annotations_from_node

from .models import JavaParameter
from ._helpers import extract_type_str

logger = logging.getLogger(__name__)

_VARARG_INDICATOR = "..."


def _is_vararg(param_node: Node) -> bool:
    """Return True when *param_node* declares a vararg parameter."""
    for child in param_node.children:
        if child.type == "...":
            return True
        # Spread parameter type nodes contain "..."
        if child.type == "spread_parameter":
            return True
    return False


def _param_type(param_node: Node) -> str:
    """Return the type string for a formal_parameter node."""
    for child in param_node.children:
        if child.type in (
            "type_identifier", "generic_type", "integral_type",
            "boolean_type", "array_type", "floating_point_type",
            "scoped_type_identifier", "annotated_type",
        ):
            return extract_type_str(child)
        # spread_parameter contains a type followed by "..."
        if child.type == "spread_parameter":
            for sub in child.children:
                if sub.type != "...":
                    return extract_type_str(sub) + "..."
    return ""


def _param_name(param_node: Node) -> str:
    """Return the identifier for a formal_parameter node."""
    # Name is the last identifier child
    name = ""
    for child in param_node.children:
        if child.type == "identifier":
            name = node_text(child)
    return name


def extract_parameters(formal_params_node: Node) -> list[JavaParameter]:
    """Extract all parameters from a ``formal_parameters`` tree-sitter node.

    Args:
        formal_params_node: A ``formal_parameters`` node containing
                            ``formal_parameter`` children.

    Returns:
        Ordered list of :class:`JavaParameter` instances.
    """
    params: list[JavaParameter] = []
    for child in formal_params_node.children:
        if child.type not in ("formal_parameter", "spread_parameter"):
            continue
        try:
            ptype = _param_type(child)
            pname = _param_name(child)
            vararg = _is_vararg(child) or child.type == "spread_parameter"

            # Extract parameter annotations (if any)
            anns = extract_annotations_from_node(child)

            if pname:
                params.append(
                    JavaParameter(
                        name=pname,
                        type=ptype,
                        is_vararg=vararg,
                        annotations=anns,
                        position=len(params),
                    )
                )
        except Exception as exc:  # noqa: BLE001
            logger.debug("Skipping malformed parameter: %s", exc)
    return params

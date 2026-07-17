"""Type parsing helpers for Java field type declarations."""
from __future__ import annotations


def parse_type_declaration(type_str: str) -> tuple[str, bool, bool, list[str]]:
    """Parse a Java type string into (base_type, is_collection, is_generic, generic_arguments).

    Args:
        type_str: Java type declaration (e.g., "List<String>", "int[]").

    Returns:
        Tuple of (base_type, is_collection, is_generic, generic_arguments).
    """
    generic_args: list[str] = []
    is_generic = "<" in type_str

    if is_generic:
        start_idx = type_str.index("<")
        inner = type_str[start_idx + 1 : type_str.rindex(">")]
        depth = 0
        current_arg = []
        for char in inner:
            if char == "<":
                depth += 1
            elif char == ">":
                depth -= 1
            elif char == "," and depth == 0:
                generic_args.append("".join(current_arg).strip())
                current_arg = []
                continue
            current_arg.append(char)
        if current_arg:
            generic_args.append("".join(current_arg).strip())

    result = []
    depth = 0
    for char in type_str:
        if char == "<":
            depth += 1
        elif char == ">":
            depth -= 1
        elif char not in ("[", "]") and depth == 0:
            result.append(char)
    base = "".join(result).strip()
    is_collection = base in {"List", "Set", "Map", "Queue", "Deque", "Stack"}

    return base, is_collection, is_generic, generic_args

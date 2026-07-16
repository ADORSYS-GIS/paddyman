"""URL classification utilities for markdown references.

Classifies reference URLs as external, relative, anchor, or cross-document.
For URL parsing utilities, see reference_url_utils.py.
"""
from __future__ import annotations

from pathlib import Path


def is_external_url(url: str) -> bool:
    """Check if URL is external (http://, https://, ftp://, etc.).

    Args:
        url: URL string to check.

    Returns:
        True if URL uses an external protocol scheme.

    Examples:
        >>> is_external_url("https://example.com")
        True
        >>> is_external_url("../docs/other.md")
        False
        >>> is_external_url("#section")
        False
    """
    if not url:
        return False
    
    # Common external protocols
    external_schemes = (
        "http://",
        "https://",
        "ftp://",
        "ftps://",
        "mailto:",
        "tel:",
        "ssh://",
        "git://",
    )
    
    return url.startswith(external_schemes)


def is_relative_path(url: str) -> bool:
    """Check if URL is a relative file path.

    Args:
        url: URL string to check.

    Returns:
        True if URL is a relative path (not external, not anchor).

    Examples:
        >>> is_relative_path("../docs/other.md")
        True
        >>> is_relative_path("./file.md")
        True
        >>> is_relative_path("images/logo.png")
        True
        >>> is_relative_path("https://example.com")
        False
        >>> is_relative_path("#section")
        False
    """
    if not url:
        return False
    
    # Not relative if it's external or an anchor
    if is_external_url(url) or is_anchor(url):
        return False
    
    # Check if it's an absolute path
    if url.startswith("/"):
        return False
    
    return True


def is_anchor(url: str) -> bool:
    """Check if URL is an internal anchor (#section).

    Args:
        url: URL string to check.

    Returns:
        True if URL is an internal anchor reference.

    Examples:
        >>> is_anchor("#section-heading")
        True
        >>> is_anchor("https://example.com#section")
        False
        >>> is_anchor("../docs/other.md#section")
        False
    """
    if not url or url == "#":
        return False
    
    # Pure anchor must start with # and have no other URL components
    return url.startswith("#") and not any(
        c in url for c in ["://", "?", "&"]
    )


def is_cross_document(url: str) -> bool:
    """Check if URL references another markdown document.

    Args:
        url: URL string to check.

    Returns:
        True if URL points to a markdown file.

    Examples:
        >>> is_cross_document("../docs/other.md")
        True
        >>> is_cross_document("./README.md")
        True
        >>> is_cross_document("docs/spec.markdown")
        True
        >>> is_cross_document("image.png")
        False
        >>> is_cross_document("https://example.com/doc.md")
        False
    """
    if not url or is_external_url(url) or is_anchor(url):
        return False
    
    # Extract the path component if there's an anchor
    path_part = url.split("#")[0] if "#" in url else url
    
    # Check if the extension is a markdown variant
    markdown_extensions = {".md", ".markdown", ".mdown", ".mkd"}
    
    try:
        path = Path(path_part)
        return path.suffix.lower() in markdown_extensions
    except Exception:
        return False


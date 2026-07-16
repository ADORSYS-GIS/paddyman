"""Markdown structure extraction.

Extract headings, sections, references, tables, lists, paragraphs and
frontmatter from complete Markdown documents. This module operates on
document dictionaries and returns enhanced structures that are compatible
with downstream extractors.
"""
from __future__ import annotations

import re
from typing import Iterable, List, Dict


HEADING_RE = re.compile(r"^(#{1,6})\s*(.+)", flags=re.MULTILINE)
LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
REF_DEF_RE = re.compile(r"^\[([^\]]+)\]:\s*(\S+)", flags=re.MULTILINE)
# Normative/bibliographic citations: [RFC6749], [HAL], [XS2A-OR], [PSD2], etc.
# Must start with an uppercase letter to avoid matching JSON/regex brackets.
CITATION_RE = re.compile(r"\[([A-Z][A-Z0-9\-]{1,30})\]")
# YAML/TOML frontmatter block delimited by --- or +++
FRONTMATTER_RE = re.compile(r"^(?:---|\+\+\+)\n(.*?)\n(?:---|\+\+\+)\s*$", re.DOTALL)


def _extract_headings(text: str) -> List[Dict]:
    return [
        {"level": len(m.group(1)), "text": m.group(2).strip()}
        for m in HEADING_RE.finditer(text)
    ]


def _extract_links(text: str) -> Dict:
    """Extract all links, reference definitions, and normative citations.

    Parses markdown text to find:
    - Inline links: [text](url)
    - Reference definitions: [id]: url
    - Normative citations: [RFC6749], [PSD2], etc.

    Args:
        text: Markdown text to parse.

    Returns:
        Dict with three keys:
            - inline: List of dicts with 'text' and 'url' keys
            - definitions: List of dicts with 'id' and 'url' keys
            - citations: Sorted, deduplicated list of citation keys

    Example:
        >>> _extract_links("See [RFC6749] and [PSD2]")
        {"inline": [], "definitions": [], "citations": ["PSD2", "RFC6749"]}
    """
    links = [{"text": m.group(1), "url": m.group(2)} for m in LINK_RE.finditer(text)]
    refs = [{"id": m.group(1), "url": m.group(2)} for m in REF_DEF_RE.finditer(text)]
    # Deduplicate and sort citations for determinism
    citations = sorted(set(m.group(1) for m in CITATION_RE.finditer(text)))
    return {"inline": links, "definitions": refs, "citations": citations}


def _extract_frontmatter(text: str) -> Dict:
    """Parse YAML frontmatter from the top of a Markdown document.

    Returns a dict of key-value pairs extracted from the frontmatter block,
    or an empty dict when no frontmatter is present or parsing fails.
    """
    m = FRONTMATTER_RE.match(text.lstrip())
    if not m:
        return {}
    try:
        import yaml  # type: ignore
        data = yaml.safe_load(m.group(1))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _extract_lists(text: str) -> List[Dict]:
    """Extract bullet and numbered lists from Markdown text.

    Returns a list of list-block dicts, each containing:
      - ``ordered``: True for numbered lists, False for bullet lists
      - ``items``: list of item text strings (without the list marker)

    Each contiguous block of same-type list items becomes one entry.
    """
    lines = text.splitlines()
    bullet_re = re.compile(r"^(\s*)[-*+]\s+(.*)")
    ordered_re = re.compile(r"^(\s*)\d+[.)]\s+(.*)")

    results: List[Dict] = []
    buf: List[str] = []
    current_ordered: bool | None = None

    def flush():
        nonlocal buf, current_ordered
        if buf:
            results.append({"ordered": bool(current_ordered), "items": list(buf)})
        buf = []
        current_ordered = None

    for line in lines:
        bm = bullet_re.match(line)
        om = ordered_re.match(line)
        if bm:
            if current_ordered is True:
                flush()
            current_ordered = False
            buf.append(bm.group(2).strip())
        elif om:
            if current_ordered is False:
                flush()
            current_ordered = True
            buf.append(om.group(2).strip())
        else:
            # Non-list line — end current block if any
            if buf:
                flush()

    flush()
    return results


def _extract_paragraphs(text: str) -> List[str]:
    """Extract non-heading, non-list, non-code-block prose paragraphs.

    Returns a list of paragraph strings. Each paragraph is a contiguous
    block of non-blank lines that does not begin with a Markdown heading
    marker, list marker, table pipe, or code-fence.
    """
    _SKIP_PREFIXES = ("#", "-", "*", "+", "|", "```", "~~~", ">")
    _ORDERED_RE = re.compile(r"^\d+[.)]\s")

    paragraphs: List[str] = []
    buf: List[str] = []

    def flush():
        if buf:
            paragraphs.append(" ".join(buf).strip())
        buf.clear()

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            flush()
            continue
        if any(stripped.startswith(p) for p in _SKIP_PREFIXES):
            flush()
            continue
        if _ORDERED_RE.match(stripped):
            flush()
            continue
        buf.append(stripped)

    flush()
    return [p for p in paragraphs if p]


def _extract_tables(text: str) -> List[Dict]:
    """Extract GFM pipe tables from markdown text as structured data.

    Parses GitHub Flavored Markdown pipe tables into structured dicts with
    headers and rows. Each table must have a header row, separator row, and
    at least one data row.

    Args:
        text: Markdown text to parse.

    Returns:
        List of table dicts, each containing:
            - headers: List of column header strings (stripped)
            - rows: List of row lists, each row is a list of cell strings (stripped)
        Returns empty list if no valid tables are found.

    Example:
        Input text:
            | Name | Age |
            |------|-----|
            | Alice| 30  |
            | Bob  | 25  |

        Output:
            [{"headers": ["Name", "Age"], "rows": [["Alice", "30"], ["Bob", "25"]]}]
    """
    lines = text.splitlines()
    tables: List[Dict] = []
    buf: List[str] = []
    in_table = False

    def flush_buf():
        nonlocal buf
        if buf:
            table = _parse_table_lines(buf)
            if table:
                tables.append(table)
            buf.clear()

    for line in lines:
        if "|" in line:
            buf.append(line)
            in_table = True
        elif in_table:
            # Non-table line encountered, flush current table
            flush_buf()
            in_table = False

    if in_table:
        flush_buf()

    return tables


def _parse_table_lines(lines: List[str]) -> Dict | None:
    """Parse a buffer of table lines into structured table data.

    Args:
        lines: List of raw markdown table lines (with pipes).

    Returns:
        Dict with 'headers' and 'rows' keys, or None if invalid table.
    """
    if len(lines) < 2:
        # Need at least header + separator
        return None

    # Parse header row
    header_line = lines[0]
    headers = _parse_table_row(header_line)
    if not headers:
        return None

    # Check for separator row
    if len(lines) < 2:
        return None
    
    separator_line = lines[1]
    if not _is_separator_row(separator_line):
        return None

    # Parse data rows
    rows = []
    for line in lines[2:]:
        row = _parse_table_row(line)
        if row:
            # Ensure row has same number of columns as headers
            # Pad with empty strings if needed, truncate if too long
            while len(row) < len(headers):
                row.append("")
            if len(row) > len(headers):
                row = row[:len(headers)]
            rows.append(row)

    return {"headers": headers, "rows": rows}


def _parse_table_row(line: str) -> List[str] | None:
    """Parse a single table row into a list of cell strings.

    Args:
        line: Raw markdown table row with pipes.

    Returns:
        List of cell strings (stripped), or None if invalid.
    """
    if not line or "|" not in line:
        return None

    # Remove leading/trailing whitespace
    line = line.strip()
    
    # Remove leading and trailing pipes
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]

    # Split on pipes and strip whitespace from each cell
    cells = [cell.strip() for cell in line.split("|")]
    
    return cells if cells else None


def _is_separator_row(line: str) -> bool:
    """Check if a line is a GFM table separator row.

    Args:
        line: Raw markdown line.

    Returns:
        True if the line is a valid separator (e.g., |---|---|).
    """
    if not line or "|" not in line:
        return False

    # Remove whitespace and pipes
    cleaned = line.strip()
    if cleaned.startswith("|"):
        cleaned = cleaned[1:]
    if cleaned.endswith("|"):
        cleaned = cleaned[:-1]

    # Split on pipes and check each cell is a separator
    cells = [cell.strip() for cell in cleaned.split("|")]
    
    for cell in cells:
        # Valid separator: optional colons, at least one dash
        # Examples: ---, :---, ---:, :---:
        if not cell:
            return False
        # Remove colons
        stripped = cell.replace(":", "")
        # Must have at least one dash remaining
        if not stripped or not all(c == "-" for c in stripped):
            return False

    return True


def extract_structure_from_documents(documents: Iterable[dict]) -> List[dict]:
    """Enhance document dictionaries with extracted markdown structure.

    Args:
        documents: Iterable of document dicts with at least a `text` key.

    Returns:
        List of enhanced document structures. Each element contains the original
        document keys plus ``headings``, ``sections``, ``references``, ``tables``,
        ``lists``, ``paragraphs``, and ``frontmatter``.
    """
    results: List[dict] = []

    for doc in documents or []:
        text = doc.get("text", "") if isinstance(doc, dict) else ""

        headings = _extract_headings(text)

        # Build sections by splitting on headings; include leading content as a
        # preface section when no initial heading exists.
        sections: List[dict] = []
        if headings:
            # iterate through headings and capture content between them
            hdr_positions = []
            for m in HEADING_RE.finditer(text):
                hdr_positions.append((m.start(), len(m.group(1)), m.group(2).strip()))

            # append trailing content after each heading
            for idx, (pos, level, title) in enumerate(hdr_positions):
                start = pos
                end = hdr_positions[idx + 1][0] if idx + 1 < len(hdr_positions) else len(text)
                content = text[start:end].strip()
                sections.append({"heading": title, "level": level, "content": content})
        else:
            if text.strip():
                sections.append({"heading": None, "level": 0, "content": text.strip()})

        links = _extract_links(text)
        tables = _extract_tables(text)
        lists = _extract_lists(text)
        paragraphs = _extract_paragraphs(text)
        frontmatter = _extract_frontmatter(text)

        out = dict(doc)
        out.update({
            "headings": headings,
            "sections": sections,
            "references": links,
            "tables": tables,
            "lists": lists,
            "paragraphs": paragraphs,
            "frontmatter": frontmatter,
        })

        results.append(out)

    return results

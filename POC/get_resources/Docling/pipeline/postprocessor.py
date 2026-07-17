"""Stage 2: Clean and normalize the raw Docling Markdown output."""
from __future__ import annotations

import pathlib
import re
from collections import Counter


# ---------------------------------------------------------------------------
# Internal helpers (mirrored from postprocess.py)
# ---------------------------------------------------------------------------


def _reconstruct_toc(text: str) -> str:
    table_pattern = re.compile(
        r"(\|[^\n]+\|\n)(\|[-| :]+\|\n)((?:\|[^\n]+\|\n)+)",
        re.MULTILINE,
    )

    def _is_toc_table(data_rows: str) -> bool:
        rows = [r for r in data_rows.strip().splitlines() if r.strip()]
        toc_like = sum(1 for r in rows if re.search(r"\.{4,}\s*\d+", r))
        return toc_like >= 3 and toc_like >= len(rows) * 0.4

    def _table_to_list(match: re.Match) -> str:
        data_rows = match.group(3)
        if not _is_toc_table(data_rows):
            return match.group(0)
        entries = []
        for row in data_rows.strip().splitlines():
            cells = [c.strip() for c in row.strip("|").split("|")]
            cells = [c for c in cells if c]
            if not cells:
                continue
            section = ""
            if cells and re.match(r"^\d[\d.]*$", cells[0]):
                section = cells.pop(0)
            seen: set[str] = set()
            content_cell = ""
            for cell in cells:
                key = re.sub(r"\.{3,}", "", cell).strip()
                if key in seen:
                    continue
                seen.add(key)
                if re.search(r"\.{3,}\s*\d+\s*$", cell):
                    content_cell = cell
                    break
            if not content_cell and cells:
                content_cell = cells[0]
            m = re.match(r"^(.*?)\s*\.{3,}\s*(\d+)\s*$", content_cell)
            if m:
                title, page = m.group(1).strip(), m.group(2)
            else:
                title, page = content_cell.strip(), ""
            if not title:
                continue
            depth = max(0, len(section.split(".")) - 1) if section else 0
            indent = "  " * depth
            prefix = f"**{section}**  " if section else ""
            page_ref = f" -- p.{page}" if page else ""
            entries.append(f"{indent}- {prefix}{title}{page_ref}")
        return "\n".join(entries) + "\n"

    return table_pattern.sub(_table_to_list, text)


def _fix_heading_levels(text: str) -> str:
    numbered_heading = re.compile(r"^#{1,6} ((\d+)(\.(\d+))*) (.+)$", re.MULTILINE)

    def _relevel(match: re.Match) -> str:
        section_num = match.group(1)
        title = match.group(5)
        level = min(len(section_num.split(".")), 4)
        return f"{'#' * level} {section_num} {title}"

    return numbered_heading.sub(_relevel, text)


def _replace_image_placeholders(text: str) -> str:
    counter = [0]

    def _replace(_match: re.Match) -> str:
        counter[0] += 1
        return f"*[Figure {counter[0]}: diagram or image -- not extracted]*"

    return re.sub(r"<!--\s*image\s*-->", _replace, text)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def postprocess_pdf(markdown_text: str, slug: str, output_dir: pathlib.Path) -> None:
    """Apply all post-processing steps to markdown and write ``<slug>_clean.md``.

    Steps applied (in order):
    1. Reconstruct PDF table-of-contents tables as indented Markdown lists.
    2. Re-level numbered headings to match their logical document depth.
    3. Replace ``<!-- image -->`` comments with readable figure markers.
    4. Remove repeated headers/footers (lines appearing 3+ times).
    5. Strip standalone page-number lines.
    6. Merge soft-wrapped paragraph lines.
    7. Normalize whitespace.

    Args:
        markdown_text: Raw markdown content from Docling.
        slug:          Filesystem-safe document identifier.
        output_dir:    Output directory for the cleaned markdown file.
    """
    dst = output_dir / f"{slug}_clean.md"

    text = markdown_text
    text = _reconstruct_toc(text)
    text = _fix_heading_levels(text)
    text = _replace_image_placeholders(text)

    lines = text.splitlines()
    freq = Counter(line.strip() for line in lines if line.strip())
    noise = {ln for ln, count in freq.items() if count >= 3 and len(ln) < 120}
    lines = [ln for ln in lines if ln.strip() not in noise]
    text = "\n".join(lines)

    text = re.sub(r"^\s*Page\s+\d+\s+of\s+\d+\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*-\s*\d+\s*-\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*\d+\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"(?<![.!?:\-])\n(?=[a-z])", " ", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.strip()

    dst.write_text(text, encoding="utf-8")

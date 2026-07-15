"""
Step 2: Clean and normalize the raw Docling Markdown output.

Applies:
- TOC table reconstruction (multi-column PDF TOC → clean indented list)
- Heading level correction (re-levels numbered headings by section depth)
- Image placeholder replacement (<!-- image --> → readable figure marker)
- Repeated header/footer removal (frequency-based)
- Page number line removal
- Broken paragraph merging
- Whitespace normalization

Usage:
    source .venv/bin/activate
    python postprocess.py <path/to/document.pdf>
"""

import argparse
import re
import pathlib
from collections import Counter

parser = argparse.ArgumentParser(description="Clean and normalise raw Docling Markdown output.")
parser.add_argument("pdf", help="Path to the original PDF file (used to resolve output paths).")
args = parser.parse_args()

SLUG = re.sub(r"[^a-z0-9]+", "_", pathlib.Path(args.pdf).stem.lower()).strip("_")
_HERE = pathlib.Path(__file__).parent.resolve()
OUT_DIR = (_HERE / "../../DataSource/pdf_spec") / SLUG

SRC = OUT_DIR / f"{SLUG}.md"
DST = OUT_DIR / f"{SLUG}_clean.md"

if not SRC.exists():
    raise FileNotFoundError(f"Source not found: {SRC}. Run convert.py first.")


def reconstruct_toc(text: str) -> str:
    """
    Detect GFM table blocks that represent a PDF table-of-contents and
    replace them with a clean indented Markdown list.

    Heuristic: a table where ≥40% of rows contain dot-leader + page-number
    patterns (e.g. "Title text .........30") is treated as a TOC table.
    """
    table_pattern = re.compile(
        r"(\|[^\n]+\|\n)"        # header row
        r"(\|[-| :]+\|\n)"       # separator row
        r"((?:\|[^\n]+\|\n)+)",  # one or more data rows
        re.MULTILINE,
    )

    def _is_toc_table(data_rows: str) -> bool:
        rows = [r for r in data_rows.strip().splitlines() if r.strip()]
        toc_like = sum(1 for r in rows if re.search(r"\.{4,}\s*\d+", r))
        return toc_like >= 3 and toc_like >= len(rows) * 0.4

    def _table_to_list(match: re.Match) -> str:
        data_rows = match.group(3)
        if not _is_toc_table(data_rows):
            return match.group(0)  # leave non-TOC tables unchanged

        entries = []
        for row in data_rows.strip().splitlines():
            cells = [c.strip() for c in row.strip("|").split("|")]
            cells = [c for c in cells if c]
            if not cells:
                continue

            # First short numeric cell = section number
            section = ""
            if cells and re.match(r"^\d[\d.]*$", cells[0]):
                section = cells.pop(0)

            # Pick the first unique cell that contains dot-leaders + page number;
            # skip duplicate columns produced by the PDF's multi-column layout.
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

            # Split "Title text .....30" into title and page number.
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
            page_ref = f" — p.{page}" if page else ""
            entries.append(f"{indent}- {prefix}{title}{page_ref}")

        return "\n".join(entries) + "\n"

    return table_pattern.sub(_table_to_list, text)


def fix_heading_levels(text: str) -> str:
    """
    Re-level headings that carry a section number so the Markdown hierarchy
    matches the document's logical structure.

    Docling collapses all headings to ## regardless of depth. This function
    reassigns heading level based on the dot-depth of the section number:
      "1 Title"       → # (H1)
      "1.1 Title"     → ## (H2)
      "1.1.1 Title"   → ### (H3)
      "1.1.1.1 Title" → #### (H4)
    Non-numbered headings are left unchanged.
    """
    numbered_heading = re.compile(
        r"^#{1,6} ((\d+)(\.(\d+))*) (.+)$", re.MULTILINE
    )

    def _relevel(match: re.Match) -> str:
        section_num = match.group(1)   # e.g. "3.4.1"
        title = match.group(5)         # e.g. "Payment Initiation Request"
        depth = len(section_num.split("."))  # 1→H1, 2→H2, 3→H3, 4→H4
        level = min(depth, 4)
        return f"{'#' * level} {section_num} {title}"

    return numbered_heading.sub(_relevel, text)


def replace_image_placeholders(text: str) -> str:
    """
    Replace Docling's <!-- image --> HTML comments with a visible Markdown
    figure marker. Since captions are not available in this document, a
    generic placeholder is used so LLMs are aware content was omitted.
    """
    image_counter = [0]

    def _replace(match: re.Match) -> str:
        image_counter[0] += 1
        return f"*[Figure {image_counter[0]}: diagram or image — not extracted]*"

    return re.sub(r"<!--\s*image\s*-->", _replace, text)


text = SRC.read_text(encoding="utf-8")

# --- 1. Reconstruct TOC tables ---
text = reconstruct_toc(text)

# --- 2. Fix heading levels ---
text = fix_heading_levels(text)

# --- 3. Replace image placeholders ---
text = replace_image_placeholders(text)

# --- 4. Remove repeated headers/footers ---
# Lines that appear 3+ times are likely page headers or footers.
lines = text.splitlines()
freq = Counter(line.strip() for line in lines if line.strip())
noise = {
    line
    for line, count in freq.items()
    if count >= 3 and len(line) < 120
}
lines = [line for line in lines if line.strip() not in noise]
text = "\n".join(lines)

# --- 5. Remove page number lines ---
# Matches "Page 12 of 94", "- 12 -", or bare integers on their own line.
text = re.sub(r"^\s*Page\s+\d+\s+of\s+\d+\s*$", "", text, flags=re.MULTILINE)
text = re.sub(r"^\s*-\s*\d+\s*-\s*$", "", text, flags=re.MULTILINE)
text = re.sub(r"^\s*\d+\s*$", "", text, flags=re.MULTILINE)

# --- 6. Merge broken paragraphs ---
# A line break between a non-sentence-ending word and a lowercase continuation
# is treated as a soft wrap rather than a paragraph break.
text = re.sub(r"(?<![.!?:\-])\n(?=[a-z])", " ", text)

# --- 7. Normalize whitespace ---
text = re.sub(r"[ \t]+", " ", text)          # collapse horizontal whitespace
text = re.sub(r"\n{3,}", "\n\n", text)        # collapse excess blank lines
text = text.strip()

DST.write_text(text, encoding="utf-8")
print(f"Cleaned document written to: {DST}")
print(f"Lines before: {len(SRC.read_text(encoding='utf-8').splitlines()):,}")
print(f"Lines after : {len(text.splitlines()):,}")

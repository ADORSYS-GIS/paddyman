"""Lightweight helpers for extracting heading positions, tables and lists
with source locations. Kept minimal to be imported by the parser.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List


def _slugify(s: str) -> str:
    s2 = re.sub(r"[^\w\s-]", "", s).strip().lower()
    s2 = re.sub(r"\s+", "-", s2)
    s2 = re.sub(r"-+", "-", s2)
    return s2


HEADING_RE = re.compile(r"^(#{1,6})\s*(.+)", flags=re.MULTILINE)


def _extract_headings_with_positions(text: str) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for m in HEADING_RE.finditer(text):
        level = len(m.group(1))
        title = m.group(2).strip()
        pos = m.start()
        line = text[:pos].count("\n") + 1
        out.append({"level": level, "text": title, "line": line, "id": _slugify(title), "pos": pos})
    return out


def _parse_table_block(lines: List[str]) -> Dict | None:
    def _parse_row(line: str) -> List[str] | None:
        line = line.strip()
        if line.startswith("|"):
            line = line[1:]
        if line.endswith("|"):
            line = line[:-1]
        cells = [c.strip() for c in line.split("|")]
        return cells if cells else None

    if len(lines) < 2:
        return None
    headers = _parse_row(lines[0])
    if not headers:
        return None
    if "-" not in lines[1]:
        return None
    rows = []
    for line in lines[2:]:
        r = _parse_row(line)
        if r:
            while len(r) < len(headers):
                r.append("")
            if len(r) > len(headers):
                r = r[: len(headers)]
            rows.append(r)
    return {"headers": headers, "rows": rows}


def _extract_table_blocks(text: str) -> List[Dict[str, Any]]:
    lines = text.splitlines()
    tables: List[Dict[str, Any]] = []
    buf: List[str] = []
    start_idx = None
    for idx, line in enumerate(lines, start=1):
        if "|" in line:
            if start_idx is None:
                start_idx = idx
            buf.append(line)
        else:
            if buf:
                tbl = _parse_table_block(buf)
                if tbl:
                    tbl["start_line"] = start_idx
                    tbl["end_line"] = idx - 1
                    tables.append(tbl)
                buf = []
                start_idx = None
    if buf:
        tbl = _parse_table_block(buf)
        if tbl:
            tbl["start_line"] = start_idx or 1
            tbl["end_line"] = len(lines)
            tables.append(tbl)
    return tables


def _extract_list_blocks(text: str) -> List[Dict[str, Any]]:
    lines = text.splitlines()
    bullet_re = re.compile(r"^(\s*)[-*+]\s+(.*)")
    ordered_re = re.compile(r"^(\s*)\d+[.)]\s+(.*)")
    results: List[Dict[str, Any]] = []
    buf: List[str] = []
    start_idx = None
    current_ordered: bool | None = None

    def _flush(end_idx: int):
        nonlocal buf, start_idx, current_ordered
        if buf and start_idx is not None:
            results.append({"ordered": bool(current_ordered), "items": list(buf), "start_line": start_idx, "end_line": end_idx})
        buf = []
        start_idx = None
        current_ordered = None

    for idx, line in enumerate(lines, start=1):
        bm = bullet_re.match(line)
        om = ordered_re.match(line)
        if bm:
            if current_ordered is True:
                _flush(idx - 1)
            if start_idx is None:
                start_idx = idx
            current_ordered = False
            buf.append(bm.group(2).strip())
        elif om:
            if current_ordered is False:
                _flush(idx - 1)
            if start_idx is None:
                start_idx = idx
            current_ordered = True
            buf.append(om.group(2).strip())
        else:
            if buf:
                _flush(idx - 1)

    if buf:
        _flush(len(lines))
    return results

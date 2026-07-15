"""Playwright-based scraper for Berlin Group Tabulator download tables.

The download pages use Tabulator.js (div.tabulator-tableHolder / div.tabulator-row).
Each row carries:
  - document title in a source-specific cell identified by ``title_field``
  - download href in [tabulator-field="Link"] a[href]

OpenFinance  : title_field="Document title and Version", V-prefixed version token
NextGenPSD2  : title_field="Document title", trailing version number
"""
from __future__ import annotations

import asyncio
import logging
import re
from pathlib import Path
from urllib.parse import urlparse

from playwright.async_api import Frame, async_playwright

from .config import SCRAPER_POST_LOAD_WAIT_MS, SCRAPER_TIMEOUT_MS, USER_AGENT
from .models import DownloadLink

logger = logging.getLogger(__name__)

# Version patterns
# OpenFinance: "Data Dictionary V2.2.6 20250731.pdf" -> "2.2.6"
_VERSION_RE = re.compile(r"V(\d+\.\d+(?:\.\d+)*)", re.IGNORECASE)
# NextGenPSD2: "NextGenPSD2 Implementation Guidelines 1.3.16" -> "1.3.16"
_TRAILING_VERSION_RE = re.compile(r"(\d+\.\d+(?:\.\d+)*)\s*$")

_DEFAULT_VERSION = "unknown"
_TABLE_SELECTOR = "div.tabulator-tableHolder"
_FRAME_PROBE_MS = 8_000   # per-frame timeout when scanning for the table
_POST_RENDER_MS = 3_000   # extra wait after table appears (Tabulator row rendering)


def _build_row_js(title_field: str) -> str:
    """Return JS that collects {title, href} from every div.tabulator-row.

    The title cell is identified by the ``tabulator-field`` attribute value
    supplied as *title_field*.  The Link cell selector is always the same.
    """
    escaped = title_field.replace('"', '\\"')
    return (
        "() => { const r = [];"
        " document.querySelectorAll('div.tabulator-row').forEach(row => {"
        f" const t = row.querySelector('[tabulator-field=\"{escaped}\"]');"
        " const a = row.querySelector('[tabulator-field=\"Link\"] a[href]');"
        " if (t && a) r.push({title: t.innerText.trim(), href: a.href});"
        " }); return r; }"
    )


def _extract_version(title: str, trailing: bool = False) -> str:
    """Extract a version string from a document title.

    *trailing=False* (OpenFinance): matches the first ``V<version>`` token.
    *trailing=True* (NextGenPSD2): matches the numeric version at the end.
    """
    pattern = _TRAILING_VERSION_RE if trailing else _VERSION_RE
    m = pattern.search(title)
    return m.group(1) if m else _DEFAULT_VERSION


def _major_version(version: str) -> int | None:
    """Return the major version integer from a version string, or None."""
    try:
        return int(version.split(".")[0])
    except (ValueError, IndexError):
        return None


def _row_to_link(
    row: dict,
    source_name: str,
    use_title_as_filename: bool = False,
    trailing_version: bool = False,
    version_major: int | None = None,
) -> DownloadLink | None:
    """Convert a Tabulator row dict to a DownloadLink; return None if data is missing."""
    href = row.get("href", "").strip()
    title = row.get("title", "").strip()
    if not href or not title:
        return None
    if use_title_as_filename:
        filename = title if title.lower().endswith(".pdf") else f"{title}.pdf"
    else:
        filename = Path(urlparse(href).path).name or title
    version = _extract_version(title, trailing=trailing_version)
    if version_major is not None and _major_version(version) != version_major:
        logger.debug("Skipping row (version %s not major %s): %s", version, version_major, title)
        return None
    return DownloadLink(
        url=href,
        filename=filename,
        version=version,
        source_name=source_name,
    )


async def _rows_from_frame(frame: Frame, title_field: str) -> list[dict]:
    """Return Tabulator row data from *frame* if it hosts the download table."""
    try:
        # Use wait_for_selector so that frames still loading get a fair chance.
        # Frames without the table raise TimeoutError which is caught below.
        await frame.wait_for_selector(_TABLE_SELECTOR, timeout=_FRAME_PROBE_MS)
        await frame.wait_for_timeout(_POST_RENDER_MS)
        row_js = _build_row_js(title_field)
        rows: list[dict] = await frame.evaluate(row_js)
        logger.info("Tabulator table found in %s — %d row(s)", frame.url, len(rows))
        return rows
    except Exception as exc:
        logger.debug("Frame %s skipped: %s", frame.url, exc)
        return []


async def _scrape_async(
    url: str,
    source_name: str,
    title_field: str = "Document title and Version",
    use_title_as_filename: bool = False,
    trailing_version: bool = False,
    version_major: int | None = None,
) -> list[DownloadLink]:
    """Load *url* with playwright and extract all download rows."""
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(user_agent=USER_AGENT)
        page = await context.new_page()
        try:
            logger.info("Loading %s", url)
            try:
                await page.goto(url, timeout=SCRAPER_TIMEOUT_MS, wait_until="domcontentloaded")
            except Exception:
                logger.warning("Page load timed out for %s — continuing", url)

            # Scroll to trigger full Tabulator row render, then wait for dynamic
            # content (Wix iframes / widgets) to finish loading before scanning frames.
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(SCRAPER_POST_LOAD_WAIT_MS)

            # Probe all frames concurrently so that per-frame probe timeouts run in
            # parallel rather than accumulating (important on Wix pages with many iframes).
            frame_results = await asyncio.gather(
                *[_rows_from_frame(frame, title_field) for frame in page.frames]
            )
            all_rows: list[dict] = [row for rows in frame_results for row in rows]

            links = [
                _row_to_link(r, source_name, use_title_as_filename, trailing_version, version_major)
                for r in all_rows
            ]
            links = [lnk for lnk in links if lnk is not None]
            logger.info("Discovered %d link(s) for %s", len(links), source_name)
            return links
        finally:
            await browser.close()


def scrape_source(
    url: str,
    source_name: str,
    title_field: str = "Document title and Version",
    use_title_as_filename: bool = False,
    trailing_version: bool = False,
    version_major: int | None = None,
) -> list[DownloadLink]:
    """Synchronously scrape a Berlin Group downloads page."""
    return asyncio.run(
        _scrape_async(url, source_name, title_field, use_title_as_filename, trailing_version, version_major)
    )

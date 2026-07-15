"""
Step 1: Convert PDF to raw Markdown using Docling.

Picture description modes (set PICTURE_DESCRIPTION_MODE below):
  "none"  — images become <!-- image --> placeholders (fast, no extra cost)
  "local" — free SmolVLM model runs on CPU; first run downloads ~500 MB
  "api"   — OpenAI GPT-4o-mini; costs ~$0.001–$0.01 per image; requires OPENAI_API_KEY

Usage:
    source .venv/bin/activate
    python convert.py <path/to/document.pdf>
"""

import pathlib

from dotenv import load_dotenv

# Load shared configuration from the Get Resources root directory.
# Both DownloadTrigger and Docling share a single .env at POC/1_Get_Resources/.env.
_ENV_FILE = pathlib.Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=_ENV_FILE)

import argparse
import json
import os
import re

from docling.datamodel.pipeline_options import (
    PdfPipelineOptions,
    PictureDescriptionApiOptions,
    PictureDescriptionVlmOptions,
)
from docling.datamodel.base_models import InputFormat
from docling.document_converter import DocumentConverter, PdfFormatOption

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
parser = argparse.ArgumentParser(description="Convert a PDF to LLM-optimised Markdown.")
parser.add_argument("pdf", help="Path to the input PDF file.")
args = parser.parse_args()

PDF_PATH = pathlib.Path(args.pdf)
if not PDF_PATH.exists():
    raise FileNotFoundError(f"PDF not found: {PDF_PATH}")

# Derive a filesystem-safe slug from the PDF filename (no extension).
# e.g. "XS2A-API-as-PSD2-...-2.4.pdf" → "xs2a_api_as_psd2_..._2_4"
SLUG = re.sub(r"[^a-z0-9]+", "_", PDF_PATH.stem.lower()).strip("_")

_HERE = pathlib.Path(__file__).parent.resolve()
OUT_DIR = (_HERE / "../../DataSource/pdf_spec") / SLUG
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
# Choose picture description mode: "none" | "local" | "api"
# "local" is impractical on CPU for documents with many figures (can take hours).
# Use "none" for fast output, or "api" if you have an OpenAI key.
PICTURE_DESCRIPTION_MODE = "none"

PICTURE_DESCRIPTION_PROMPT = (
    "Describe this figure or diagram in one or two concise sentences, "
    "focusing on its content and purpose."
)
# ---------------------------------------------------------------------------

options = PdfPipelineOptions()
options.do_ocr = True               # Tesseract OCR (sudo apt install tesseract-ocr)
options.do_table_structure = True   # export tables as GFM Markdown
options.table_structure_options.do_cell_matching = True  # preserve merged cells

if PICTURE_DESCRIPTION_MODE == "local":
    # Free. Runs on CPU. Downloads ~500 MB model on first run from HuggingFace.
    # Extra RAM: ~2 GB. Adds ~10–30 s per figure on CPU.
    options.generate_picture_images = True
    options.do_picture_description = True
    options.picture_description_options = PictureDescriptionVlmOptions(
        repo_id="HuggingFaceTB/SmolVLM-256M-Instruct",
        prompt=PICTURE_DESCRIPTION_PROMPT,
    )
elif PICTURE_DESCRIPTION_MODE == "api":
    # Costs money. Requires OPENAI_API_KEY in .env file.
    # Cost estimate: ~$0.001–$0.01 per figure depending on image size.
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "OPENAI_API_KEY not set. Add it to .env or switch to "
            "PICTURE_DESCRIPTION_MODE='local'."
        )
    options.generate_picture_images = True
    options.do_picture_description = True
    options.picture_description_options = PictureDescriptionApiOptions(
        url="https://api.openai.com/v1/chat/completions",
        params=dict(model="gpt-4o-mini", max_tokens=200),
        prompt=PICTURE_DESCRIPTION_PROMPT,
        headers={"Authorization": f"Bearer {api_key}"},
    )
# "none": picture description disabled; images become <!-- image --> placeholders

# Wire options into the converter — without this, all options above are ignored.
converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(pipeline_options=options)
    }
)
result = converter.convert(str(PDF_PATH))
doc = result.document

# Export full raw Markdown — named after the source PDF.
raw_md_path = OUT_DIR / f"{SLUG}.md"
md = doc.export_to_markdown()
raw_md_path.write_text(md, encoding="utf-8")

# Export document-level metadata — named after the source PDF.
meta_path = OUT_DIR / f"{SLUG}_metadata.json"
meta = {
    "source_pdf": str(PDF_PATH),
    "slug": SLUG,
    "title": doc.name,
    "num_pages": len(doc.pages),
    "num_tables": len(doc.tables),
    "num_figures": len(doc.pictures),
    "picture_description_mode": PICTURE_DESCRIPTION_MODE,
}
meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")

print(f"Pages : {meta['num_pages']}")
print(f"Tables: {meta['num_tables']}")
print(f"Figs  : {meta['num_figures']}")
print(f"Picture description: {PICTURE_DESCRIPTION_MODE}")
print(f"Raw MD  : {raw_md_path}")
print(f"Metadata: {meta_path}")


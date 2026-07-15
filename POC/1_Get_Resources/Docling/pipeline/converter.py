"""Stage 1: Convert a PDF to raw Markdown and a metadata JSON using Docling."""
from __future__ import annotations

import json
import os
import pathlib

from .metadata_writer import extract_heading_pages, extract_version


def build_converter(picture_mode: str):
    """Create and return a configured DocumentConverter.

    Imported lazily so callers that never reach this function do not require
    docling to be installed just to parse CLI arguments.

    Args:
        picture_mode: One of ``"none"``, ``"local"``, or ``"api"``.
    """
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import (
        PdfPipelineOptions,
        PictureDescriptionApiOptions,
        PictureDescriptionVlmOptions,
    )
    from docling.document_converter import DocumentConverter, PdfFormatOption

    _PICTURE_PROMPT = (
        "Describe this figure or diagram in one or two concise sentences, "
        "focusing on its content and purpose."
    )

    options = PdfPipelineOptions()
    options.do_ocr = True
    options.do_table_structure = True
    options.table_structure_options.do_cell_matching = True

    if picture_mode == "local":
        options.generate_picture_images = True
        options.do_picture_description = True
        options.picture_description_options = PictureDescriptionVlmOptions(
            repo_id="HuggingFaceTB/SmolVLM-256M-Instruct",
            prompt=_PICTURE_PROMPT,
        )
    elif picture_mode == "api":
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "OPENAI_API_KEY not set. Add it to .env or use --picture-mode=local."
            )
        options.generate_picture_images = True
        options.do_picture_description = True
        options.picture_description_options = PictureDescriptionApiOptions(
            url="https://api.openai.com/v1/chat/completions",
            params=dict(model="gpt-4o-mini", max_tokens=200),
            prompt=_PICTURE_PROMPT,
            headers={"Authorization": f"Bearer {api_key}"},
        )

    return DocumentConverter(
        format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=options)}
    )


def convert_pdf(
    converter,
    pdf_path: pathlib.Path,
    slug: str,
    output_dir: pathlib.Path,
    picture_mode: str,
) -> str:
    """Run Docling on *pdf_path* and return the raw markdown content.

    Args:
        converter:    A DocumentConverter returned by :func:`build_converter`.
        pdf_path:     Absolute path to the source PDF.
        slug:         Filesystem-safe identifier for this document.
        output_dir:   Output directory (used for validation, not for writing).
        picture_mode: Picture description mode (currently unused, kept for API compatibility).

    Returns:
        Raw markdown content from Docling conversion.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    result = converter.convert(str(pdf_path))
    doc = result.document

    return doc.export_to_markdown()

"""Markdown parser package for Docling document ingestion.

Expose a single entry point `load_documents` which reads documents from the
configured input directory (or a supplied path) and returns a list of
LlamaIndex `Document` objects for downstream processing.
"""
from .reader import load_documents  # noqa: F401

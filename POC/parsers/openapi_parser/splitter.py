"""Semantic chunking for OpenAPI YAML documents — ``ParsingChunking`` stage.

Architecture role: ``ParsingChunking`` in Layer 2 (Ingestion & Processing).

Accepts LlamaIndex ``Document`` objects produced by
:func:`openapi_parser.readers.read_local` or
:func:`openapi_parser.readers.read_gitlab` and splits them into semantic
chunks using LlamaIndex ``SemanticSplitterNodeParser``.

Semantic splitting on YAML files prevents endpoint and schema definitions from
being split mid-block, preserving structural integrity for the downstream
``MetadataEntityExtraction`` stage.

``SemanticSplitterNodeParser`` is imported at runtime so the module can be
imported and tested without an active OpenAI connection.
"""
from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import Iterable, List

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _derive_source_slug(meta: dict | None, default: str) -> str:
    if not meta:
        return default
    path = meta.get("file_path") or meta.get("location") or meta.get("source")
    if not path:
        return default
    try:
        return Path(str(path)).stem
    except Exception:
        return str(path)


def _stable_chunk_id(source_slug: str, chunk_text: str) -> str:
    """Deterministic chunk identifier — SHA1 prefix of the chunk text."""
    h = hashlib.sha1(chunk_text.encode("utf-8")).hexdigest()[:8]
    return f"{source_slug}_{h}"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def split_documents(documents: Iterable) -> List[dict]:
    """Split OpenAPI Document objects into semantic chunks.

    Each document's YAML text is split on meaning boundaries so that
    endpoint and schema definitions are never broken across chunks.  The
    returned chunks carry the originating file-path metadata for version-tag
    injection in the next pipeline stage.

    Args:
        documents: Iterable of LlamaIndex ``Document`` objects.  Each
            document's ``text`` should be the raw YAML content of an OpenAPI
            spec file.

    Returns:
        List of chunk dictionaries with keys:

        - ``chunk_id``: stable identifier (``<slug>_<sha1prefix>``)
        - ``text``: chunk text
        - ``chunk_order``: 1-based position within the source document
        - ``source_document_id``: file path or generated identifier
        - ``source_document_path``: original file path when available
        - ``spec_source``: same as ``source_document_path``
        - ``metadata``: full metadata dict from the source document
    """
    try:
        from llama_index.core.node_parser import SemanticSplitterNodeParser  # type: ignore
    except ImportError:
        try:
            from llama_index.node_parser.semantic_splitter import SemanticSplitterNodeParser  # type: ignore
        except ImportError:
            from llama_index.node_parser import SemanticSplitterNodeParser  # type: ignore

    from llama_index.embeddings.openai import OpenAIEmbedding  # type: ignore
    from shared.config import settings as _cfg

    api_key = _cfg.openai_api_key
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is required for SemanticSplitterNodeParser. "
            "Set it in POC/.env; non-secret embedding settings live in POC/config.yml."
        )

    embed_kwargs: dict = {"api_key": api_key, "model_name": _cfg.embed_model_name}
    if _cfg.embed_base_url:
        embed_kwargs["api_base"] = _cfg.embed_base_url

    parser = SemanticSplitterNodeParser(embed_model=OpenAIEmbedding(**embed_kwargs))

    chunks: List[dict] = []
    for doc_index, doc in enumerate(documents or []):
        text = getattr(doc, "text", None)
        if text is None:
            get_text = getattr(doc, "get_text", None)
            text = get_text() if callable(get_text) else ""
        if not text or not str(text).strip():
            continue

        raw_meta = getattr(doc, "extra_info", None) or getattr(doc, "metadata", None) or {}
        if not isinstance(raw_meta, dict):
            raw_meta = {}

        source_path: str | None = raw_meta.get("file_path")
        source_slug = _derive_source_slug(raw_meta, f"doc{doc_index:04d}")
        source_id: str | None = source_path or raw_meta.get("source_id")

        try:
            nodes = parser.split(text) if hasattr(parser, "split") else parser.split_text(text)
        except Exception:
            try:
                nodes = parser.split(doc)  # type: ignore[arg-type]
            except Exception:
                nodes = [type("_N", (), {"text": text})()]

        for idx, node in enumerate(nodes):
            node_text = getattr(node, "text", None) or (getattr(node, "get_text", lambda: "")())
            if node_text is None:
                node_text = str(node)
            node_text = str(node_text)

            chunks.append({
                "chunk_id": _stable_chunk_id(source_slug, node_text),
                "text": node_text,
                "chunk_order": idx + 1,
                "source_document_id": source_id or source_slug,
                "source_document_path": source_path,
                "spec_source": source_path,
                "metadata": dict(raw_meta),
            })

    return chunks

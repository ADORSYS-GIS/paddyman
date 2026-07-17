"""spaCy-based entity extraction pipeline — Phase 4, Chunk 4.1.

Entry point:

    from spacy.pipeline import SpacyExtractionPipeline
    from shared.models import SourceMetadata, SourceType

    pipeline = SpacyExtractionPipeline.build()
    result = pipeline.run("Payment consent was approved.", source_metadata)
"""

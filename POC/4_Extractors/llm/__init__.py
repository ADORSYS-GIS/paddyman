"""LLM entity extraction package.

All LLM configuration is read through ``shared.config.settings``.

Usage::

    from services.extraction_service import ExtractionService
    from client.factory import create_client

    service = ExtractionService(client=create_client())
    result  = service.extract(text, source_metadata)
"""

"""Embedding generation package.

All embedding configuration is read through ``shared.config.settings``.

Usage::

    from services.embedding_service import EmbeddingService
    from client.factory import create_client

    service = EmbeddingService(client=create_client())
    result  = service.embed_entity(entity, source_metadata)
"""

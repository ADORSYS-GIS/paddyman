"""Generates and logs a summary of the parsing operation."""
from __future__ import annotations

import logging
from typing import Any

log = logging.getLogger(__name__)


def log_summary(results: list[dict[str, Any]]):
    """Log a summary of the parsed entities."""
    total_apis = sum(1 for r in results if r.get("api"))
    total_endpoints = sum(len(r.get("endpoints", [])) for r in results)
    total_operations = sum(len(r.get("operations", [])) for r in results)
    total_parameters = sum(len(r.get("parameters", [])) for r in results)
    total_request_bodies = sum(len(r.get("request_bodies", [])) for r in results)
    total_responses = sum(len(r.get("responses", [])) for r in results)
    total_security_schemes = sum(len(r.get("security_schemes", [])) for r in results)
    total_tags = sum(len(r.get("tags", [])) for r in results)

    log.info("--- OpenAPI Parser Summary ---")
    log.info(f"APIs: {total_apis}")
    log.info(f"Endpoints: {total_endpoints}")
    log.info(f"Operations: {total_operations}")
    log.info(f"Parameters: {total_parameters}")
    log.info(f"Request Bodies: {total_request_bodies}")
    log.info(f"Responses: {total_responses}")
    log.info(f"Security Schemes: {total_security_schemes}")
    log.info(f"Tags: {total_tags}")
    log.info("------------------------------")

"""Unit tests for OpenAPI info metadata extraction.

Covers:
- Comprehensive info metadata extraction (title, version, description)
- Contact information extraction
- License information extraction
- Terms of service URL extraction
- External documentation extraction
- Custom extension fields (x-*) extraction
- Description truncation for summary
- Missing optional fields handling
- Required field validation
"""
from __future__ import annotations

import textwrap

import pytest
import yaml


# ---------------------------------------------------------------------------
# Test fixtures
# ---------------------------------------------------------------------------

_MINIMAL_SPEC = textwrap.dedent("""\
    openapi: "3.0.1"
    info:
      title: Payment API
      version: "1.0.0"
""")

_FULL_INFO_SPEC = textwrap.dedent("""\
    openapi: "3.0.1"
    info:
      title: NextGenPSD2 XS2A Framework
      version: "1.3.16_2025-11-27"
      description: |
        This API provides a comprehensive framework for payment services.
        It supports multiple account types and payment methods.
      termsOfService: "https://example.com/terms"
      contact:
        name: Berlin Group
        email: support@berlin-group.org
        url: https://www.berlin-group.org
      license:
        name: Apache 2.0
        url: https://www.apache.org/licenses/LICENSE-2.0.html
    externalDocs:
      url: https://docs.example.com
      description: Additional documentation
    servers:
      - url: https://api.example.com/v1
        description: Production
""")

_CUSTOM_EXTENSIONS_SPEC = textwrap.dedent("""\
    openapi: "3.0.1"
    info:
      title: Extended API
      version: "2.0.0"
      x-api-id: "ext-001"
      x-audience: internal
      x-custom-field: custom-value
""")

_LONG_DESCRIPTION_SPEC = textwrap.dedent("""\
    openapi: "3.0.1"
    info:
      title: API with Long Description
      version: "1.0.0"
      description: |
        This is a very long description that exceeds the truncation limit.
        It contains multiple paragraphs and detailed information about
        the API's functionality, usage, authentication, and more details
        that will be truncated in the summary version for display purposes.
""")

_NO_INFO_SPEC = textwrap.dedent("""\
    openapi: "3.0.1"
    paths: {}
""")

_MISSING_TITLE_SPEC = textwrap.dedent("""\
    openapi: "3.0.1"
    info:
      version: "1.0.0"
""")

_MISSING_VERSION_SPEC = textwrap.dedent("""\
    openapi: "3.0.1"
    info:
      title: No Version API
""")

_SWAGGER2_SPEC = textwrap.dedent("""\
    swagger: "2.0"
    info:
      title: Legacy API
      version: "0.9.0"
""")


# ---------------------------------------------------------------------------
# extract_info_metadata tests
# ---------------------------------------------------------------------------

class TestExtractInfoMetadata:
    def test_minimal_required_fields(self):
        """Verify title and version are extracted."""
        from openapi_parser.info_extractor import extract_info_metadata

        raw = yaml.safe_load(_MINIMAL_SPEC)
        result = extract_info_metadata(raw, "/fake/spec.yaml")

        assert result["title"] == "Payment API"
        assert result["version"] == "1.0.0"
        assert result["openapi_version"] == "3.0.1"
        assert result["servers"] == []

    def test_full_info_metadata(self):
        """Verify all info fields are extracted."""
        from openapi_parser.info_extractor import extract_info_metadata

        raw = yaml.safe_load(_FULL_INFO_SPEC)
        result = extract_info_metadata(raw, "/fake/full.yaml")

        assert result["title"] == "NextGenPSD2 XS2A Framework"
        assert result["version"] == "1.3.16_2025-11-27"
        assert "comprehensive framework" in result["description"]
        assert result["terms_of_service"] == "https://example.com/terms"

    def test_contact_information_extracted(self):
        """Verify contact information is extracted."""
        from openapi_parser.info_extractor import extract_info_metadata

        raw = yaml.safe_load(_FULL_INFO_SPEC)
        result = extract_info_metadata(raw, "/fake/full.yaml")

        assert result["contact"]["name"] == "Berlin Group"
        assert result["contact"]["email"] == "support@berlin-group.org"
        assert result["contact"]["url"] == "https://www.berlin-group.org"

    def test_license_information_extracted(self):
        """Verify license information is extracted."""
        from openapi_parser.info_extractor import extract_info_metadata

        raw = yaml.safe_load(_FULL_INFO_SPEC)
        result = extract_info_metadata(raw, "/fake/full.yaml")

        assert result["license"]["name"] == "Apache 2.0"
        assert (
            result["license"]["url"]
            == "https://www.apache.org/licenses/LICENSE-2.0.html"
        )

    def test_external_docs_extracted(self):
        """Verify external docs are extracted."""
        from openapi_parser.info_extractor import extract_info_metadata

        raw = yaml.safe_load(_FULL_INFO_SPEC)
        result = extract_info_metadata(raw, "/fake/full.yaml")

        assert result["external_docs"]["url"] == "https://docs.example.com"
        assert result["external_docs"]["description"] == "Additional documentation"

    def test_custom_extensions_extracted(self):
        """Verify x-* extensions are captured."""
        from openapi_parser.info_extractor import extract_info_metadata

        raw = yaml.safe_load(_CUSTOM_EXTENSIONS_SPEC)
        result = extract_info_metadata(raw, "/fake/ext.yaml")

        assert "extensions" in result
        assert result["extensions"]["x-api-id"] == "ext-001"
        assert result["extensions"]["x-audience"] == "internal"
        assert result["extensions"]["x-custom-field"] == "custom-value"

    def test_description_truncation(self):
        """Verify description is truncated for summary."""
        from openapi_parser.info_extractor import extract_info_metadata

        raw = yaml.safe_load(_LONG_DESCRIPTION_SPEC)
        result = extract_info_metadata(raw, "/fake/long.yaml")

        # Full description should be preserved
        assert len(result["description"]) > 200

        # Summary should be truncated
        assert len(result["description_summary"]) <= 200
        assert result["description_summary"].endswith("...")

    def test_swagger_version_extracted(self):
        """Verify swagger 2.0 version is extracted."""
        from openapi_parser.info_extractor import extract_info_metadata

        raw = yaml.safe_load(_SWAGGER2_SPEC)
        result = extract_info_metadata(raw, "/fake/swagger.yaml")

        assert result["openapi_version"] == "2.0"

    def test_missing_info_raises_error(self):
        """Verify error raised when info block is missing."""
        from openapi_parser.info_extractor import (
            InfoExtractionError,
            extract_info_metadata,
        )

        raw = yaml.safe_load(_NO_INFO_SPEC)

        with pytest.raises(InfoExtractionError, match="info"):
            extract_info_metadata(raw, "/fake/no_info.yaml")

    def test_missing_title_raises_error(self):
        """Verify error raised when title is missing."""
        from openapi_parser.info_extractor import (
            InfoExtractionError,
            extract_info_metadata,
        )

        raw = yaml.safe_load(_MISSING_TITLE_SPEC)

        with pytest.raises(InfoExtractionError, match="title"):
            extract_info_metadata(raw, "/fake/no_title.yaml")

    def test_missing_version_raises_error(self):
        """Verify error raised when version is missing."""
        from openapi_parser.info_extractor import (
            InfoExtractionError,
            extract_info_metadata,
        )

        raw = yaml.safe_load(_MISSING_VERSION_SPEC)

        with pytest.raises(InfoExtractionError, match="version"):
            extract_info_metadata(raw, "/fake/no_version.yaml")

    def test_missing_optional_fields_handled(self):
        """Verify missing optional fields don't cause errors."""
        from openapi_parser.info_extractor import extract_info_metadata

        raw = yaml.safe_load(_MINIMAL_SPEC)
        result = extract_info_metadata(raw, "/fake/spec.yaml")

        # These fields should not be in the result when missing
        assert "description" not in result
        assert "contact" not in result
        assert "license" not in result
        assert "terms_of_service" not in result
        assert "external_docs" not in result
        assert "extensions" not in result

    def test_servers_extracted(self):
        """Verify servers list is extracted."""
        from openapi_parser.info_extractor import extract_info_metadata

        raw = yaml.safe_load(_FULL_INFO_SPEC)
        result = extract_info_metadata(raw, "/fake/full.yaml")

        assert len(result["servers"]) == 1
        assert result["servers"][0]["url"] == "https://api.example.com/v1"
        assert result["servers"][0]["description"] == "Production"


# ---------------------------------------------------------------------------
# _truncate_description tests
# ---------------------------------------------------------------------------

class TestTruncateDescription:
    def test_short_text_not_truncated(self):
        """Verify short text is returned as-is."""
        from openapi_parser.info_extractor import _truncate_description

        text = "Short description"
        result = _truncate_description(text, 200)

        assert result == text
        assert not result.endswith("...")

    def test_long_text_truncated_with_ellipsis(self):
        """Verify long text is truncated with ellipsis."""
        from openapi_parser.info_extractor import _truncate_description

        text = "A" * 300
        result = _truncate_description(text, 200)

        assert len(result) == 200
        assert result.endswith("...")
        # Verify actual content is 197 chars (200 - 3 for "...")
        assert len(result.replace("...", "")) == 197

    def test_exact_length_not_truncated(self):
        """Verify text at exactly max_length is not truncated."""
        from openapi_parser.info_extractor import _truncate_description

        text = "A" * 200
        result = _truncate_description(text, 200)

        assert result == text
        assert not result.endswith("...")

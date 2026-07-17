"""Unit tests for openapi_parser.readers (Chunk 3.2).

Covers:
- local YAML loading via SimpleDirectoryReader (monkeypatched)
- GitLab loading via GitLabRepositoryReader (monkeypatched)
- endpoints_from_documents — YAML parsing + endpoint extraction
- invalid YAML skipped gracefully
- missing OpenAPI metadata skipped gracefully
- non-YAML GitLab files filtered out
- empty document list returns empty list
- bytes text decoded correctly
"""
from __future__ import annotations

import textwrap
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_MINIMAL_YAML = textwrap.dedent("""\
    openapi: "3.0.1"
    info:
      title: Pay API
      version: "1.0.0"
    paths:
      /payments:
        post:
          summary: Create payment
          responses:
            "201":
              description: Created
""")

_SPEC_NO_PATHS = textwrap.dedent("""\
    openapi: "3.0.1"
    info:
      title: No Paths API
      version: "1.0.0"
""")

_INVALID_YAML = "key: [\nnot closed"

_NO_INFO_YAML = textwrap.dedent("""\
    openapi: "3.0.1"
    paths: {}
""")


def _make_document(text: str, file_path: str = "/fake/spec.yaml") -> MagicMock:
    """Build a mock LlamaIndex Document."""
    doc = MagicMock()
    doc.text = text
    doc.metadata = {"file_path": file_path}
    doc.id_ = file_path
    return doc


# ---------------------------------------------------------------------------
# endpoints_from_documents
# ---------------------------------------------------------------------------

class TestEndpointsFromDocuments:
    def test_single_document_returns_endpoints(self):
        from openapi_parser.readers import endpoints_from_documents
        doc = _make_document(_MINIMAL_YAML)
        results = endpoints_from_documents([doc])
        assert len(results) == 1
        assert results[0].method == "POST"
        assert results[0].path == "/payments"
        assert results[0].api_title == "Pay API"

    def test_empty_list_returns_empty(self):
        from openapi_parser.readers import endpoints_from_documents
        assert endpoints_from_documents([]) == []

    def test_spec_without_paths_returns_no_endpoints(self):
        from openapi_parser.readers import endpoints_from_documents
        doc = _make_document(_SPEC_NO_PATHS)
        assert endpoints_from_documents([doc]) == []

    def test_invalid_yaml_skipped(self):
        from openapi_parser.readers import endpoints_from_documents
        bad_doc = _make_document(_INVALID_YAML, "/bad.yaml")
        good_doc = _make_document(_MINIMAL_YAML, "/good.yaml")
        results = endpoints_from_documents([bad_doc, good_doc])
        assert len(results) == 1
        assert results[0].spec_source == "/good.yaml"

    def test_missing_info_block_skipped(self):
        from openapi_parser.readers import endpoints_from_documents
        doc = _make_document(_NO_INFO_YAML, "/no_info.yaml")
        assert endpoints_from_documents([doc]) == []

    def test_bytes_text_decoded(self):
        from openapi_parser.readers import endpoints_from_documents
        doc = _make_document("", "/bytes.yaml")
        doc.text = _MINIMAL_YAML.encode("utf-8")
        results = endpoints_from_documents([doc])
        assert len(results) == 1

    def test_multiple_documents_combined(self):
        from openapi_parser.readers import endpoints_from_documents
        yaml_2 = textwrap.dedent("""\
            openapi: "3.0.1"
            info:
              title: Account API
              version: "1.0.0"
            paths:
              /accounts:
                get:
                  responses:
                    "200":
                      description: OK
        """)
        docs = [_make_document(_MINIMAL_YAML, "/a.yaml"), _make_document(yaml_2, "/b.yaml")]
        results = endpoints_from_documents(docs)
        assert len(results) == 2
        paths = {r.path for r in results}
        assert paths == {"/payments", "/accounts"}

    def test_spec_source_from_document_metadata(self):
        from openapi_parser.readers import endpoints_from_documents
        doc = _make_document(_MINIMAL_YAML, "/custom/path/spec.yaml")
        results = endpoints_from_documents([doc])
        assert results[0].spec_source == "/custom/path/spec.yaml"


# ---------------------------------------------------------------------------
# read_local
# ---------------------------------------------------------------------------

class TestReadLocal:
    def test_returns_documents_from_simple_directory_reader(self, monkeypatch, tmp_path: Path):
        (tmp_path / "spec.yaml").write_text(_MINIMAL_YAML, encoding="utf-8")

        fake_doc = _make_document(_MINIMAL_YAML, str(tmp_path / "spec.yaml"))
        FakeReader = MagicMock()
        FakeReader.return_value.load_data.return_value = [fake_doc]

        monkeypatch.setattr("openapi_parser.readers.SimpleDirectoryReader", FakeReader)

        from openapi_parser.readers import read_local
        docs = read_local(tmp_path)

        assert len(docs) == 1
        FakeReader.assert_called_once_with(
            str(tmp_path), recursive=True, required_exts=[".yaml", ".yml"]
        )

    def test_nonexistent_directory_returns_empty(self):
        from openapi_parser.readers import read_local
        assert read_local(Path("/nonexistent/path")) == []

    def test_uses_settings_when_no_dir_given(self, monkeypatch, tmp_path: Path):
        class FakeSettings:
            yaml_spec_dir = tmp_path

        monkeypatch.setattr("shared.config.settings", FakeSettings())

        FakeReader = MagicMock()
        FakeReader.return_value.load_data.return_value = []
        monkeypatch.setattr("openapi_parser.readers.SimpleDirectoryReader", FakeReader)

        from openapi_parser.readers import read_local
        result = read_local(None)

        assert result == []
        FakeReader.assert_called_once_with(
            str(tmp_path), recursive=True, required_exts=[".yaml", ".yml"]
        )

    def test_reader_exception_returns_empty(self, monkeypatch, tmp_path: Path):
        FakeReader = MagicMock()
        FakeReader.return_value.load_data.side_effect = RuntimeError("reader error")
        monkeypatch.setattr("openapi_parser.readers.SimpleDirectoryReader", FakeReader)

        from openapi_parser.readers import read_local
        assert read_local(tmp_path) == []


# ---------------------------------------------------------------------------
# read_gitlab
# ---------------------------------------------------------------------------

class TestReadGitlab:
    def _make_gitlab_doc(self, file_path: str, text: str) -> MagicMock:
        doc = MagicMock()
        doc.text = text
        doc.metadata = {"file_path": file_path}
        doc.id_ = file_path
        return doc

    def test_returns_only_yaml_documents(self, monkeypatch):
        yaml_doc = self._make_gitlab_doc("api/spec.yaml", _MINIMAL_YAML)
        json_doc = self._make_gitlab_doc("readme.md", "# ignore")
        txt_doc = self._make_gitlab_doc("notes.txt", "plain text")

        FakeReader = MagicMock()
        FakeReader.return_value.load_data.return_value = [yaml_doc, json_doc, txt_doc]

        FakeGitlab = MagicMock()
        monkeypatch.setattr("openapi_parser.readers.Gitlab", FakeGitlab)
        monkeypatch.setattr("openapi_parser.readers.GitLabRepositoryReader", FakeReader)

        from openapi_parser.readers import read_gitlab
        docs = read_gitlab(project_id=42, ref="main")

        assert len(docs) == 1
        assert docs[0].metadata["file_path"] == "api/spec.yaml"

    def test_uses_adorsys_config_when_flagged(self, monkeypatch):
        class FakeSettings:
            adorsys_base_url = "https://git.adorsys.de"
            adorsys_token = "adorsys-token"
            gitlab_base_url = "https://gitlab.com"
            gitlab_token = "gitlab-token"

        monkeypatch.setattr("shared.config.settings", FakeSettings())

        FakeReader = MagicMock()
        FakeReader.return_value.load_data.return_value = []
        FakeGitlab = MagicMock()
        monkeypatch.setattr("openapi_parser.readers.Gitlab", FakeGitlab)
        monkeypatch.setattr("openapi_parser.readers.GitLabRepositoryReader", FakeReader)

        from openapi_parser.readers import read_gitlab
        read_gitlab(project_id=99, ref="develop", use_adorsys=True)

        FakeGitlab.assert_called_once_with(
            url="https://git.adorsys.de", private_token="adorsys-token"
        )

    def test_uses_public_gitlab_config_by_default(self, monkeypatch):
        class FakeSettings:
            adorsys_base_url = "https://git.adorsys.de"
            adorsys_token = "adorsys-token"
            gitlab_base_url = "https://gitlab.com"
            gitlab_token = "public-token"

        monkeypatch.setattr("shared.config.settings", FakeSettings())

        FakeReader = MagicMock()
        FakeReader.return_value.load_data.return_value = []
        FakeGitlab = MagicMock()
        monkeypatch.setattr("openapi_parser.readers.Gitlab", FakeGitlab)
        monkeypatch.setattr("openapi_parser.readers.GitLabRepositoryReader", FakeReader)

        from openapi_parser.readers import read_gitlab
        read_gitlab(project_id=7)

        FakeGitlab.assert_called_once_with(
            url="https://gitlab.com", private_token="public-token"
        )

    def test_reader_exception_returns_empty(self, monkeypatch):
        FakeReader = MagicMock()
        FakeReader.return_value.load_data.side_effect = Exception("network error")
        FakeGitlab = MagicMock()
        monkeypatch.setattr("openapi_parser.readers.Gitlab", FakeGitlab)
        monkeypatch.setattr("openapi_parser.readers.GitLabRepositoryReader", FakeReader)

        from openapi_parser.readers import read_gitlab
        assert read_gitlab(project_id=1) == []

    def test_yml_extension_included(self, monkeypatch):
        yml_doc = self._make_gitlab_doc("api/spec.yml", _MINIMAL_YAML)

        FakeReader = MagicMock()
        FakeReader.return_value.load_data.return_value = [yml_doc]
        FakeGitlab = MagicMock()
        monkeypatch.setattr("openapi_parser.readers.Gitlab", FakeGitlab)
        monkeypatch.setattr("openapi_parser.readers.GitLabRepositoryReader", FakeReader)

        from openapi_parser.readers import read_gitlab
        docs = read_gitlab(project_id=1)
        assert len(docs) == 1

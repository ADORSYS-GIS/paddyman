"""Unit tests for annotation attribute extraction.

Covers AST-based extraction (annotation_value_extractor),
string-based parsing (annotation_string_parser), and end-to-end
annotation normalisation covering Spring, Lombok, and validation
annotation patterns.
"""
from __future__ import annotations

import sys
from pathlib import Path

_PARSERS_ROOT = Path(__file__).resolve().parent.parent.parent
_POC_ROOT = _PARSERS_ROOT.parent
for _p in (str(_POC_ROOT), str(_PARSERS_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from java_parser.annotation_string_parser import parse_attributes
from java_parser.annotation_normalizer import (
    normalize_annotation_obj,
    normalize_annotation_str,
    normalize_annotations,
)
from java_parser.java_ast.models import JavaAnnotation
from java_parser.java_ast.extractor import extract_file_ast
from java_parser.java_ast.parser import parse_bytes


# ── Helper ─────────────────────────────────────────────────────────────────────

def _extract_class_annotations(src: str) -> list[dict]:
    """Parse Java source and return normalised annotations for the first class."""
    root = parse_bytes(src.encode())
    result = extract_file_ast(root, file_path="Test.java", repository="repo", module="module")
    assert result.declarations, "No declarations found"
    decl = result.declarations[0]
    return [
        normalize_annotation_obj(ann, result.imports)
        for ann in decl.annotations
    ]


# ── parse_attributes (string parser) ──────────────────────────────────────────


class TestParseAttributes:
    def test_empty_returns_empty_dict(self) -> None:
        assert parse_attributes("") == {}
        assert parse_attributes(None) == {}

    def test_single_string_attribute(self) -> None:
        result = parse_attributes('"${aspsp.profile.baseUrl}"')
        assert result == {"value": "${aspsp.profile.baseUrl}"}

    def test_single_numeric_attribute(self) -> None:
        result = parse_attributes("1")
        assert result == {"value": "1"}

    def test_named_string_attribute(self) -> None:
        result = parse_attributes('value = "/api/v1"')
        assert result == {"value": "/api/v1"}

    def test_named_boolean_attribute(self) -> None:
        result = parse_attributes("required = false")
        assert result == {"required": "false"}

    def test_named_enum_attribute(self) -> None:
        result = parse_attributes("method = RequestMethod.POST")
        assert result == {"method": "RequestMethod.POST"}

    def test_multiple_named_attributes(self) -> None:
        result = parse_attributes('value = "/accounts", method = RequestMethod.GET')
        assert result["value"] == "/accounts"
        assert result["method"] == "RequestMethod.GET"

    def test_array_attribute_parsed_as_list(self) -> None:
        result = parse_attributes('produces = {"application/json", "application/xml"}')
        assert result["produces"] == ["application/json", "application/xml"]

    def test_comma_inside_braces_not_split(self) -> None:
        result = parse_attributes('value = "/path", produces = {"json", "xml"}')
        assert result["value"] == "/path"
        assert result["produces"] == ["json", "xml"]


# ── normalize_annotation_str ───────────────────────────────────────────────────


class TestNormalizeAnnotationStr:
    def test_marker_annotation_no_attributes(self) -> None:
        result = normalize_annotation_str("@Override", [])
        assert result["name"] == "@Override"
        assert result["attributes"] == {}

    def test_single_value_default_key(self) -> None:
        result = normalize_annotation_str('@Value("${prop}")', [])
        assert result["attributes"] == {"value": "${prop}"}

    def test_named_attribute(self) -> None:
        result = normalize_annotation_str('@Autowired(required = false)', [])
        assert result["attributes"] == {"required": "false"}

    def test_import_resolution(self) -> None:
        imports = ["org.springframework.beans.factory.annotation.Autowired"]
        result = normalize_annotation_str("@Autowired", imports)
        assert result["qualified_name"] == "org.springframework.beans.factory.annotation.Autowired"

    def test_without_at_prefix(self) -> None:
        result = normalize_annotation_str("Deprecated", [])
        assert result["name"] == "@Deprecated"


# ── normalize_annotation_obj (AST-based) ───────────────────────────────────────


class TestNormalizeAnnotationObj:
    def test_marker_annotation_empty_attributes(self) -> None:
        ann = JavaAnnotation(name="Data")
        result = normalize_annotation_obj(ann, [])
        assert result["name"] == "@Data"
        assert result["attributes"] == {}

    def test_pre_populated_attributes_used_directly(self) -> None:
        ann = JavaAnnotation(name="Order", attributes={"value": "1"})
        result = normalize_annotation_obj(ann, [])
        assert result["attributes"] == {"value": "1"}

    def test_legacy_value_field_parsed_as_fallback(self) -> None:
        ann = JavaAnnotation(name="Value", value='"${my.prop}"')
        result = normalize_annotation_obj(ann, [])
        assert result["attributes"] == {"value": "${my.prop}"}


# ── AST-based extraction (end-to-end through parse_and_extract) ─────────────


class TestASTAnnotationExtraction:
    def test_marker_annotation_empty_attributes(self) -> None:
        anns = _extract_class_annotations("@Deprecated\npublic class Old {}")
        assert len(anns) == 1
        assert anns[0]["name"] == "@Deprecated"
        assert anns[0]["attributes"] == {}

    def test_single_string_value_annotation(self) -> None:
        anns = _extract_class_annotations(
            '@RequestMapping("/api/v1")\npublic class AccountController {}'
        )
        assert len(anns) == 1
        assert anns[0]["attributes"] == {"value": "/api/v1"}

    def test_named_string_attribute(self) -> None:
        anns = _extract_class_annotations(
            '@RequestMapping(value = "/api/v1")\npublic class AccountController {}'
        )
        assert anns[0]["attributes"]["value"] == "/api/v1"

    def test_boolean_attribute(self) -> None:
        anns = _extract_class_annotations(
            "@Autowired(required = false)\npublic class Svc {}"
        )
        assert anns[0]["attributes"]["required"] == "false"

    def test_enum_attribute(self) -> None:
        anns = _extract_class_annotations(
            "@RequestMapping(method = RequestMethod.POST)\npublic class Ctrl {}"
        )
        assert anns[0]["attributes"]["method"] == "RequestMethod.POST"

    def test_array_attribute(self) -> None:
        anns = _extract_class_annotations(
            '@RequestMapping(produces = {"application/json", "application/xml"})\n'
            "public class Ctrl {}"
        )
        produces = anns[0]["attributes"]["produces"]
        assert isinstance(produces, list)
        assert "application/json" in produces
        assert "application/xml" in produces

    def test_multiple_named_attributes(self) -> None:
        anns = _extract_class_annotations(
            '@RequestMapping(value = "/api", method = RequestMethod.GET)\n'
            "public class Ctrl {}"
        )
        attrs = anns[0]["attributes"]
        assert attrs["value"] == "/api"
        assert attrs["method"] == "RequestMethod.GET"

    def test_multiple_annotations(self) -> None:
        anns = _extract_class_annotations(
            "@Deprecated\n@SuppressWarnings\npublic class Old {}"
        )
        assert len(anns) == 2
        names = {a["name"] for a in anns}
        assert "@Deprecated" in names
        assert "@SuppressWarnings" in names


# ── Integration: Spring annotations ─────────────────────────────────────────


class TestSpringAnnotationIntegration:
    def test_request_mapping_path_and_method(self) -> None:
        anns = _extract_class_annotations(
            "import org.springframework.web.bind.annotation.RequestMapping;\n"
            '@RequestMapping(value = "/accounts", method = RequestMethod.GET)\n'
            "public class AccountController {}"
        )
        assert anns[0]["qualified_name"] == (
            "org.springframework.web.bind.annotation.RequestMapping"
        )
        assert anns[0]["attributes"]["value"] == "/accounts"

    def test_value_annotation_with_spel(self) -> None:
        anns = _extract_class_annotations(
            "import org.springframework.beans.factory.annotation.Value;\n"
            '@Value("${aspsp.profile.baseUrl}")\n'
            "public class ProfileConfig {}"
        )
        assert anns[0]["attributes"]["value"] == "${aspsp.profile.baseUrl}"
        assert anns[0]["qualified_name"] == (
            "org.springframework.beans.factory.annotation.Value"
        )

    def test_autowired_required_false(self) -> None:
        anns = _extract_class_annotations(
            "import org.springframework.beans.factory.annotation.Autowired;\n"
            "@Autowired(required = false)\n"
            "public class OptionalSvc {}"
        )
        assert anns[0]["attributes"]["required"] == "false"


# ── Integration: Lombok annotations ────────────────────────────────────────


class TestLombokAnnotationIntegration:
    def test_data_annotation_no_attributes(self) -> None:
        anns = _extract_class_annotations("@Data\npublic class Foo {}")
        assert len(anns) == 1
        assert anns[0]["name"] == "@Data"
        assert anns[0]["attributes"] == {}

    def test_builder_annotation_no_attributes(self) -> None:
        anns = _extract_class_annotations("@Builder\npublic class Foo {}")
        assert anns[0]["name"] == "@Builder"
        assert anns[0]["attributes"] == {}


# ── Integration: Validation annotations ────────────────────────────────────


class TestValidationAnnotationIntegration:
    def test_not_null_no_attributes(self) -> None:
        anns = _extract_class_annotations("@NotNull\npublic class Foo {}")
        assert anns[0]["name"] == "@NotNull"
        assert anns[0]["attributes"] == {}

    def test_size_with_min_and_max(self) -> None:
        anns = _extract_class_annotations(
            "@Size(min = 1, max = 100)\npublic class Foo {}"
        )
        attrs = anns[0]["attributes"]
        assert attrs["min"] == "1"
        assert attrs["max"] == "100"

"""Unit tests for Spring annotation extraction (Chunk 1.4).

Covers:
- Controller annotation detection (@RestController, @RequestMapping, mapping verbs)
- Service detection (@Service)
- Repository detection (@Repository)
- Component detection (@Component)
- Entity detection (@Entity)
- Annotation value / attribute extraction
- Classes with multiple Spring annotations
- Classes with no Spring annotations (no result returned)
- Invalid / empty inputs
"""
from __future__ import annotations

import pytest

from java_parser.java_ast.extractor import extract_file_ast
from java_parser.java_ast.parser import parse_bytes
from java_parser.spring.classifier import extract_spring_components, extract_spring_from_source
from java_parser.spring.models import SpringComponentResult


# ── Test helpers ───────────────────────────────────────────────────────────────


def _extract(src: str) -> list[SpringComponentResult]:
    """Parse *src* and return extracted Spring components."""
    root = parse_bytes(src.encode())
    file_ast = extract_file_ast(
        root,
        file_path="Test.java",
        repository="test-repo",
        module="test-module",
    )
    return extract_spring_components(root, file_ast)


def _first(src: str) -> SpringComponentResult:
    results = _extract(src)
    assert results, "Expected at least one SpringComponentResult"
    return results[0]


# ── Controller detection ───────────────────────────────────────────────────────


class TestControllerDetection:
    def test_rest_controller_marker(self) -> None:
        result = _first(
            "package com.example;\n"
            "@RestController\n"
            "public class PaymentController {}"
        )
        assert result.component_type == "controller"
        assert "RestController" in result.annotations
        assert result.class_name == "PaymentController"
        assert result.package == "com.example"

    def test_request_mapping_with_path(self) -> None:
        result = _first(
            "@RestController\n"
            "@RequestMapping(\"/api/v1\")\n"
            "public class OrderController {}"
        )
        assert result.component_type == "controller"
        assert "RequestMapping" in result.annotations
        assert "/api/v1" in result.mapped_paths

    def test_get_mapping(self) -> None:
        result = _first(
            "@RestController\n"
            "@GetMapping(\"/payments\")\n"
            "public class PayController {}"
        )
        assert "GetMapping" in result.annotations
        assert "GET" in result.http_methods
        assert "/payments" in result.mapped_paths

    def test_post_mapping(self) -> None:
        result = _first(
            "@RestController\n"
            "@PostMapping(\"/payments\")\n"
            "public class PayController {}"
        )
        assert "PostMapping" in result.annotations
        assert "POST" in result.http_methods

    def test_controller_type_priority(self) -> None:
        """Controller takes priority over other stereotype annotations."""
        result = _first(
            "@RestController\n"
            "@Service\n"
            "public class HybridClass {}"
        )
        assert result.component_type == "controller"


# ── Service detection ──────────────────────────────────────────────────────────


class TestServiceDetection:
    def test_service_annotation(self) -> None:
        result = _first(
            "package de.adorsys.payments;\n"
            "@Service\n"
            "public class PaymentService {}"
        )
        assert result.component_type == "service"
        assert result.class_name == "PaymentService"
        assert result.package == "de.adorsys.payments"
        assert result.annotations == ["Service"]

    def test_service_no_path(self) -> None:
        result = _first("@Service\npublic class FeeService {}")
        assert result.mapped_paths == []
        assert result.http_methods == []


# ── Repository detection ───────────────────────────────────────────────────────


class TestRepositoryDetection:
    def test_repository_annotation(self) -> None:
        result = _first(
            "package com.example.repo;\n"
            "@Repository\n"
            "public class AccountRepository {}"
        )
        assert result.component_type == "repository"
        assert result.class_name == "AccountRepository"
        assert result.annotations == ["Repository"]

    def test_repository_provenance(self) -> None:
        root = parse_bytes(b"@Repository\npublic class R {}")
        file_ast = extract_file_ast(
            root, file_path="src/R.java", repository="my-repo", module="core"
        )
        results = extract_spring_components(root, file_ast)
        assert results[0].repository == "my-repo"
        assert results[0].module == "core"
        assert results[0].file_path == "src/R.java"


# ── Component detection ────────────────────────────────────────────────────────


class TestComponentDetection:
    def test_component_annotation(self) -> None:
        result = _first(
            "@Component\n"
            "public class EmailNotifier {}"
        )
        assert result.component_type == "component"
        assert result.class_name == "EmailNotifier"

    def test_component_lower_priority_than_service(self) -> None:
        result = _first("@Service\n@Component\npublic class X {}")
        assert result.component_type == "service"


# ── Entity detection ───────────────────────────────────────────────────────────


class TestEntityDetection:
    def test_entity_annotation(self) -> None:
        result = _first(
            "package com.example.model;\n"
            "@Entity\n"
            "public class Payment {}"
        )
        assert result.component_type == "entity"
        assert result.class_name == "Payment"
        assert result.annotations == ["Entity"]

    def test_entity_no_paths(self) -> None:
        result = _first("@Entity\npublic class Account {}")
        assert result.mapped_paths == []


# ── Annotation value extraction ────────────────────────────────────────────────


class TestAnnotationValueExtraction:
    def test_named_value_attribute(self) -> None:
        result = _first(
            "@RestController\n"
            "@RequestMapping(value = \"/accounts\")\n"
            "public class AccountController {}"
        )
        assert "/accounts" in result.mapped_paths

    def test_multiple_mapping_annotations(self) -> None:
        result = _first(
            "@RestController\n"
            "@RequestMapping(\"/payments\")\n"
            "@PostMapping(\"/payments/create\")\n"
            "public class PayController {}"
        )
        assert "/payments" in result.mapped_paths
        assert "/payments/create" in result.mapped_paths
        assert "POST" in result.http_methods

    def test_annotation_details_present(self) -> None:
        result = _first(
            "@RestController\n"
            "@RequestMapping(\"/api\")\n"
            "public class ApiController {}"
        )
        names = [a.name for a in result.annotation_details]
        assert "RestController" in names
        assert "RequestMapping" in names
        request_mapping = next(
            a for a in result.annotation_details if a.name == "RequestMapping"
        )
        assert request_mapping.value == "/api"

    def test_to_dict_output(self) -> None:
        result = _first(
            "@Service\n"
            "public class BillingService {}"
        )
        d = result.to_dict()
        assert d["type"] == "service"
        assert d["class"] == "BillingService"
        assert "Service" in d["annotations"]
        assert isinstance(d["annotation_details"], list)


# ── Multiple annotations ───────────────────────────────────────────────────────


class TestMultipleAnnotations:
    def test_rest_controller_and_request_mapping(self) -> None:
        result = _first(
            "@RestController\n"
            "@RequestMapping(\"/v2/orders\")\n"
            "public class OrderControllerV2 {}"
        )
        assert len(result.annotations) == 2
        assert "RestController" in result.annotations
        assert "RequestMapping" in result.annotations

    def test_annotation_order_preserved(self) -> None:
        result = _first(
            "@RestController\n"
            "@GetMapping(\"/items\")\n"
            "@PostMapping(\"/items\")\n"
            "public class ItemController {}"
        )
        assert result.annotations[0] == "RestController"
        assert "GET" in result.http_methods
        assert "POST" in result.http_methods

    def test_non_spring_annotations_ignored(self) -> None:
        result = _first(
            "@SuppressWarnings(\"unchecked\")\n"
            "@Service\n"
            "public class CleanService {}"
        )
        assert result.annotations == ["Service"]


# ── No Spring annotations ──────────────────────────────────────────────────────


class TestNoSpringAnnotations:
    def test_plain_class_returns_empty(self) -> None:
        results = _extract("public class PlainClass {}")
        assert results == []

    def test_non_spring_annotation_only(self) -> None:
        results = _extract(
            "@SuppressWarnings(\"all\")\n"
            "public class UtilClass {}"
        )
        assert results == []

    def test_empty_file(self) -> None:
        results = _extract("")
        assert results == []

    def test_interface_without_spring(self) -> None:
        results = _extract("public interface Foo {}")
        assert results == []


# ── extract_spring_from_source convenience wrapper ─────────────────────────────


class TestExtractSpringFromSource:
    def test_source_bytes_input(self) -> None:
        src = b"@Repository\npublic class UserRepo {}"
        results = extract_spring_from_source(
            src, file_path="UserRepo.java", repository="repo", module="data"
        )
        assert len(results) == 1
        assert results[0].component_type == "repository"
        assert results[0].file_path == "UserRepo.java"

    def test_multiple_classes_in_file(self) -> None:
        src = (
            b"@Service\npublic class AlphaService {}\n"
            b"@Repository\npublic class AlphaRepo {}"
        )
        results = extract_spring_from_source(src)
        types = {r.component_type for r in results}
        assert "service" in types
        assert "repository" in types
        assert len(results) == 2

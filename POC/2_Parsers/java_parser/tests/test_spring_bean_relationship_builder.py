"""Unit tests for Spring bean injection relationship builder."""
from __future__ import annotations

from java_parser.spring_bean_relationship_builder import build_injects_bean_relationships


def _class(name: str, annotations: list[dict] | None = None) -> dict:
    return {"type": "Class", "name": name, "uuid": f"uuid-{name}", "annotations": annotations or []}


def test_field_injection_with_autowired() -> None:
    entities = [
        _class("AccountService"),
        _class("AccountRepository"),
        {"type": "Field", "class": "AccountService", "name": "accountRepository", "field_type": "AccountRepository", "annotations": [{"name": "@Autowired", "attributes": {}}]},
    ]
    rels = build_injects_bean_relationships(entities)
    assert len(rels) == 1
    assert rels[0]["type"] == "INJECTS_BEAN"
    assert rels[0]["properties"]["injection_type"] == "field"
    assert rels[0]["properties"]["required"] is True


def test_constructor_injection_with_autowired() -> None:
    entities = [
        _class("PaymentService"),
        _class("PaymentRepository"),
        {"type": "Constructor", "class": "PaymentService", "name": "PaymentService", "qualified_class": "com.example.PaymentService", "annotations": [{"name": "@Autowired", "attributes": {}}]},
        {"type": "Parameter", "method_qualified_name": "com.example.PaymentService.<init>", "name": "paymentRepository", "parameter_type": "PaymentRepository", "position": 0, "annotations": []},
    ]
    rels = build_injects_bean_relationships(entities)
    assert rels[0]["properties"]["injection_type"] == "constructor"
    assert rels[0]["properties"]["parameter_position"] == 0


def test_setter_injection_detected() -> None:
    entities = [
        _class("S"), _class("Repo"),
        {"type": "Method", "class": "S", "name": "setRepo", "qualified_class": "x.S", "annotations": [{"name": "@Autowired", "attributes": {}}]},
        {"type": "Parameter", "method_qualified_name": "x.S.setRepo", "name": "repo", "parameter_type": "Repo", "position": 0, "annotations": []},
    ]
    rels = build_injects_bean_relationships(entities)
    assert rels[0]["properties"]["injection_type"] == "setter"
    assert rels[0]["properties"]["setter_method"] == "setRepo"


def test_qualifier_annotation_extracted() -> None:
    entities = [
        _class("PaymentService"), _class("PaymentRepository"),
        {"type": "Field", "class": "PaymentService", "name": "repo", "field_type": "PaymentRepository", "annotations": [{"name": "@Autowired", "attributes": {}}, {"name": "@Qualifier", "attributes": {"value": "primaryPaymentRepo"}}]},
    ]
    rels = build_injects_bean_relationships(entities)
    assert rels[0]["properties"]["qualifier"] == '@Qualifier("primaryPaymentRepo")'
    assert rels[0]["properties"]["bean_name"] == "primaryPaymentRepo"


def test_named_annotation_extracted() -> None:
    entities = [
        _class("NService"), _class("EmailClient"),
        {"type": "Field", "class": "NService", "name": "emailClient", "field_type": "EmailClient", "annotations": [{"name": "@Inject", "attributes": {}}, {"name": "@Named", "attributes": {"value": "emailClientBean"}}]},
    ]
    rels = build_injects_bean_relationships(entities)
    assert rels[0]["properties"]["qualifier"] == '@Named("emailClientBean")'


def test_required_false_from_autowired() -> None:
    entities = [
        _class("NotificationService"), _class("EmailClient"),
        {"type": "Field", "class": "NotificationService", "name": "emailClient", "field_type": "EmailClient", "annotations": [{"name": "@Autowired", "attributes": {"required": False}}]},
    ]
    rels = build_injects_bean_relationships(entities)
    assert rels[0]["properties"]["required"] is False


def test_multiple_constructor_parameters() -> None:
    entities = [
        _class("OrderService"), _class("RepoA"), _class("RepoB"),
        {"type": "Constructor", "class": "OrderService", "name": "OrderService", "qualified_class": "x.OrderService", "annotations": [{"name": "@Autowired", "attributes": {}}]},
        {"type": "Parameter", "method_qualified_name": "x.OrderService.<init>", "name": "a", "parameter_type": "RepoA", "position": 0, "annotations": []},
        {"type": "Parameter", "method_qualified_name": "x.OrderService.<init>", "name": "b", "parameter_type": "RepoB", "position": 1, "annotations": []},
    ]
    rels = build_injects_bean_relationships(entities)
    assert len(rels) == 2


def test_resource_annotation_supported() -> None:
    entities = [
        _class("X"), _class("Y"),
        {"type": "Field", "class": "X", "name": "y", "field_type": "Y", "annotations": [{"name": "@Resource", "attributes": {"name": "yBean"}}]},
    ]
    rels = build_injects_bean_relationships(entities)
    assert rels[0]["properties"]["annotation"] == "@Resource"
    assert rels[0]["properties"]["bean_name"] == "yBean"

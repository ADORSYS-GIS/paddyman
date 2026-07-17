"""Tests for enhanced CALLS extraction metadata."""
from __future__ import annotations

from java_parser.java_ast.parser import parse_bytes
from java_parser.relationships.call_extractor import extract_call_relationships


def _extract_calls(src: str):
    root = parse_bytes(src.encode())
    return extract_call_relationships(
        root,
        file_path="Test.java",
        repository="test-repo",
        module="test-module",
        package="com.example",
    )


def test_static_call_metadata() -> None:
    calls = _extract_calls(
        """
        class Test {
            void caller() {
                Math.max(1, 2);
            }
        }
        """
    )
    assert len(calls) == 1
    call = calls[0]
    assert call.is_static is True
    assert call.receiver_type == "Math"
    assert call.arguments_count == 2
    assert call.argument_types == ["int", "int"]
    assert call.method_signature == "max(int, int)"


def test_instance_call_metadata() -> None:
    calls = _extract_calls(
        """
        class Test {
            void caller() {
                account.getBalance();
            }
        }
        """
    )
    assert len(calls) == 1
    call = calls[0]
    assert call.is_static is False
    assert call.receiver_type == "account"
    assert call.receiver_variable == "account"
    assert call.arguments_count == 0
    assert call.argument_types == []
    assert call.method_signature == "getBalance()"


def test_constructor_call_metadata() -> None:
    calls = _extract_calls(
        """
        class Test {
            void caller() {
                new Person("John", 30);
            }
        }
        """
    )
    assert len(calls) == 1
    call = calls[0]
    assert call.is_constructor is True
    assert call.target_method == "<init>"
    assert call.argument_types == ["String", "int"]
    assert call.method_signature == "Person.<init>(String, int)"


def test_chain_call_and_line_numbers() -> None:
    calls = _extract_calls(
        """
        class Test {
            void caller() {
                account.getOwner().getName();
            }
        }
        """
    )
    assert len(calls) == 2
    methods = {c.target_method for c in calls}
    assert methods == {"getOwner", "getName"}
    assert all(c.call_site_line == 4 for c in calls)

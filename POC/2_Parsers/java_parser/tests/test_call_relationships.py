"""Unit tests for method call and constructor call relationship extraction.

Tests the comprehensive CALLS relationship extraction including:
- Instance method calls
- Static method calls
- Constructor calls (new expressions)
- Chained method calls
- Super and this calls
- Call site line numbers
- Arguments counting
- Call type differentiation (static vs instance)
"""
from __future__ import annotations

import pytest

from java_parser.java_ast.parser import parse_bytes
from java_parser.relationships.call_extractor import extract_call_relationships


def _extract_calls(src: str) -> list:
    """Parse *src* and extract call relationships."""
    root = parse_bytes(src.encode())
    return extract_call_relationships(
        root,
        file_path="Test.java",
        repository="test-repo",
        module="test-module",
        package="com.example",
    )


def _to_dicts(relationships: list) -> list[dict]:
    """Convert relationships to dicts for easier assertion."""
    return [rel.to_dict() for rel in relationships]


class TestInstanceMethodCalls:
    """Test instance method call extraction."""
    
    def test_simple_instance_call(self) -> None:
        """Verify simple instance method call is captured."""
        calls = _extract_calls(
            """
            package com.example;
            class Test {
                void caller() {
                    obj.doSomething();
                }
            }
            """
        )
        assert len(calls) == 1
        call = calls[0].to_dict()
        assert call["source_method"] == "caller"
        assert call["target_method"] == "doSomething"
        assert call["target_class"] == "obj"
        assert call["is_static"] is False
        assert call["is_constructor"] is False
        assert call["call_site_line"] == 5
        assert call["arguments_count"] == 0
    
    def test_instance_call_with_arguments(self) -> None:
        """Verify arguments are counted correctly."""
        calls = _extract_calls(
            """
            class Test {
                void caller() {
                    obj.method(a, b, c);
                }
            }
            """
        )
        assert len(calls) == 1
        assert calls[0].arguments_count == 3


class TestStaticMethodCalls:
    """Test static method call extraction."""
    
    def test_static_call_identified(self) -> None:
        """Verify static method call is identified by uppercase receiver."""
        calls = _extract_calls(
            """
            class Test {
                void caller() {
                    Utils.staticMethod();
                }
            }
            """
        )
        assert len(calls) == 1
        call = calls[0].to_dict()
        assert call["target_method"] == "staticMethod"
        assert call["target_class"] == "Utils"
        assert call["is_static"] is True
        assert call["is_constructor"] is False
    
    def test_static_call_with_qualified_name(self) -> None:
        """Verify fully qualified static call."""
        calls = _extract_calls(
            """
            class Test {
                void caller() {
                    com.example.Helper.doWork();
                }
            }
            """
        )
        assert len(calls) == 1
        assert calls[0].target_class == "com.example.Helper"
        assert calls[0].is_static is True


class TestConstructorCalls:
    """Test constructor call (new expression) extraction."""
    
    def test_simple_constructor_call(self) -> None:
        """Verify constructor call is captured."""
        calls = _extract_calls(
            """
            class Test {
                void caller() {
                    new ArrayList<>();
                }
            }
            """
        )
        assert len(calls) == 1
        call = calls[0].to_dict()
        assert call["target_method"] == "<init>"
        assert call["target_class"] == "ArrayList"
        assert call["is_constructor"] is True
        assert call["is_static"] is False
    
    def test_constructor_with_arguments(self) -> None:
        """Verify constructor arguments are counted."""
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
        assert calls[0].arguments_count == 2
        assert calls[0].is_constructor is True
    
    def test_generic_type_constructor(self) -> None:
        """Verify generic type in constructor is handled."""
        calls = _extract_calls(
            """
            class Test {
                void caller() {
                    new HashMap<String, Integer>();
                }
            }
            """
        )
        assert len(calls) == 1
        # Should extract base type without generics
        assert calls[0].target_class == "HashMap"


class TestChainedCalls:
    """Test chained method call extraction."""
    
    def test_chained_method_calls(self) -> None:
        """Verify each call in chain creates separate relationship."""
        calls = _extract_calls(
            """
            class Test {
                void caller() {
                    builder.setA().setB().build();
                }
            }
            """
        )
        # Should have 3 separate call relationships
        assert len(calls) == 3
        methods = {call.target_method for call in calls}
        assert methods == {"setA", "setB", "build"}


class TestCallSiteLineNumbers:
    """Test call site line number extraction."""
    
    def test_line_numbers_accurate(self) -> None:
        """Verify call site line numbers match source."""
        calls = _extract_calls(
            """
            class Test {
                void caller() {
                    obj.first();
                    obj.second();
                    obj.third();
                }
            }
            """
        )
        assert len(calls) == 3
        # Line numbers should be sequential
        line_numbers = sorted([call.call_site_line for call in calls])
        assert line_numbers == [4, 5, 6]


class TestSuperAndThisCalls:
    """Test super and this method call handling."""
    
    def test_super_call(self) -> None:
        """Verify super method call is captured."""
        calls = _extract_calls(
            """
            class Test extends Base {
                void caller() {
                    super.method();
                }
            }
            """
        )
        assert len(calls) == 1
        call = calls[0]
        assert call.target_class == "super"
        assert call.target_method == "method"
    
    def test_this_call(self) -> None:
        """Verify this method call is captured."""
        calls = _extract_calls(
            """
            class Test {
                void caller() {
                    this.helper();
                }
            }
            """
        )
        assert len(calls) == 1
        assert calls[0].target_class == "this"


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_method_no_calls(self) -> None:
        """Verify empty method produces no calls."""
        calls = _extract_calls(
            """
            class Test {
                void caller() {}
            }
            """
        )
        assert len(calls) == 0
    
    def test_multiple_methods_isolated(self) -> None:
        """Verify calls from different methods are tracked separately."""
        calls = _extract_calls(
            """
            class Test {
                void first() {
                    obj.a();
                }
                void second() {
                    obj.b();
                }
            }
            """
        )
        assert len(calls) == 2
        source_methods = {call.source_method for call in calls}
        assert source_methods == {"first", "second"}
    
    def test_constructor_method_body(self) -> None:
        """Verify calls in constructor body are captured."""
        calls = _extract_calls(
            """
            class Test {
                Test() {
                    init();
                }
            }
            """
        )
        assert len(calls) == 1
        assert calls[0].target_method == "init"
    
    def test_deduplication_same_line(self) -> None:
        """Verify duplicate calls to same target in same method are deduplicated."""
        calls = _extract_calls(
            """
            class Test {
                void caller() {
                    obj.method();
                    obj.method();
                }
            }
            """
        )
        # Should only have one relationship for duplicate calls in same method
        assert len(calls) == 1


class TestMixedCallTypes:
    """Test methods with multiple call types."""
    
    def test_method_with_mixed_calls(self) -> None:
        """Verify method with instance, static, and constructor calls."""
        calls = _extract_calls(
            """
            class Test {
                void process() {
                    obj.doWork();
                    Utils.staticHelper();
                    new Result();
                }
            }
            """
        )
        assert len(calls) == 3
        
        # Check we have one of each type
        has_instance = any(not call.is_static and not call.is_constructor for call in calls)
        has_static = any(call.is_static for call in calls if call.is_static is not None)
        has_constructor = any(call.is_constructor for call in calls)
        
        assert has_instance
        assert has_static
        assert has_constructor

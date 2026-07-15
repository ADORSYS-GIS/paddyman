"""Unit tests for deterministic entity normalisation rules."""
from __future__ import annotations

from entities.rules import TypeMapRule, default_rule_chain
from entities.rules.casing import to_pascal_case
from entities.rules.source_pattern import SourcePatternRule


class TestCasing:
    def test_space_separated_name_to_pascal_case(self) -> None:
        assert to_pascal_case("Payment Initiation") == "PaymentInitiation"

    def test_snake_case_name_to_pascal_case(self) -> None:
        assert to_pascal_case("payment_initiation") == "PaymentInitiation"

    def test_kebab_case_name_to_pascal_case(self) -> None:
        assert to_pascal_case("payment-initiation") == "PaymentInitiation"

    def test_camel_case_name_to_pascal_case(self) -> None:
        assert to_pascal_case("paymentInitiation") == "PaymentInitiation"

    def test_all_caps_abbreviation_is_normalised(self) -> None:
        assert to_pascal_case("PaymentAPIController") == "PaymentApiController"


class TestSourcePatterns:
    def test_java_controller_suffix_removed(self) -> None:
        rule = SourcePatternRule()
        assert rule.apply("PaymentController", "controller", "java_parser") == "Payment"

    def test_openapi_method_path_to_resource(self) -> None:
        rule = SourcePatternRule()
        assert rule.apply("POST /payments", "endpoint", "openapi_parser") == "payment"

    def test_openapi_path_parameters_are_ignored(self) -> None:
        rule = SourcePatternRule()
        assert (
            rule.apply("GET /accounts/{accountId}/transactions", "endpoint", "openapi_parser")
            == "transaction"
        )

    def test_unknown_parser_passes_through(self) -> None:
        rule = SourcePatternRule()
        assert rule.apply("Payment Initiation", "concept", "markdown_parser") is None


class TestRuleChain:
    def test_java_payment_controller_to_payment_initiation(self) -> None:
        chain = default_rule_chain()
        assert chain.apply("PaymentController", "controller", "java_parser") == "PaymentInitiation"

    def test_openapi_payment_endpoint_to_payment_initiation(self) -> None:
        chain = default_rule_chain()
        assert chain.apply("POST /payments", "endpoint", "openapi_parser") == "PaymentInitiation"

    def test_documentation_concept_to_payment_initiation(self) -> None:
        chain = default_rule_chain()
        assert chain.apply("Payment Initiation", "concept", "markdown_parser") == "PaymentInitiation"

    def test_deterministic_output_for_same_input(self) -> None:
        chain = default_rule_chain()
        first = chain.apply("POST /payments", "endpoint", "openapi_parser")
        second = chain.apply("POST /payments", "endpoint", "openapi_parser")
        assert first == second == "PaymentInitiation"


class TestTypeMap:
    def test_known_source_type_maps_to_canonical_type(self) -> None:
        assert TypeMapRule().normalise_type("controller") == "api_component"

    def test_unknown_type_falls_back_to_concept(self) -> None:
        assert TypeMapRule().normalise_type("unknown") == "concept"
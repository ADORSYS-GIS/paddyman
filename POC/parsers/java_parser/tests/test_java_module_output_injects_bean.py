"""Integration tests for INJECTS_BEAN relationships in module output."""
from __future__ import annotations

from pathlib import Path

from java_module_output import write_java_module_normalized_jsons
from normalized_json import load_normalized_json


def test_spring_beans_have_injects_bean_relationships(tmp_path: Path) -> None:
    repo = tmp_path / "test-repo"
    repo.mkdir()
    (repo / "App.java").write_text(
        "package com.example;\n"
        "import org.springframework.stereotype.Service;\n"
        "import org.springframework.stereotype.Repository;\n"
        "import org.springframework.beans.factory.annotation.Autowired;\n"
        "@Repository class AccountRepository {}\n"
        "@Service class AccountService {\n"
        "  @Autowired private AccountRepository accountRepository;\n"
        "}\n"
    )
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    write_java_module_normalized_jsons(source_dir=tmp_path, output_dir=out_dir)

    bundle = load_normalized_json(list(out_dir.glob("*.json"))[0])
    rels = [r for r in bundle.relationships if r.get("type") == "INJECTS_BEAN"]
    assert len(rels) == 1
    props = rels[0].get("properties", {})
    assert props.get("framework") == "spring"
    assert props.get("injection_type") == "field"


def test_qualifier_name_matches_named_bean_definition(tmp_path: Path) -> None:
    repo = tmp_path / "test-repo"
    repo.mkdir()
    (repo / "Payment.java").write_text(
        "package com.example;\n"
        "import org.springframework.stereotype.Repository;\n"
        "import org.springframework.stereotype.Service;\n"
        "import org.springframework.beans.factory.annotation.Autowired;\n"
        "import org.springframework.beans.factory.annotation.Qualifier;\n"
        "@Repository(\"primaryPaymentRepo\") class PrimaryPaymentRepository {}\n"
        "@Service class PaymentService {\n"
        "  @Autowired @Qualifier(\"primaryPaymentRepo\") private PrimaryPaymentRepository paymentRepository;\n"
        "}\n"
    )
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    write_java_module_normalized_jsons(source_dir=tmp_path, output_dir=out_dir)

    bundle = load_normalized_json(list(out_dir.glob("*.json"))[0])
    rel = next(r for r in bundle.relationships if r.get("type") == "INJECTS_BEAN")
    props = rel.get("properties", {})
    assert props.get("bean_name") == "primaryPaymentRepo"
    assert props.get("qualifier") == '@Qualifier("primaryPaymentRepo")'
    assert rel.get("target_resolved") is not False

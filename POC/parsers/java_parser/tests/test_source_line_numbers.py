"""Regression tests for Java entity source line numbers."""
from __future__ import annotations

import sys
from pathlib import Path

_PARSERS_ROOT = Path(__file__).resolve().parent.parent.parent
_POC_ROOT = _PARSERS_ROOT.parent
for _path in (str(_POC_ROOT), str(_PARSERS_ROOT)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from java_parser.java_entity_builder import entities_for_record


class _Record:
    def __init__(self, relative_path: str, lines: int) -> None:
        self.repository = "repo"
        self.module = "mod"
        self.relative_path = relative_path
        self.lines = lines


def _write_day_deserializer(tmp_path: Path) -> _Record:
    lines = [f"// filler {line}" for line in range(1, 31)]
    lines.extend(
        [
            "public class DayOfExecutionDeserializer {",
            "  private final String pattern;",
            "",
            "  public DayOfExecutionDeserializer() {",
            "    this.pattern = \"yyyy-MM-dd\";",
            "  }",
            "",
            "  public DayOfExecution deserialize(String value) {",
            "    if (value == null) {",
            "      return null;",
            "    }",
            "    return DayOfExecution.valueOf(value);",
            "  }",
            "",
            "  enum DayOfExecution {",
            "    MONDAY",
            "  }",
            "}",
            "",
            "interface ExecutionReader {}",
            "",
            "enum ExecutionState { ACTIVE }",
        ]
    )
    java_file = tmp_path / "src" / "DayOfExecutionDeserializer.java"
    java_file.parent.mkdir(parents=True)
    java_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return _Record(str(java_file.relative_to(tmp_path)), len(lines))


def test_day_deserializer_entities_have_source_line_numbers(tmp_path: Path) -> None:
    record = _write_day_deserializer(tmp_path)
    entities = entities_for_record(tmp_path, record, "doc:id", "mod")
    assert entities

    for entity in entities:
        assert entity["start_line"] >= 1
        assert entity["end_line"] >= entity["start_line"]

    by_type = {(entity["type"], entity["name"]): entity for entity in entities}
    assert by_type[("Class", "DayOfExecutionDeserializer")]["start_line"] == 31
    assert by_type[("Class", "DayOfExecutionDeserializer")]["end_line"] == 48
    assert by_type[("Field", "pattern")]["start_line"] == 32
    assert by_type[("Field", "pattern")]["end_line"] == 32
    assert by_type[("Constructor", "DayOfExecutionDeserializer")]["start_line"] == 34
    assert by_type[("Constructor", "DayOfExecutionDeserializer")]["end_line"] == 36
    assert by_type[("Method", "deserialize")]["start_line"] == 38
    assert by_type[("Method", "deserialize")]["end_line"] == 43
    assert by_type[("Interface", "ExecutionReader")]["start_line"] == 50
    assert by_type[("Enum", "ExecutionState")]["start_line"] == 52
    assert record.lines >= max(entity["end_line"] for entity in entities)
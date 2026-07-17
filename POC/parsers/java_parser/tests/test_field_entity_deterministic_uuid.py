from java_parser.members.models import JavaField
from java_parser.field_entity_builder import field_to_entity


def test_field_uuid_is_deterministic():
    field = JavaField(
        name="myField",
        type="int",
        modifiers=["private"],
        class_name="TestClass",
        package="com.example",
        file_path="src/main/java/com/example/TestClass.java",
        repository="myrepo",
        module="mymodule",
    )

    document_id = "java_parser:myrepo:src/main/java/com/example/TestClass.java"

    ent1 = field_to_entity(field, document_id)
    ent2 = field_to_entity(field, document_id)

    assert ent1["uuid"] == ent2["uuid"]

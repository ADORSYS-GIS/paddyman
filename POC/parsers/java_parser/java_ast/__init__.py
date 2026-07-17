"""Java AST package — public API."""
from .discovery_bridge import parse_inventory, parse_record
from .extractor import extract_file_ast, parse_and_extract
from .models import (
    JavaDeclarationType,
    JavaFileAst,
    JavaImportDeclaration,
    JavaTypeDeclaration,
    SourceLocation,
)
from .parser import parse_bytes, parse_file

__all__ = [
    # Models
    "JavaDeclarationType",
    "SourceLocation",
    "JavaImportDeclaration",
    "JavaTypeDeclaration",
    "JavaFileAst",
    # Parsing
    "parse_bytes",
    "parse_file",
    # Extraction
    "extract_file_ast",
    "parse_and_extract",
    # Discovery integration
    "parse_record",
    "parse_inventory",
]

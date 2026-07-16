# Java Parser: Missing Package Entities

## Priority

**Medium**

## Goal

Extract Java packages as first-class entities rather than only storing them as metadata.

## Implementation Standards

This ticket must follow [docs/best_practices.md](../best_practices.md), with particular attention to:

- Separation of concerns between parsing, normalization, and graph construction
- Dependency injection for any new builder or extractor collaborators
- Deterministic package extraction and deduplication
- Reuse of the existing Java parser architecture instead of introducing ad hoc helpers
- Documentation updates in the Java parser README
- Tests covering happy paths, edge cases, invalid inputs, empty inputs, deterministic behavior, and error handling

## Current Issue

The Java parser currently captures package information only as metadata within file and class entities:

```json
{
  "source_metadata": {
    "package": "de.adorsys.psd2.aspsp.profile.domain"
  }
}
```

Packages are not extracted as separate `Package` entities with their own IDs and relationships.

This prevents:
- Package-level dependency analysis
- Module boundary visualization
- Package hierarchy navigation
- Cross-package relationship tracking

## Expected Behavior

Every Java package should be extracted as a distinct `Package` entity:

```json
{
  "type": "Package",
  "name": "de.adorsys.psd2.aspsp.profile.domain",
  "source": "java_parser:aspsp-xs2a:aspsp-profile:...",
  "properties": {
    "qualified_name": "de.adorsys.psd2.aspsp.profile.domain",
    "module": "aspsp-profile",
    "repository": "aspsp-xs2a",
    "file_path": "aspsp-profile/aspsp-profile-api/src/main/java/de/adorsys/psd2/aspsp/profile/domain"
  }
}
```

Relationships to create:
- `CONTAINS` from Package to Class/Interface/Enum
- `IMPORTS` from Package to Package (package-level imports)
- `BELONGS_TO` from Package to Module

## Required Implementation

1. Add a dedicated package entity builder in `POC/2_Parsers/java_parser/`
2. Reuse the package declarations already available from the Java AST extraction step
3. Extract unique packages from all parsed Java files in a deterministic order
4. Build `Package` entities with qualified names and preserved repository/module/file metadata
5. Build `CONTAINS` relationships from Package to contained types
6. Build package-level `IMPORTS` relationships where package dependency information is available
7. Wire package entity extraction into the existing Java parser pipeline without changing unrelated entity outputs
8. Keep package extraction isolated to the parser stage; do not move graph construction into parsing logic

## Validation Checklist

- [ ] Every unique Java package appears as a `Package` entity
- [ ] Package entities contain `qualified_name` property
- [ ] `CONTAINS` relationships link packages to their classes/interfaces/enums
- [ ] Package hierarchy is preserved (e.g., `java.util` contains `java.util.concurrent`)
- [ ] Repository and module metadata preserved in package entities
- [ ] No duplicate package entities
- [ ] Package extraction is deterministic across repeated runs
- [ ] Existing class/interface/enum metadata unchanged

## Testing Requirements

1. Unit test: single-file package extraction
2. Unit test: multi-file same-package extraction (no duplicates)
3. Unit test: nested package hierarchy
4. Unit test: package with multiple types (class, interface, enum)
5. Integration test: package entity count matches unique packages in codebase
6. Integration test: verify CONTAINS relationships
7. Unit test: empty or package-less file input
8. Unit test: invalid package metadata handled gracefully
9. Integration test: repeated runs produce stable package entity ordering and counts

## Documentation Updates

Update `POC/2_Parsers/java_parser/README.md`:
- Add Package to entity list
- Document CONTAINS relationship
- Explain package deduplication logic
- Note package hierarchy handling and deterministic extraction order

# Java Parser: Missing Package Entities

## Priority

**Medium**

## Goal

Extract Java packages as first-class entities rather than only storing them as metadata.

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

1. Create `PackageEntityBuilder` in `POC/2_Parsers/java_parser/`
2. Extract unique packages from all parsed Java files
3. Build `Package` entities with qualified names
4. Build `CONTAINS` relationships from Package to contained types
5. Build package-level import relationships
6. Add package entity extraction to main pipeline

## Validation Checklist

- [ ] Every unique Java package appears as a `Package` entity
- [ ] Package entities contain `qualified_name` property
- [ ] `CONTAINS` relationships link packages to their classes/interfaces/enums
- [ ] Package hierarchy is preserved (e.g., `java.util` contains `java.util.concurrent`)
- [ ] Repository and module metadata preserved in package entities
- [ ] No duplicate package entities
- [ ] Existing class/interface/enum metadata unchanged

## Testing Requirements

1. Unit test: single-file package extraction
2. Unit test: multi-file same-package extraction (no duplicates)
3. Unit test: nested package hierarchy
4. Unit test: package with multiple types (class, interface, enum)
5. Integration test: package entity count matches unique packages in codebase
6. Integration test: verify CONTAINS relationships

## Documentation Updates

Update `POC/2_Parsers/java_parser/README.md`:
- Add Package to entity list
- Document CONTAINS relationship
- Explain package deduplication logic

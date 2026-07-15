"""Pipeline summary dataclass and aggregation utilities."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PipelineSummary:
    """Aggregated counts from one or more pipeline runs."""

    repositories: int = 0
    modules: int = 0
    java_files: int = 0
    classes: int = 0
    interfaces: int = 0
    enums: int = 0
    methods: int = 0
    fields: int = 0
    constructors: int = 0
    spring_components: int = 0
    di_relationships: int = 0
    inheritance_relationships: int = 0
    implementation_relationships: int = 0
    call_relationships: int = 0
    errors: int = 0
    # Resource file counts
    resource_files: int = 0
    properties_files: int = 0
    yaml_files: int = 0
    xml_files: int = 0
    pom_files: int = 0
    migration_files: int = 0
    config_keys: int = 0
    maven_dependencies: int = 0


def accumulate(total: PipelineSummary, addition: PipelineSummary) -> None:
    """Add per-file counts from *addition* into *total* in-place."""
    total.java_files += addition.java_files
    total.classes += addition.classes
    total.interfaces += addition.interfaces
    total.enums += addition.enums
    total.methods += addition.methods
    total.fields += addition.fields
    total.constructors += addition.constructors
    total.spring_components += addition.spring_components
    total.di_relationships += addition.di_relationships
    total.inheritance_relationships += addition.inheritance_relationships
    total.implementation_relationships += addition.implementation_relationships
    total.call_relationships += addition.call_relationships
    total.errors += addition.errors
    total.resource_files += addition.resource_files
    total.properties_files += addition.properties_files
    total.yaml_files += addition.yaml_files
    total.xml_files += addition.xml_files
    total.pom_files += addition.pom_files
    total.migration_files += addition.migration_files
    total.config_keys += addition.config_keys
    total.maven_dependencies += addition.maven_dependencies

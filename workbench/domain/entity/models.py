"""Industry-neutral entity definitions and project-owned entity identity."""

from datetime import datetime
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from workbench.domain.value_types import OpaqueId, assert_safe_metadata, freeze_value


ENTITY_DEFINITION_SCHEMA_VERSION = "workbench.entity-definition/1"
ENTITY_RECORD_SCHEMA_VERSION = "workbench.entity/1"
ENTITY_VERSION_SCHEMA_VERSION = "workbench.entity-version/1"
ENTITY_RELATION_SCHEMA_VERSION = "workbench.entity-relation/1"
EntityPropertyType = Literal["text", "number", "boolean", "json", "reference"]
EntityState = Literal["draft", "active", "archived"]


class EntityPropertyDefinition(BaseModel):
    """One named, typed property in a reusable EntitySchema."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    key: OpaqueId
    label: Annotated[str, Field(min_length=1, max_length=500)]
    value_type: EntityPropertyType
    required: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def freeze_metadata(self) -> "EntityPropertyDefinition":
        assert_safe_metadata(self.metadata, path="metadata")
        object.__setattr__(self, "metadata", freeze_value(self.metadata))
        return self


class EntitySchema(BaseModel):
    """Schema for generic entity properties; packages may provide definitions later."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: OpaqueId
    name: Annotated[str, Field(min_length=1, max_length=500)]
    properties: tuple[EntityPropertyDefinition, ...] = ()
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_schema(self) -> "EntitySchema":
        keys = [property_.key for property_ in self.properties]
        if len(keys) != len(set(keys)):
            raise ValueError("entity schema property keys must be unique")
        assert_safe_metadata(self.metadata, path="metadata")
        object.__setattr__(self, "metadata", freeze_value(self.metadata))
        return self


class EntityDefinition(BaseModel):
    """Stable generic entity type identity and its schema."""

    model_config = ConfigDict(frozen=True, extra="forbid", populate_by_name=True, serialize_by_alias=True)

    schema_version: Literal[ENTITY_DEFINITION_SCHEMA_VERSION] = ENTITY_DEFINITION_SCHEMA_VERSION
    id: OpaqueId
    entity_type: OpaqueId
    entity_schema: EntitySchema = Field(alias="schema")
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def freeze_metadata(self) -> "EntityDefinition":
        assert_safe_metadata(self.metadata, path="metadata")
        object.__setattr__(self, "metadata", freeze_value(self.metadata))
        return self

    @property
    def schema(self) -> EntitySchema:
        """Compatibility accessor for the canonical serialized `schema` name."""
        return self.entity_schema


class EntityRecord(BaseModel):
    """Project-owned entity identity; mutable state is versioned by a later card."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal[ENTITY_RECORD_SCHEMA_VERSION] = ENTITY_RECORD_SCHEMA_VERSION
    id: OpaqueId
    entity_type: OpaqueId
    definition_id: OpaqueId
    project_id: OpaqueId
    properties: dict[str, Any] = Field(default_factory=dict)
    state: EntityState = "draft"
    version_ids: tuple[OpaqueId, ...] = ()
    current_version_id: OpaqueId | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def freeze_payload(self) -> "EntityRecord":
        assert_safe_metadata(self.properties, path="properties")
        assert_safe_metadata(self.metadata, path="metadata")
        if len(self.version_ids) != len(set(self.version_ids)):
            raise ValueError("entity version ids must be unique")
        if self.current_version_id is not None and self.current_version_id not in self.version_ids:
            raise ValueError("entity current version must be one of its versions")
        object.__setattr__(self, "properties", freeze_value(self.properties))
        object.__setattr__(self, "metadata", freeze_value(self.metadata))
        return self

    def with_version(self, version_id: str) -> "EntityRecord":
        """Return a new identity projection naming the appended version."""
        if version_id in self.version_ids:
            raise ValueError(f"entity already references version: {version_id}")
        return EntityRecord.model_validate(
            {
                **self.model_dump(mode="python"),
                "version_ids": (*self.version_ids, version_id),
                "current_version_id": version_id,
            }
        )


class EntityVersionPayload(BaseModel):
    """The complete mutable entity state captured by one immutable version."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    properties: dict[str, Any] = Field(default_factory=dict)
    state: EntityState = "draft"
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def freeze_payload(self) -> "EntityVersionPayload":
        assert_safe_metadata(self.properties, path="properties")
        assert_safe_metadata(self.metadata, path="metadata")
        object.__setattr__(self, "properties", freeze_value(self.properties))
        object.__setattr__(self, "metadata", freeze_value(self.metadata))
        return self


class EntityVersionLineage(BaseModel):
    """Explicit ancestry and source references for an entity state snapshot."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    parent_version_id: OpaqueId | None = None
    source_refs: tuple[OpaqueId, ...] = ()
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def freeze_metadata(self) -> "EntityVersionLineage":
        assert_safe_metadata(self.metadata, path="metadata")
        object.__setattr__(self, "metadata", freeze_value(self.metadata))
        return self


class EntityVersionRef(BaseModel):
    """The stable address of one entity snapshot, suitable for typed refs."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    entity_id: OpaqueId
    version_id: OpaqueId


class EntityVersion(BaseModel):
    """One immutable, project-scoped snapshot of an EntityRecord state."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal[ENTITY_VERSION_SCHEMA_VERSION] = ENTITY_VERSION_SCHEMA_VERSION
    id: OpaqueId
    entity_id: OpaqueId
    project_id: OpaqueId
    ordinal: Annotated[int, Field(ge=1)]
    payload: EntityVersionPayload
    author_id: OpaqueId
    created_at: datetime
    lineage: EntityVersionLineage = Field(default_factory=EntityVersionLineage)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def freeze_metadata(self) -> "EntityVersion":
        assert_safe_metadata(self.metadata, path="metadata")
        object.__setattr__(self, "metadata", freeze_value(self.metadata))
        return self

    def ref(self) -> EntityVersionRef:
        return EntityVersionRef(entity_id=self.entity_id, version_id=self.id)


class EntityRelationEndpoint(BaseModel):
    """A typed address for either an Entity or another Workbench resource."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    resource_type: OpaqueId
    resource_id: OpaqueId
    version_id: OpaqueId | None = None


class EntityRelation(BaseModel):
    """A project-scoped business relation, distinct from a Canvas Edge."""

    model_config = ConfigDict(frozen=True, extra="forbid", populate_by_name=True, serialize_by_alias=True)

    schema_version: Literal[ENTITY_RELATION_SCHEMA_VERSION] = ENTITY_RELATION_SCHEMA_VERSION
    id: OpaqueId
    project_id: OpaqueId
    relation_type: OpaqueId
    from_endpoint: EntityRelationEndpoint = Field(alias="from")
    to_endpoint: EntityRelationEndpoint = Field(alias="to")
    revision: Annotated[int, Field(ge=1)] = 1
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_relation(self) -> "EntityRelation":
        if self.from_endpoint == self.to_endpoint:
            raise ValueError("entity relation endpoints must be distinct")
        assert_safe_metadata(self.metadata, path="metadata")
        object.__setattr__(self, "metadata", freeze_value(self.metadata))
        return self


def validate_entity_properties(schema: EntitySchema, properties: dict[str, Any]) -> None:
    """Validate property keys and requiredness against a generic EntitySchema."""

    definitions = {property_.key: property_ for property_ in schema.properties}
    unknown = sorted(set(properties) - definitions.keys())
    if unknown:
        raise ValueError(f"entity has unknown properties: {', '.join(unknown)}")
    missing = [key for key, definition in definitions.items() if definition.required and key not in properties]
    if missing:
        raise ValueError(f"entity is missing required properties: {', '.join(missing)}")
    assert_safe_metadata(properties, path="properties")

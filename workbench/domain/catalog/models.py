"""Generic, industry-neutral catalog records and item versions."""

from datetime import datetime
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from workbench.domain.value_types import OpaqueId, assert_safe_metadata, freeze_value


CATALOG_SCHEMA_VERSION = "workbench.catalog/1"
CatalogScope = Literal["workspace", "project"]
CatalogAttributeType = Literal["text", "number", "boolean", "json", "reference"]
CatalogMediaKind = Literal["asset_version", "artifact_version"]


class CatalogAttributeDefinition(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", populate_by_name=True, serialize_by_alias=True)

    key: OpaqueId
    label: Annotated[str, Field(min_length=1, max_length=500)]
    value_type: CatalogAttributeType
    required: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_metadata(self) -> "CatalogAttributeDefinition":
        assert_safe_metadata(self.metadata, path="metadata")
        object.__setattr__(self, "metadata", freeze_value(self.metadata))
        return self


class CatalogSchema(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: OpaqueId
    name: Annotated[str, Field(min_length=1, max_length=500)]
    attributes: list[CatalogAttributeDefinition] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def require_unique_attribute_keys(self) -> "CatalogSchema":
        keys = [attribute.key for attribute in self.attributes]
        if len(keys) != len(set(keys)):
            raise ValueError("catalog schema attribute keys must be unique")
        assert_safe_metadata(self.metadata, path="metadata")
        object.__setattr__(self, "metadata", freeze_value(self.metadata))
        return self


class CatalogMediaRef(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    kind: CatalogMediaKind
    ref_id: OpaqueId
    role: Annotated[str, Field(min_length=1, max_length=100)] = "default"
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_metadata(self) -> "CatalogMediaRef":
        assert_safe_metadata(self.metadata, path="metadata")
        object.__setattr__(self, "metadata", freeze_value(self.metadata))
        return self


class Catalog(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", populate_by_name=True, serialize_by_alias=True)

    schema_version: Literal[CATALOG_SCHEMA_VERSION] = CATALOG_SCHEMA_VERSION
    id: OpaqueId
    workspace_id: OpaqueId
    project_id: OpaqueId | None = None
    scope: CatalogScope
    name: Annotated[str, Field(min_length=1, max_length=500)]
    catalog_schema: CatalogSchema = Field(alias="schema")
    item_ids: tuple[OpaqueId, ...] = ()
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_scope(self) -> "Catalog":
        if self.scope == "project" and self.project_id is None:
            raise ValueError("project catalogs require project_id")
        if self.scope == "workspace" and self.project_id is not None:
            raise ValueError("workspace catalogs cannot set project_id")
        if len(self.item_ids) != len(set(self.item_ids)):
            raise ValueError("catalog item ids must be unique")
        assert_safe_metadata(self.metadata, path="metadata")
        object.__setattr__(self, "metadata", freeze_value(self.metadata))
        return self

    def with_item(self, item_id: str) -> "Catalog":
        if item_id in self.item_ids:
            raise ValueError(f"catalog already references item: {item_id}")
        return self.model_copy(update={"item_ids": (*self.item_ids, item_id)})


class CatalogItem(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: OpaqueId
    catalog_id: OpaqueId
    title: Annotated[str, Field(min_length=1, max_length=500)]
    version_ids: tuple[OpaqueId, ...] = ()
    current_version_id: OpaqueId | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_item(self) -> "CatalogItem":
        if len(self.version_ids) != len(set(self.version_ids)):
            raise ValueError("catalog item version ids must be unique")
        if self.current_version_id is not None and self.current_version_id not in self.version_ids:
            raise ValueError("catalog item current version must be one of its versions")
        if self.current_version_id is None and self.version_ids:
            object.__setattr__(self, "current_version_id", self.version_ids[-1])
        assert_safe_metadata(self.metadata, path="metadata")
        object.__setattr__(self, "metadata", freeze_value(self.metadata))
        return self

    def with_version(self, version_id: str) -> "CatalogItem":
        if version_id in self.version_ids:
            raise ValueError(f"catalog item already references version: {version_id}")
        return self.model_copy(update={"version_ids": (*self.version_ids, version_id), "current_version_id": version_id})


class CatalogItemVersion(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: OpaqueId
    catalog_id: OpaqueId
    item_id: OpaqueId
    ordinal: Annotated[int, Field(ge=1)]
    attributes: dict[str, Any] = Field(default_factory=dict)
    media_refs: tuple[CatalogMediaRef, ...] = ()
    created_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def freeze_payload(self) -> "CatalogItemVersion":
        assert_safe_metadata(self.attributes, path="attributes")
        assert_safe_metadata(self.metadata, path="metadata")
        object.__setattr__(self, "attributes", freeze_value(self.attributes))
        object.__setattr__(self, "metadata", freeze_value(self.metadata))
        return self


def validate_item_attributes(schema: CatalogSchema, attributes: dict[str, Any]) -> None:
    definitions = {attribute.key: attribute for attribute in schema.attributes}
    unknown = sorted(set(attributes) - definitions.keys())
    if unknown:
        raise ValueError(f"catalog item has unknown attributes: {', '.join(unknown)}")
    missing = [key for key, definition in definitions.items() if definition.required and key not in attributes]
    if missing:
        raise ValueError(f"catalog item is missing required attributes: {', '.join(missing)}")

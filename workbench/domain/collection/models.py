"""Industry-neutral structured multi-item domain records."""

from typing import Annotated, Any, Literal, TypeAlias, Union

from pydantic import BaseModel, ConfigDict, Field, model_validator


COLLECTION_SCHEMA_VERSION = "workbench.collection/1"
OpaqueId = Annotated[str, Field(min_length=1, max_length=255)]
CollectionValueType = Literal[
    "asset_version",
    "artifact_version",
    "entity_ref",
    "entity_version",
    "collection",
    "literal",
]
CollectionReferenceType = Literal[
    "asset_version",
    "artifact_version",
    "entity_ref",
    "entity_version",
    "collection",
]


class CollectionColumn(BaseModel):
    """A named, typed value column in a CollectionSchema."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: OpaqueId
    key: OpaqueId
    label: Annotated[str, Field(min_length=1, max_length=500)]
    value_type: CollectionValueType
    required: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class CollectionSchema(BaseModel):
    """The reusable column contract for Collection items."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: OpaqueId
    name: Annotated[str, Field(min_length=1, max_length=500)]
    columns: list[CollectionColumn] = Field(default_factory=list)
    version: Annotated[int, Field(ge=1)] = 1
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def require_unique_columns(self):
        column_ids = [column.id for column in self.columns]
        column_keys = [column.key for column in self.columns]
        if len(column_ids) != len(set(column_ids)):
            raise ValueError("collection schema column ids must be unique")
        if len(column_keys) != len(set(column_keys)):
            raise ValueError("collection schema column keys must be unique")
        return self


class CollectionLiteralCell(BaseModel):
    """A literal value cell, kept distinct from typed resource references."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    type: Literal["literal"] = "literal"
    value: Any


class CollectionReferenceCell(BaseModel):
    """A cell referring to a typed Workbench resource or Collection."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    type: Literal["reference"] = "reference"
    reference_type: CollectionReferenceType
    reference_id: OpaqueId
    metadata: dict[str, Any] = Field(default_factory=dict)


CollectionCell: TypeAlias = Annotated[
    Union[CollectionLiteralCell, CollectionReferenceCell],
    Field(discriminator="type"),
]


class CollectionItem(BaseModel):
    """One ordered row of values; it has no Canvas Group membership fields."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: OpaqueId
    order: Annotated[int, Field(ge=0)]
    values: dict[str, CollectionCell] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Collection(BaseModel):
    """A generic structured multi-item resource independent from Canvas Group."""

    model_config = ConfigDict(frozen=True, extra="forbid", populate_by_name=True, serialize_by_alias=True)

    schema_version: Literal[COLLECTION_SCHEMA_VERSION] = COLLECTION_SCHEMA_VERSION
    id: OpaqueId
    project_id: OpaqueId
    name: Annotated[str, Field(min_length=1, max_length=500)]
    collection_schema: CollectionSchema = Field(alias="schema")
    items: list[CollectionItem] = Field(default_factory=list)
    default_view: dict[str, Any] = Field(default_factory=dict)
    revision: Annotated[int, Field(ge=1)] = 1
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_items_against_schema(self):
        columns = {column.key: column for column in self.collection_schema.columns}
        item_ids = [item.id for item in self.items]
        item_orders = [item.order for item in self.items]
        if len(item_ids) != len(set(item_ids)):
            raise ValueError("collection item ids must be unique")
        if len(item_orders) != len(set(item_orders)):
            raise ValueError("collection item order values must be unique")
        for item in self.items:
            for key, cell in item.values.items():
                column = columns.get(key)
                if column is None:
                    raise ValueError(f"collection item references unknown column: {key}")
                if column.value_type == "literal":
                    if not isinstance(cell, CollectionLiteralCell):
                        raise ValueError(f"column {key} accepts literal cells only")
                elif not isinstance(cell, CollectionReferenceCell) or cell.reference_type != column.value_type:
                    raise ValueError(f"column {key} requires a {column.value_type} reference cell")
            missing = [column.key for column in self.collection_schema.columns if column.required and column.key not in item.values]
            if missing:
                raise ValueError(f"collection item is missing required columns: {', '.join(missing)}")
        return self

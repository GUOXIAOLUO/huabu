"""Pydantic value records for the versioned Canvas kernel."""

from datetime import datetime
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .input_bindings import InputBindingValue
from .ports import PortSet
from .states import NodeState


NODE_SCHEMA_VERSION = "workbench.node/1"
EDGE_SCHEMA_VERSION = "workbench.edge/1"
NodeKind = Literal["asset", "skill", "artifact", "entity", "task", "approval", "group", "collection", "composite", "legacy"]


OpaqueId = Annotated[str, Field(min_length=1, max_length=255)]


class DefinitionRef(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    type: Annotated[str, Field(min_length=1, max_length=120)]
    id: OpaqueId
    version: Annotated[str, Field(min_length=1, max_length=120)]


class RendererRef(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: OpaqueId
    version: Annotated[str, Field(min_length=1, max_length=120)]


class Position(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    x: float
    y: float


class Size(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    width: Annotated[float, Field(gt=0)]
    height: Annotated[float, Field(gt=0)]


class ArtifactOrAssetVersionRef(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    type: Literal["asset_version", "artifact_version"]
    id: OpaqueId


class ModelBinding(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    selection_mode: Literal["user", "skill_default", "system_default"]
    provider_id: OpaqueId | None = None
    model_id: OpaqueId | None = None
    parameters: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def provider_and_model_are_paired(self):
        if bool(self.provider_id) != bool(self.model_id):
            raise ValueError("provider_id and model_id must be set together")
        return self


class NodeRecord(BaseModel):
    """Canonical node view. Provider and business details stay in definitions or extensions."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal[NODE_SCHEMA_VERSION] = NODE_SCHEMA_VERSION
    id: OpaqueId
    project_id: OpaqueId
    canvas_id: OpaqueId
    kind: NodeKind
    definition_ref: DefinitionRef
    renderer: RendererRef
    state: NodeState
    title: Annotated[str, Field(min_length=1, max_length=500)]
    position: Position
    size: Size
    ports: PortSet = Field(default_factory=PortSet)
    input_bindings: list[InputBindingValue] = Field(default_factory=list)
    output_refs: list[ArtifactOrAssetVersionRef] = Field(default_factory=list)
    model_binding: ModelBinding | None = None
    config: dict[str, Any] = Field(default_factory=dict)
    provenance_ref: OpaqueId | None = None
    created_by: OpaqueId
    created_at: datetime
    updated_at: datetime
    revision: Annotated[int, Field(ge=1)] = 1
    metadata: dict[str, Any] = Field(default_factory=dict)
    extensions: dict[str, Any] = Field(default_factory=dict)


class EdgeEndpoint(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    node_id: OpaqueId
    port_id: OpaqueId


class EdgeRecord(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal[EDGE_SCHEMA_VERSION] = EDGE_SCHEMA_VERSION
    id: OpaqueId
    canvas_id: OpaqueId
    from_: EdgeEndpoint = Field(alias="from")
    to: EdgeEndpoint
    state: Literal["active", "disabled"] = "active"
    metadata: dict[str, Any] = Field(default_factory=dict)
    revision: Annotated[int, Field(ge=1)] = 1

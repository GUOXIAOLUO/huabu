"""Immutable, provenance-preserving project knowledge context projections."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from workbench.domain.entity import EntityRecord
from workbench.domain.knowledge.entry import KnowledgeEntry
from workbench.domain.knowledge.models import KnowledgeSourceScope
from workbench.domain.value_types import OpaqueId, assert_safe_metadata, freeze_value


PROJECT_KNOWLEDGE_CONTEXT_SCHEMA_VERSION = "workbench.project-knowledge-context/1"
KNOWLEDGE_SNAPSHOT_SCHEMA_VERSION = "workbench.knowledge-snapshot/1"
ContextResourceType = Literal["asset", "artifact", "catalog"]


class ProjectKnowledgeContextPolicy(BaseModel):
    """Explicit inclusion policy; absence of a scope never widens the context."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    knowledge_scopes: tuple[KnowledgeSourceScope, ...] = ("project",)
    resource_scopes: tuple[OpaqueId, ...] = ("project",)
    include_entities: bool = True
    include_resources: bool = True
    max_entities: int = Field(default=100, ge=0, le=1_000)
    max_knowledge: int = Field(default=100, ge=0, le=1_000)
    max_resources: int = Field(default=100, ge=0, le=1_000)

    @model_validator(mode="after")
    def validate_scopes(self) -> "ProjectKnowledgeContextPolicy":
        if len(self.knowledge_scopes) != len(set(self.knowledge_scopes)):
            raise ValueError("knowledge context scopes must be unique")
        if len(self.resource_scopes) != len(set(self.resource_scopes)):
            raise ValueError("knowledge context resource scopes must be unique")
        return self


class ProjectKnowledgeContextResource(BaseModel):
    """A typed resource identity included by a canonical resource reader."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    resource_type: ContextResourceType
    resource_id: OpaqueId
    version_id: OpaqueId | None = None
    scope: OpaqueId
    provenance: tuple[OpaqueId, ...] = ()


class ProjectKnowledgeContextSnapshotRef(BaseModel):
    """Stable ref captured for future execution context assembly."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    kind: Literal["entity", "knowledge", "resource"]
    ref_id: OpaqueId
    version_id: OpaqueId | None = None
    scope: OpaqueId
    provenance: tuple[OpaqueId, ...] = ()


class ProjectKnowledgeContext(BaseModel):
    """Inspectable context; it contains references, not an implicit file dump."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal[PROJECT_KNOWLEDGE_CONTEXT_SCHEMA_VERSION] = PROJECT_KNOWLEDGE_CONTEXT_SCHEMA_VERSION
    project_id: OpaqueId
    policy: ProjectKnowledgeContextPolicy
    generated_at: datetime
    entities: tuple[EntityRecord, ...] = ()
    knowledge: tuple[KnowledgeEntry, ...] = ()
    resources: tuple[ProjectKnowledgeContextResource, ...] = ()
    snapshot_refs: tuple[ProjectKnowledgeContextSnapshotRef, ...] = ()
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def freeze_context(self) -> "ProjectKnowledgeContext":
        assert_safe_metadata(self.metadata, path="metadata")
        object.__setattr__(self, "metadata", freeze_value(self.metadata))
        return self


class KnowledgeSnapshot(ProjectKnowledgeContext):
    """Formal immutable snapshot captured by an execution run."""

    schema_version: Literal[KNOWLEDGE_SNAPSHOT_SCHEMA_VERSION] = KNOWLEDGE_SNAPSHOT_SCHEMA_VERSION
    snapshot_id: OpaqueId
    captured_at: datetime

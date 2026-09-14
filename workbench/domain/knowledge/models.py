"""Generic, project-neutral sources from which Knowledge may be derived."""

from datetime import datetime
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from workbench.domain.value_types import OpaqueId, assert_safe_metadata, freeze_value


KNOWLEDGE_SOURCE_SCHEMA_VERSION = "workbench.knowledge-source/1"
KnowledgeSourceType = Literal["asset", "document", "manual"]
KnowledgeSourceScope = Literal["system", "common", "industry", "company", "workspace", "project", "user"]
KnowledgeSourceStatus = Literal["draft", "active", "archived"]
KnowledgeSourceOrigin = Literal["user", "import", "package", "integration"]


class KnowledgeSourceProvenance(BaseModel):
    """Who and what established a source record, without carrying secrets."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    origin: KnowledgeSourceOrigin
    actor_id: OpaqueId | None = None
    source_ref: OpaqueId | None = None
    captured_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def freeze_metadata(self) -> "KnowledgeSourceProvenance":
        assert_safe_metadata(self.metadata, path="metadata")
        object.__setattr__(self, "metadata", freeze_value(self.metadata))
        return self


class KnowledgeSource(BaseModel):
    """A lifecycle-managed address of material usable by Knowledge runtime."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal[KNOWLEDGE_SOURCE_SCHEMA_VERSION] = KNOWLEDGE_SOURCE_SCHEMA_VERSION
    id: OpaqueId
    source_type: KnowledgeSourceType
    source_ref: OpaqueId | None = None
    scope: KnowledgeSourceScope = "project"
    project_id: OpaqueId | None = None
    workspace_id: OpaqueId | None = None
    status: KnowledgeSourceStatus = "draft"
    provenance: KnowledgeSourceProvenance
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_scope_and_reference(self) -> "KnowledgeSource":
        if self.scope == "project" and self.project_id is None:
            raise ValueError("project knowledge sources require project_id")
        if self.scope in {"company", "workspace"} and self.workspace_id is None:
            raise ValueError(f"{self.scope} knowledge sources require workspace_id")
        if self.scope != "project" and self.project_id is not None:
            raise ValueError("only project knowledge sources may set project_id")
        if self.scope not in {"company", "workspace"} and self.workspace_id is not None:
            raise ValueError("only company or workspace knowledge sources may set workspace_id")
        if self.source_type in {"asset", "document"} and self.source_ref is None:
            raise ValueError(f"{self.source_type} knowledge sources require source_ref")
        assert_safe_metadata(self.metadata, path="metadata")
        object.__setattr__(self, "metadata", freeze_value(self.metadata))
        return self

    def activate(self) -> "KnowledgeSource":
        """Return the same source identity in the active lifecycle state."""
        if self.status == "archived":
            raise ValueError("archived knowledge sources cannot be activated")
        return self.model_copy(update={"status": "active"})

    def archive(self) -> "KnowledgeSource":
        """Return the source in its terminal archived state."""
        return self.model_copy(update={"status": "archived"})

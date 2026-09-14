"""Normalized, source-backed knowledge entries."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from workbench.domain.knowledge.models import KnowledgeSourceScope
from workbench.domain.value_types import OpaqueId, assert_safe_metadata, freeze_value


KNOWLEDGE_ENTRY_SCHEMA_VERSION = "workbench.knowledge-entry/1"


class KnowledgeEntry(BaseModel):
    """A reusable fact or note that always retains one or more source ids."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal[KNOWLEDGE_ENTRY_SCHEMA_VERSION] = KNOWLEDGE_ENTRY_SCHEMA_VERSION
    id: OpaqueId
    project_id: OpaqueId
    content: str | None = Field(default=None, max_length=100_000)
    structured_payload: dict[str, Any] | None = None
    source_refs: tuple[OpaqueId, ...] = Field(min_length=1)
    tags: tuple[OpaqueId, ...] = ()
    scope: KnowledgeSourceScope = "project"
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_entry(self) -> "KnowledgeEntry":
        if not (self.content and self.content.strip()) and not self.structured_payload:
            raise ValueError("knowledge entries require content or structured_payload")
        if len(self.source_refs) != len(set(self.source_refs)):
            raise ValueError("knowledge entry source_refs must be unique")
        if len(self.tags) != len(set(self.tags)):
            raise ValueError("knowledge entry tags must be unique")
        if self.structured_payload is not None:
            assert_safe_metadata(self.structured_payload, path="structured_payload")
            object.__setattr__(self, "structured_payload", freeze_value(self.structured_payload))
        assert_safe_metadata(self.metadata, path="metadata")
        object.__setattr__(self, "metadata", freeze_value(self.metadata))
        return self

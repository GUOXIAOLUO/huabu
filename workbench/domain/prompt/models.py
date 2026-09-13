"""First-class, project-owned Prompt and immutable PromptVersion records."""

from datetime import datetime
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field


PROMPT_SCHEMA_VERSION = "workbench.prompt/1"
PROMPT_VERSION_SCHEMA_VERSION = "workbench.prompt-version/1"
RESOLVED_PROMPT_SCHEMA_VERSION = "workbench.resolved-prompt/1"
OpaqueId = Annotated[str, Field(min_length=1, max_length=255)]
PromptLayerName = Literal["default", "project", "task", "runtime"]


class PromptRef(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    prompt_id: OpaqueId
    version: Annotated[int, Field(ge=1)]


class PromptDefinition(BaseModel):
    """Stable Prompt identity; content lives in immutable versions."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal[PROMPT_SCHEMA_VERSION] = PROMPT_SCHEMA_VERSION
    id: OpaqueId
    project_id: OpaqueId
    name: Annotated[str, Field(min_length=1, max_length=500)]
    description: str = ""
    current_version: Annotated[int, Field(ge=1)] = 1
    metadata: dict[str, Any] = Field(default_factory=dict)


class PromptVersion(BaseModel):
    """Immutable Prompt content addressed by PromptDefinition id and version."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal[PROMPT_VERSION_SCHEMA_VERSION] = PROMPT_VERSION_SCHEMA_VERSION
    prompt_id: OpaqueId
    version: Annotated[int, Field(ge=1)]
    content: Annotated[str, Field(min_length=1, max_length=100_000)]
    created_by: OpaqueId
    created_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)


class PromptLayer(BaseModel):
    """One complete prompt candidate from a resolution layer."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    layer: PromptLayerName
    prompt: PromptRef | None = None
    content: Annotated[str, Field(min_length=1, max_length=100_000)]
    metadata: dict[str, Any] = Field(default_factory=dict)


class ResolvedPrompt(BaseModel):
    """Immutable execution-ready snapshot produced by PromptResolver."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal[RESOLVED_PROMPT_SCHEMA_VERSION] = RESOLVED_PROMPT_SCHEMA_VERSION
    prompt: PromptRef | None = None
    content: Annotated[str, Field(min_length=1, max_length=100_000)]
    source: PromptLayerName
    metadata: dict[str, Any] = Field(default_factory=dict)

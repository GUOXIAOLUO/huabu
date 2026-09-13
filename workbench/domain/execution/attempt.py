"""Immutable per-item execution attempt records."""

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from workbench.domain.value_types import OpaqueId, assert_safe_metadata, freeze_value


EXECUTION_ATTEMPT_SCHEMA_VERSION = "workbench.execution-attempt/1"
ExecutionAttemptStatus = Literal["prepared", "running", "succeeded", "failed", "cancelled"]


class ExecutionAttempt(BaseModel):
    """One deterministic attempt for one frozen run input item."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal[EXECUTION_ATTEMPT_SCHEMA_VERSION] = EXECUTION_ATTEMPT_SCHEMA_VERSION
    id: OpaqueId
    run_id: OpaqueId
    input_id: OpaqueId
    item_index: Annotated[int, Field(ge=0)]
    attempt_number: Annotated[int, Field(ge=1)]
    created_at: datetime
    status: ExecutionAttemptStatus = "prepared"
    retry_count: Annotated[int, Field(ge=0)] = 0
    error: str | None = None
    output_refs: tuple[OpaqueId, ...] = ()
    started_at: datetime | None = None
    finished_at: datetime | None = None
    summary: dict[str, object] = Field(default_factory=dict)
    revision: Annotated[int, Field(ge=1)] = 1

    @model_validator(mode="after")
    def validate_summary(self):
        assert_safe_metadata(self.summary, path="summary")
        object.__setattr__(self, "summary", freeze_value(self.summary))
        return self

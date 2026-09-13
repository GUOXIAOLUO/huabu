"""Immutable top-level execution run records."""

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from workbench.domain.execution.input_projection import ExecutionInputProjection
from workbench.domain.execution.policy import ExecutionPolicy
from workbench.domain.value_types import OpaqueId, assert_safe_metadata, freeze_value


EXECUTION_RUN_SCHEMA_VERSION = "workbench.execution-run/1"
ExecutionRunStatus = Literal["prepared", "queued", "running", "succeeded", "failed", "cancelled"]
EXECUTION_RUN_TRANSITIONS: dict[str, frozenset[str]] = {
    "prepared": frozenset({"queued", "running", "succeeded", "failed", "cancelled"}),
    "queued": frozenset({"running", "succeeded", "failed", "cancelled"}),
    "running": frozenset({"succeeded", "failed", "cancelled"}),
    "succeeded": frozenset(), "failed": frozenset(), "cancelled": frozenset(),
}


class ExecutionRun(BaseModel):
    """Durable run identity plus immutable input/policy snapshots."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal[EXECUTION_RUN_SCHEMA_VERSION] = EXECUTION_RUN_SCHEMA_VERSION
    id: OpaqueId
    project_id: OpaqueId
    task_id: OpaqueId
    execution_profile_ref: OpaqueId
    policy: ExecutionPolicy
    input_projection: ExecutionInputProjection
    status: ExecutionRunStatus = "prepared"
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    summary: dict[str, object] = Field(default_factory=dict)
    revision: Annotated[int, Field(ge=1)] = 1

    @model_validator(mode="after")
    def validate_summary(self):
        assert_safe_metadata(self.summary, path="summary")
        object.__setattr__(self, "summary", freeze_value(self.summary))
        return self

    def can_transition_to(self, status: ExecutionRunStatus) -> bool:
        return status == self.status or status in EXECUTION_RUN_TRANSITIONS[self.status]

"""Immutable normalized execution events owned by Workbench persistence."""

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from workbench.domain.value_types import OpaqueId, assert_safe_metadata, freeze_value


EXECUTION_EVENT_SCHEMA_VERSION = "workbench.execution-event/1"
ExecutionEventType = Literal["queued", "started", "progress", "partial_result", "completed", "failed", "cancelled"]


class ExecutionEventRecord(BaseModel):
    """A durable, normalized observation of one execution run."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal[EXECUTION_EVENT_SCHEMA_VERSION] = EXECUTION_EVENT_SCHEMA_VERSION
    id: OpaqueId
    run_id: OpaqueId
    attempt_id: OpaqueId | None = None
    sequence: Annotated[int, Field(ge=1)]
    event_type: ExecutionEventType
    payload: dict[str, object] = Field(default_factory=dict)
    occurred_at: datetime

    @model_validator(mode="after")
    def validate_payload(self):
        assert_safe_metadata(self.payload, path="payload")
        object.__setattr__(self, "payload", freeze_value(self.payload))
        return self

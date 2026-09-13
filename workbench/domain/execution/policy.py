"""Provider-neutral execution scheduling policy."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


EXECUTION_POLICY_SCHEMA_VERSION = "workbench.execution-policy/1"
ExecutionMode = Literal["single", "batch", "map"]
ExecutionOrder = Literal["input", "completion"]


class ExecutionPolicy(BaseModel):
    """Explicit scheduling controls, separate from Collection data semantics."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal[EXECUTION_POLICY_SCHEMA_VERSION] = EXECUTION_POLICY_SCHEMA_VERSION
    mode: ExecutionMode = "single"
    concurrency: Annotated[int, Field(ge=1)] = 1
    start_index: Annotated[int, Field(ge=0)] = 0
    limit: Annotated[int, Field(ge=1)] | None = None
    retry: Annotated[int, Field(ge=0)] = 0
    timeout: Annotated[float, Field(gt=0)] = 300.0
    order: ExecutionOrder = "input"
    continue_on_error: bool = False

    @model_validator(mode="after")
    def validate_mode_constraints(self):
        if self.mode == "single" and self.concurrency != 1:
            raise ValueError("single execution policy requires concurrency=1")
        return self

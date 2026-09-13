"""Immutable execution branch lineage records.

A regeneration never overwrites the run it came from: it creates a new run and a
record of where that run came from. This record is that lineage.

Two boundaries are deliberate. A run has at most one origin, so the lineage of a
run is a single parent rather than a graph — a branch is a decision about which
snapshot to reuse, not a merge. And a branch may name the exact result it was
branched from, using the same three-part identity the Result Tray stages and
Result Selection rates, so lineage can point at one candidate rather than at a
whole run; naming a result means naming all three parts or none of them.
"""

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from workbench.domain.execution.policy import ExecutionPolicy
from workbench.domain.value_types import OpaqueId, assert_safe_metadata, freeze_value


EXECUTION_BRANCH_SCHEMA_VERSION = "workbench.execution-branch/1"
ExecutionBranchKind = Literal["regenerate"]


class ExecutionBranch(BaseModel):
    """Where one run came from: its source run, and optionally its source result."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal[EXECUTION_BRANCH_SCHEMA_VERSION] = EXECUTION_BRANCH_SCHEMA_VERSION
    id: OpaqueId
    project_id: OpaqueId
    run_id: OpaqueId
    source_run_id: OpaqueId
    source_attempt_id: OpaqueId | None = None
    source_output_name: Annotated[str, Field(min_length=1, max_length=255)] | None = None
    source_ordinal: Annotated[int, Field(ge=0)] | None = None
    policy_override: ExecutionPolicy | None = None
    kind: ExecutionBranchKind = "regenerate"
    created_at: datetime
    metadata: dict[str, object] = Field(default_factory=dict)
    revision: Annotated[int, Field(ge=1)] = 1

    @model_validator(mode="after")
    def validate_metadata(self):
        assert_safe_metadata(self.metadata, path="metadata")
        object.__setattr__(self, "metadata", freeze_value(self.metadata))
        return self

    @model_validator(mode="after")
    def validate_source(self):
        # A regeneration is always a new run: it may never point at itself.
        if self.run_id == self.source_run_id:
            raise ValueError("a branch cannot descend from itself")
        # A result is named by all three parts or by none of them.
        named = [self.source_attempt_id, self.source_output_name, self.source_ordinal]
        if any(part is not None for part in named) and not all(part is not None for part in named):
            raise ValueError("a branch that names a result must name its attempt, output and ordinal")
        return self

    def has_result_lineage(self) -> bool:
        """True when the branch descends from one result, not just from a run."""
        return self.source_attempt_id is not None

    def result_identity(self) -> tuple[str, str, int] | None:
        """The three-part source result identity, or None for a whole-run branch."""
        if not self.has_result_lineage():
            return None
        return (self.source_attempt_id, self.source_output_name, self.source_ordinal)

"""The address of one produced result, usable as a reference from anywhere.

A result is finer than the attempt that produced it: one attempt emits a named
output, and that output may occur more than once in a batch. Four parts are
therefore needed to name one result, and all four are required — an address
missing any part points at a different result, or at none.

This record is deliberately only an address. It carries no rating, no selection,
no approval and no storage location, so it can be embedded wherever something
needs to say *which* result it came from without dragging what the user thought
of it along.
"""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

from workbench.domain.value_types import OpaqueId


EXECUTION_RESULT_IDENTITY_SCHEMA_VERSION = "workbench.result-identity/1"


class ExecutionResultIdentity(BaseModel):
    """Four-part address of one result of one attempt."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal[EXECUTION_RESULT_IDENTITY_SCHEMA_VERSION] = EXECUTION_RESULT_IDENTITY_SCHEMA_VERSION
    run_id: OpaqueId
    attempt_id: OpaqueId
    output_name: Annotated[str, Field(min_length=1, max_length=255)]
    ordinal: Annotated[int, Field(ge=0)]

    def label(self) -> str:
        """Stable human-readable name of the one result this addresses."""
        return f"{self.output_name}#{self.ordinal}"

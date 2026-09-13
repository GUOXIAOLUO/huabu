"""Runtime-neutral executor port and its typed lifecycle envelopes.

An executor is an implementation capability.  It does not select or own a
model, provider connection, or execution profile; callers resolve those
separate concepts before constructing an :class:`ExecutionRequest`.
"""

from collections.abc import AsyncIterator
from typing import Any, Literal, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field, model_validator

from workbench.domain.value_types import OpaqueId, assert_safe_metadata


EXECUTOR_CONTRACT_VERSION = "workbench.executor-contract/1"

ExecutionStatus = Literal["prepared", "queued", "running", "succeeded", "failed", "cancelled"]
ExecutorHealthStatus = Literal["healthy", "degraded", "unavailable", "unknown"]
ExecutionEventKind = Literal["started", "progress", "partial_result", "completed", "failed", "cancelled"]


class _ContractModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class ExecutionInput(_ContractModel):
    """One named input supplied to an executor."""

    name: str = Field(min_length=1, max_length=255)
    value: Any


class ExecutionOutput(_ContractModel):
    """One named output emitted by an executor."""

    name: str = Field(min_length=1, max_length=255)
    value: Any


class ExecutionRequest(_ContractModel):
    """Immutable request shared by every executor implementation.

    ``idempotency_key`` is stable across safe retries.  The optional refs are
    provenance references only; they do not turn Executor into an owner of
    ModelAvailability or ExecutionProfile.
    """

    contract_version: Literal[EXECUTOR_CONTRACT_VERSION] = EXECUTOR_CONTRACT_VERSION
    execution_id: OpaqueId
    idempotency_key: OpaqueId
    inputs: tuple[ExecutionInput, ...] = ()
    config: dict[str, Any] = Field(default_factory=dict)
    model_availability_ref: OpaqueId | None = None
    execution_profile_ref: OpaqueId | None = None

    @model_validator(mode="after")
    def validate_request(self):
        names = [item.name for item in self.inputs]
        if len(names) != len(set(names)):
            raise ValueError("execution input names must be unique")
        assert_safe_metadata(self.config, path="config")
        return self


class PreparedExecution(_ContractModel):
    """Executor-owned preparation token returned before starting work."""

    execution_id: OpaqueId
    status: Literal["prepared"] = "prepared"
    executor_ref: OpaqueId
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_metadata(self):
        assert_safe_metadata(self.metadata)
        return self


class ExecutionHandle(_ContractModel):
    """Stable handle used by all subsequent lifecycle operations."""

    execution_id: OpaqueId
    executor_ref: OpaqueId


class ExecutionEvent(_ContractModel):
    """Typed stream envelope; partial results are never confused with final output."""

    execution_id: OpaqueId
    sequence: int = Field(ge=0)
    kind: ExecutionEventKind
    status: ExecutionStatus
    outputs: tuple[ExecutionOutput, ...] = ()
    message: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_event(self):
        assert_safe_metadata(self.metadata)
        return self


class ExecutionResult(_ContractModel):
    """Terminal result envelope, including partial outputs and failure detail."""

    execution_id: OpaqueId
    status: Literal["succeeded", "failed", "cancelled"]
    outputs: tuple[ExecutionOutput, ...] = ()
    error: str | None = None
    usage: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_result(self):
        if self.status == "failed" and not self.error:
            raise ValueError("failed execution results require an error")
        if self.status != "failed" and self.error is not None:
            raise ValueError("only failed execution results may contain an error")
        assert_safe_metadata(self.usage, path="usage")
        return self


class ExecutionStatusSnapshot(_ContractModel):
    """Point-in-time lifecycle status returned by ``status``."""

    execution_id: OpaqueId
    status: ExecutionStatus
    message: str | None = None


class CancelResult(_ContractModel):
    """Idempotent cancellation acknowledgement."""

    execution_id: OpaqueId
    accepted: bool
    status: Literal["cancelled", "succeeded", "failed", "unknown"]


class ExecutorHealth(_ContractModel):
    """Operational health, separate from execution status."""

    executor_ref: OpaqueId
    status: ExecutorHealthStatus
    message: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_metadata(self):
        assert_safe_metadata(self.metadata)
        return self


@runtime_checkable
class Executor(Protocol):
    """The normalized lifecycle port implemented by every executor adapter.

    ``cancel`` must be safe to repeat, and ``idempotency_key`` on a request
    must identify the same logical execution across retries.  Implementations
    may reject unsupported cancellation explicitly through ``CancelResult``.
    """

    executor_ref: OpaqueId

    async def prepare(self, request: ExecutionRequest) -> PreparedExecution: ...

    async def start(self, prepared: PreparedExecution) -> ExecutionHandle: ...

    def stream(self, handle: ExecutionHandle) -> AsyncIterator[ExecutionEvent]: ...

    async def cancel(self, handle: ExecutionHandle) -> CancelResult: ...

    async def status(self, handle: ExecutionHandle) -> ExecutionStatusSnapshot: ...

    async def result(self, handle: ExecutionHandle) -> ExecutionResult: ...

    async def cleanup(self, handle: ExecutionHandle) -> None: ...

    async def health(self) -> ExecutorHealth: ...

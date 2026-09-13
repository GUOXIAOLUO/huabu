"""Generic direct model/API execution route behind the Executor contract.

A direct model execution calls one provider endpoint configured through a
:class:`ProviderConnection` that is reachable through one
:class:`ModelAvailability` provider route.  This adapter owns only Workbench
lifecycle translation for that call: route resolution from the separate
availability/connection records, event/output normalization, and the
timeout/cancel boundaries.

Transport, HTTP or SDK details, authentication and credential resolution stay
behind the injected :class:`DirectModelTransport` port, so no provider SDK or
secret material reaches the domain or this adapter.  Route identity is never
substituted: a ``runtime`` route belongs to another executor (for example
``CodexHarnessExecutor``) and is rejected here rather than silently rerouted.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, Callable, Literal, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field, model_validator

from workbench.domain.availability import ModelAvailability
from workbench.domain.execution import (
    CancelResult,
    ExecutionEvent,
    ExecutionHandle,
    ExecutionInput,
    ExecutionOutput,
    ExecutionProfile,
    ExecutionRequest,
    ExecutionResult,
    ExecutionStatusSnapshot,
    ExecutorHealth,
    PreparedExecution,
)
from workbench.domain.provider import ProviderConnection
from workbench.domain.value_types import OpaqueId, assert_safe_metadata


DIRECT_MODEL_EXECUTOR_REF = "direct-model"
DIRECT_MODEL_ROUTE_TYPE = "provider"
DIRECT_MODEL_OUTPUT_NAME = "text"
DEFAULT_DIRECT_MODEL_TIMEOUT_SECONDS = 60.0
DEFAULT_DIRECT_MODEL_CANCEL_TIMEOUT_SECONDS = 10.0

_UNUSABLE_CONNECTION_STATUSES = frozenset({"disabled", "error"})

AvailabilityResolver = Callable[[str], ModelAvailability | None]
ConnectionResolver = Callable[[str], ProviderConnection | None]


class DirectModelExecutorError(RuntimeError):
    """A bounded failure at the direct model route boundary."""


class DirectModelTransportError(RuntimeError):
    """A bounded failure raised by a direct model transport implementation."""


class _SeamModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class DirectModelCall(_SeamModel):
    """One provider-neutral direct model call.

    Every provider-facing value is an opaque reference: the credential travels
    as a ``credential_ref`` id that only the transport's credential store can
    resolve, so no secret material crosses the executor or domain boundary.
    """

    execution_id: OpaqueId
    idempotency_key: OpaqueId
    availability_ref: OpaqueId
    model_ref: OpaqueId
    provider_id: OpaqueId
    connection_ref: OpaqueId
    credential_ref: OpaqueId | None = None
    inputs: tuple[ExecutionInput, ...] = ()
    parameters: dict[str, Any] = Field(default_factory=dict)
    connection_config: dict[str, Any] = Field(default_factory=dict)
    capabilities: tuple[OpaqueId, ...] = ()

    @model_validator(mode="after")
    def validate_call(self):
        assert_safe_metadata(self.parameters, path="parameters")
        assert_safe_metadata(self.connection_config, path="connection_config")
        if len(self.capabilities) != len(set(self.capabilities)):
            raise ValueError("direct model call capabilities must be unique")
        return self


class DirectModelSubmission(_SeamModel):
    """Transport-owned acceptance token for one submitted direct model call."""

    submission_id: OpaqueId
    status: Literal["accepted", "running"] = "accepted"
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_metadata(self):
        assert_safe_metadata(self.metadata)
        return self


class DirectModelRawEvent(_SeamModel):
    """One provider-shaped event before Workbench normalization."""

    kind: Literal["progress", "partial_result", "completed", "failed", "cancelled"]
    name: OpaqueId | None = None
    value: Any = None
    message: str | None = None
    usage: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_event(self):
        assert_safe_metadata(self.usage, path="usage")
        assert_safe_metadata(self.metadata)
        return self


@runtime_checkable
class DirectModelTransport(Protocol):
    """The provider-facing call boundary owned by transport adapters.

    Implementations own endpoint selection, authentication, wire format and
    upstream cancellation.  ``next_event`` returning ``None`` means the
    provider stream finished without emitting an explicit terminal event.
    """

    async def submit(self, call: DirectModelCall) -> DirectModelSubmission: ...

    async def next_event(self, submission: DirectModelSubmission) -> DirectModelRawEvent | None: ...

    async def cancel(self, submission: DirectModelSubmission) -> bool: ...

    async def close(self, submission: DirectModelSubmission) -> None: ...


@dataclass
class _ExecutionState:
    request: ExecutionRequest
    call: DirectModelCall
    submission: DirectModelSubmission
    status: str = "running"
    sequence: int = 0
    outputs: list[ExecutionOutput] = field(default_factory=list)
    usage: dict[str, Any] = field(default_factory=dict)
    result: ExecutionResult | None = None
    cancel_event: ExecutionEvent | None = None
    wake: asyncio.Event = field(default_factory=asyncio.Event)
    terminal_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    cleaned: bool = False


class DirectModelExecutor:
    """Adapt one direct provider model call to the generic Executor lifecycle.

    The executor resolves its route from ``ModelAvailability`` and
    ``ProviderConnection`` records but never selects a replacement route,
    model, or executor; an unusable or non-provider route is a bounded error.
    """

    executor_ref = DIRECT_MODEL_EXECUTOR_REF

    def __init__(
        self,
        *,
        transport: DirectModelTransport,
        availability_resolver: AvailabilityResolver,
        connection_resolver: ConnectionResolver,
        profile: ExecutionProfile | None = None,
        timeout_seconds: float | None = None,
        cancel_timeout_seconds: float | None = None,
    ):
        if not isinstance(transport, DirectModelTransport):
            raise TypeError("DirectModelExecutor requires a DirectModelTransport")
        if not callable(availability_resolver):
            raise TypeError("DirectModelExecutor requires an availability resolver")
        if not callable(connection_resolver):
            raise TypeError("DirectModelExecutor requires a connection resolver")
        if profile is not None and profile.executor_ref != DIRECT_MODEL_EXECUTOR_REF:
            raise ValueError("DirectModelExecutor requires a direct-model execution profile")
        if profile is not None:
            if timeout_seconds is not None and timeout_seconds != profile.timeout_seconds:
                raise ValueError("timeout_seconds must match the execution profile")
            if cancel_timeout_seconds is not None and cancel_timeout_seconds != profile.cancel_timeout_seconds:
                raise ValueError("cancel_timeout_seconds must match the execution profile")
        timeout_seconds = profile.timeout_seconds if profile is not None else (DEFAULT_DIRECT_MODEL_TIMEOUT_SECONDS if timeout_seconds is None else timeout_seconds)
        cancel_timeout_seconds = profile.cancel_timeout_seconds if profile is not None else (DEFAULT_DIRECT_MODEL_CANCEL_TIMEOUT_SECONDS if cancel_timeout_seconds is None else cancel_timeout_seconds)
        if timeout_seconds <= 0:
            raise ValueError("Direct model timeout_seconds must be positive")
        if cancel_timeout_seconds <= 0:
            raise ValueError("Direct model cancel_timeout_seconds must be positive")
        self._transport = transport
        self._availability_resolver = availability_resolver
        self._connection_resolver = connection_resolver
        self._profile = profile
        self._timeout_seconds = timeout_seconds
        self._cancel_timeout_seconds = cancel_timeout_seconds
        self._prepared: dict[str, tuple[ExecutionRequest, DirectModelCall]] = {}
        self._states: dict[str, _ExecutionState] = {}

    async def prepare(self, request: ExecutionRequest) -> PreparedExecution:
        if request.execution_id in self._states:
            raise DirectModelExecutorError(f"execution is already prepared: {request.execution_id}")
        if request.execution_id in self._prepared:
            raise DirectModelExecutorError(f"execution is already prepared: {request.execution_id}")
        if self._profile is not None and request.execution_profile_ref not in {
            self._profile.id,
            f"{self._profile.id}@{self._profile.version}",
        }:
            raise DirectModelExecutorError("execution request does not use the configured execution profile")
        call, availability = self._build_call(request)
        self._prepared[request.execution_id] = (request, call)
        return PreparedExecution(
            execution_id=request.execution_id,
            executor_ref=self.executor_ref,
            metadata={
                "route_type": DIRECT_MODEL_ROUTE_TYPE,
                "model_ref": call.model_ref,
                "provider_id": call.provider_id,
                "connection_ref": call.connection_ref,
                "executor_type": availability.executor_type,
            },
        )

    async def start(self, prepared: PreparedExecution) -> ExecutionHandle:
        self._require_prepared(prepared)
        entry = self._prepared.pop(prepared.execution_id, None)
        if entry is None:
            raise DirectModelExecutorError(f"execution was not prepared: {prepared.execution_id}")
        request, call = entry
        try:
            submission = await self._within_timeout(self._transport.submit(call), self._timeout_seconds)
        except (DirectModelTransportError, asyncio.TimeoutError) as error:
            raise DirectModelExecutorError(str(error)) from error
        if not isinstance(submission, DirectModelSubmission):
            raise DirectModelExecutorError("direct model transport returned an invalid submission")
        self._states[request.execution_id] = _ExecutionState(request=request, call=call, submission=submission)
        return ExecutionHandle(execution_id=request.execution_id, executor_ref=self.executor_ref)

    async def stream(self, handle: ExecutionHandle):
        state = self._state(handle)
        deadline = asyncio.get_running_loop().time() + self._timeout_seconds
        yield self._event(state, "started", "running")
        while True:
            if state.cancel_event is not None:
                event, state.cancel_event = state.cancel_event, None
                yield event
                break
            if state.result is not None:
                break
            remaining = deadline - asyncio.get_running_loop().time()
            if remaining <= 0:
                async with state.terminal_lock:
                    if state.cancel_event is not None or state.result is not None:
                        continue
                    event = self._terminal_event(state, "failed", "Direct model execution timed out")
                yield event
                break
            queue_task = asyncio.create_task(self._transport.next_event(state.submission))
            wake_task = asyncio.create_task(state.wake.wait())
            done, pending = await asyncio.wait(
                {queue_task, wake_task},
                timeout=remaining,
                return_when=asyncio.FIRST_COMPLETED,
            )
            for task in pending:
                task.cancel()
            if pending:
                await asyncio.gather(*pending, return_exceptions=True)
            if not done:
                async with state.terminal_lock:
                    if state.cancel_event is not None or state.result is not None:
                        continue
                    event = self._terminal_event(state, "failed", "Direct model execution timed out")
                yield event
                break
            if wake_task in done:
                continue
            if queue_task.exception() is not None:
                error = queue_task.exception()
                terminal_message = str(error) if str(error) else "Direct model execution failed"
                async with state.terminal_lock:
                    if state.cancel_event is not None or state.result is not None:
                        continue
                    event = self._terminal_event(state, "failed", terminal_message)
                yield event
                break
            raw = queue_task.result()
            async with state.terminal_lock:
                if state.cancel_event is not None or state.result is not None:
                    continue
                if raw is None:
                    event = self._terminal_event(state, "succeeded", None)
                else:
                    event = self._map_event(state, raw)
            yield event
            if state.result is not None:
                break

    async def cancel(self, handle: ExecutionHandle) -> CancelResult:
        state = self._state(handle)
        async with state.terminal_lock:
            if state.result is not None:
                return CancelResult(
                    execution_id=handle.execution_id,
                    accepted=state.result.status == "cancelled",
                    status=state.result.status,
                )
            try:
                accepted = await self._within_timeout(self._transport.cancel(state.submission), self._cancel_timeout_seconds)
            except (DirectModelTransportError, asyncio.TimeoutError):
                return CancelResult(execution_id=handle.execution_id, accepted=False, status="unknown")
            if not accepted:
                return CancelResult(execution_id=handle.execution_id, accepted=False, status="unknown")
            state.status = "cancelled"
            state.result = ExecutionResult(execution_id=handle.execution_id, status="cancelled", outputs=tuple(state.outputs))
            state.cancel_event = self._event(state, "cancelled", "cancelled", message="Direct model execution cancelled")
        state.wake.set()
        return CancelResult(execution_id=handle.execution_id, accepted=True, status="cancelled")

    async def status(self, handle: ExecutionHandle) -> ExecutionStatusSnapshot:
        state = self._state(handle)
        status = state.result.status if state.result is not None else state.status
        return ExecutionStatusSnapshot(execution_id=handle.execution_id, status=status)

    async def result(self, handle: ExecutionHandle) -> ExecutionResult:
        state = self._state(handle)
        if state.result is None:
            raise DirectModelExecutorError("direct model execution has not reached a terminal state")
        return state.result

    async def cleanup(self, handle: ExecutionHandle) -> None:
        state = self._state(handle)
        if state.cleaned:
            return
        state.cleaned = True
        await self._transport.close(state.submission)
        self._states.pop(handle.execution_id, None)

    async def health(self) -> ExecutorHealth:
        return ExecutorHealth(
            executor_ref=self.executor_ref,
            status="healthy",
            metadata={"route_type": DIRECT_MODEL_ROUTE_TYPE},
        )

    def _build_call(self, request: ExecutionRequest) -> tuple[DirectModelCall, ModelAvailability]:
        availability_ref = request.model_availability_ref
        if not availability_ref:
            raise DirectModelExecutorError("direct model execution requires a model availability reference")
        availability = self._availability_resolver(availability_ref)
        if availability is None:
            raise DirectModelExecutorError(f"model availability is not available: {availability_ref}")
        if availability.route_type != DIRECT_MODEL_ROUTE_TYPE:
            raise DirectModelExecutorError("direct model execution requires a provider route")
        if not availability.enabled:
            raise DirectModelExecutorError(f"model availability is disabled: {availability.id}")
        if availability.status == "unavailable":
            raise DirectModelExecutorError(f"model availability is unavailable: {availability.id}")
        connection = self._connection_resolver(availability.route_ref)
        if connection is None:
            raise DirectModelExecutorError(f"provider connection is not configured: {availability.route_ref}")
        if connection.status in _UNUSABLE_CONNECTION_STATUSES:
            raise DirectModelExecutorError(f"provider connection is not usable: {connection.id}")
        parameters = dict(self._profile.default_params) if self._profile is not None else {}
        parameters.update(request.config)
        call = DirectModelCall(
            execution_id=request.execution_id,
            idempotency_key=request.idempotency_key,
            availability_ref=availability.id,
            model_ref=availability.model_ref,
            provider_id=connection.provider_id,
            connection_ref=connection.id,
            credential_ref=connection.credential_ref.id if connection.credential_ref is not None else None,
            inputs=request.inputs,
            parameters=parameters,
            connection_config=dict(connection.config),
            capabilities=availability.normalized_capabilities,
        )
        return call, availability

    def _require_prepared(self, prepared: PreparedExecution) -> None:
        if prepared.executor_ref != self.executor_ref:
            raise DirectModelExecutorError("prepared execution belongs to another executor")
        if prepared.execution_id in self._states:
            raise DirectModelExecutorError(f"execution is already started: {prepared.execution_id}")

    def _state(self, handle: ExecutionHandle) -> _ExecutionState:
        if handle.executor_ref != self.executor_ref:
            raise DirectModelExecutorError("execution handle belongs to another executor")
        try:
            return self._states[handle.execution_id]
        except KeyError as error:
            raise DirectModelExecutorError(f"execution is not active: {handle.execution_id}") from error

    @staticmethod
    async def _within_timeout(awaitable, timeout: float):
        return await asyncio.wait_for(awaitable, timeout=timeout)

    def _map_event(self, state: _ExecutionState, raw: DirectModelRawEvent) -> ExecutionEvent:
        outputs: tuple[ExecutionOutput, ...] = ()
        if raw.value is not None:
            output = ExecutionOutput(name=raw.name or DIRECT_MODEL_OUTPUT_NAME, value=raw.value)
            state.outputs.append(output)
            outputs = (output,)
        if raw.usage:
            state.usage.update(raw.usage)
        if raw.kind == "completed":
            return self._terminal_event(state, "succeeded", raw.message, outputs)
        if raw.kind == "failed":
            return self._terminal_event(state, "failed", raw.message or "Direct model execution failed", outputs)
        if raw.kind == "cancelled":
            return self._terminal_event(state, "cancelled", raw.message, outputs)
        return self._event(state, raw.kind, "running", message=raw.message, outputs=outputs)

    def _event(self, state: _ExecutionState, kind, status, *, message=None, outputs=()):
        event = ExecutionEvent(
            execution_id=state.request.execution_id,
            sequence=state.sequence,
            kind=kind,
            status=status,
            outputs=outputs,
            message=message if isinstance(message, str) else None,
            metadata={"route_type": DIRECT_MODEL_ROUTE_TYPE, "provider_id": state.call.provider_id},
        )
        state.sequence += 1
        return event

    def _terminal_event(self, state: _ExecutionState, status, message, outputs=()):
        if status == "failed":
            state.status = "failed"
            state.result = ExecutionResult(
                execution_id=state.request.execution_id,
                status="failed",
                outputs=tuple(state.outputs),
                error=message or "Direct model execution failed",
            )
            kind = "failed"
        elif status == "cancelled":
            state.status = "cancelled"
            state.result = ExecutionResult(
                execution_id=state.request.execution_id,
                status="cancelled",
                outputs=tuple(state.outputs),
            )
            kind = "cancelled"
        else:
            state.status = "succeeded"
            state.result = ExecutionResult(
                execution_id=state.request.execution_id,
                status="succeeded",
                outputs=tuple(state.outputs),
                usage=dict(state.usage),
            )
            kind = "completed"
        return self._event(state, kind, status, message=message, outputs=outputs)

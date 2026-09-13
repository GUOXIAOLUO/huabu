"""RunningHub execution behind the provider-neutral Executor contract.

Before this seam, RunningHub execution was owned by the Canvas runtime: the
``/api/runninghub/submit`` and ``/api/runninghub/query`` endpoints carried the
whole task lifecycle (submit, poll, classify status codes, collect outputs)
inside request handlers that also served provider-shaped Canvas cards.

:class:`RunningHubExecutor` owns the Workbench side of one RunningHub run
instead: it resolves a versioned retained route (``ai_app`` or ``workflow``)
plus the configured execution profile, maps Workbench input roles onto
RunningHub ``nodeInfoList`` fields, and normalizes RunningHub task status and
outputs into typed :class:`ExecutionEvent` / :class:`ExecutionOutput` values.
RunningHub is thereby one executor route among several, not the owner of a
Canvas runtime.

RunningHub transport (endpoint URLs, API key/wallet resolution, HTTP polling,
status-code semantics and output extraction) stays behind the injected
:class:`RunningHubTransport` port, so no provider SDK, secret material, or
status-code table reaches the domain or this seam.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, Callable, Literal, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field, model_validator

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
from workbench.domain.value_types import OpaqueId, assert_safe_metadata


RUNNINGHUB_EXECUTOR_REF = "runninghub"
RUNNINGHUB_RUNTIME_ROUTE = "runninghub"
DEFAULT_RUNNINGHUB_TIMEOUT_SECONDS = 1800.0
DEFAULT_RUNNINGHUB_CANCEL_TIMEOUT_SECONDS = 30.0

RunningHubRouteKind = Literal["ai_app", "workflow"]
RunningHubOutputKind = Literal["image", "video", "audio", "text", "file"]
RunningHubRawEventKind = Literal["queued", "running", "progress", "output", "completed", "failed", "cancelled"]

RouteResolver = Callable[["RunningHubRouteRef"], "RunningHubRoute | None"]


class RunningHubExecutorError(RuntimeError):
    """A bounded failure at the RunningHub executor boundary."""


class RunningHubTransportError(RuntimeError):
    """A bounded failure raised by a RunningHub transport implementation."""


class _SeamModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class RunningHubRouteRef(_SeamModel):
    """Exact reference to one immutable retained RunningHub route version."""

    kind: RunningHubRouteKind
    route_id: OpaqueId
    version: int = Field(ge=1)

    @property
    def ref(self) -> str:
        return f"{self.kind}:{self.route_id}@{self.version}"

    @classmethod
    def parse(cls, value: Any) -> "RunningHubRouteRef":
        """Accept ``kind:route_id@version`` or an explicit mapping.

        A missing version is an error rather than an implied "latest": the
        executor never silently substitutes another route version.
        """
        if isinstance(value, RunningHubRouteRef):
            return value
        if isinstance(value, dict):
            kind = value.get("kind") or value.get("route_kind")
            route_id = value.get("route_id") or value.get("id")
            version = value.get("version")
            if kind not in ("ai_app", "workflow"):
                raise ValueError("RunningHub route reference requires kind ai_app or workflow")
            if not isinstance(route_id, str) or not route_id.strip():
                raise ValueError("RunningHub route reference requires a route_id")
            if not isinstance(version, int) or isinstance(version, bool) or version < 1:
                raise ValueError("RunningHub route reference requires a positive integer version")
            return cls(kind=kind, route_id=route_id.strip(), version=version)
        if not isinstance(value, str) or not value.strip():
            raise ValueError("RunningHub route reference must be a string or mapping")
        text = value.strip()
        head, _, tail = text.partition(":")
        if not head or not tail:
            raise ValueError("RunningHub route reference requires kind:route_id@version")
        if head not in ("ai_app", "workflow"):
            raise ValueError("RunningHub route reference requires kind ai_app or workflow")
        route_id, _, raw_version = tail.rpartition("@")
        if not route_id or not raw_version:
            raise ValueError("RunningHub route reference requires an explicit version")
        try:
            version = int(raw_version)
        except ValueError as error:
            raise ValueError(f"RunningHub route reference has an invalid version: {text}") from error
        if version < 1:
            raise ValueError("RunningHub route reference requires a positive integer version")
        return cls(kind=head, route_id=route_id, version=version)


class RunningHubNodeBinding(_SeamModel):
    """Map one Workbench input role onto one RunningHub node field."""

    role: OpaqueId
    node_id: OpaqueId
    field_name: OpaqueId
    required: bool = True


class RunningHubRoute(_SeamModel):
    """One immutable retained RunningHub route version."""

    kind: RunningHubRouteKind
    route_id: OpaqueId
    version: int = Field(ge=1)
    title: str = ""
    instance_type: OpaqueId | None = None
    add_metadata: bool = False
    node_bindings: tuple[RunningHubNodeBinding, ...] = ()

    @model_validator(mode="after")
    def validate_route(self):
        roles = [binding.role for binding in self.node_bindings]
        if len(roles) != len(set(roles)):
            raise ValueError("RunningHub route node bindings must have unique roles")
        return self

    @property
    def ref(self) -> RunningHubRouteRef:
        return RunningHubRouteRef(kind=self.kind, route_id=self.route_id, version=self.version)


class RunningHubNodeInfo(_SeamModel):
    """One sanitized ``nodeInfoList`` entry for a RunningHub submit call."""

    node_id: OpaqueId
    field_name: OpaqueId
    value: Any = None


class RunningHubCall(_SeamModel):
    """One provider-neutral RunningHub task call."""

    execution_id: OpaqueId
    idempotency_key: OpaqueId
    route_kind: RunningHubRouteKind
    route_id: OpaqueId
    route_version: int = Field(ge=1)
    connection_ref: OpaqueId | None = None
    node_info: tuple[RunningHubNodeInfo, ...] = ()
    parameters: dict[str, Any] = Field(default_factory=dict)
    capabilities: tuple[OpaqueId, ...] = ()

    @model_validator(mode="after")
    def validate_call(self):
        assert_safe_metadata(self.parameters, path="parameters")
        return self

    @property
    def route_ref(self) -> str:
        return f"{self.route_kind}:{self.route_id}@{self.route_version}"


class RunningHubSubmission(_SeamModel):
    """Transport-owned acceptance token for one submitted RunningHub task."""

    task_id: OpaqueId
    status: Literal["queued", "running"] = "queued"
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_metadata(self):
        assert_safe_metadata(self.metadata)
        return self


class RunningHubOutputItem(_SeamModel):
    """One normalized RunningHub output item declared by the transport."""

    kind: RunningHubOutputKind
    url: OpaqueId
    filename: OpaqueId | None = None
    text: str | None = None
    name: OpaqueId | None = None


class RunningHubRawEvent(_SeamModel):
    """One RunningHub-shaped event before Workbench normalization."""

    kind: RunningHubRawEventKind
    code: int | None = None
    items: tuple[RunningHubOutputItem, ...] = ()
    message: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_event(self):
        assert_safe_metadata(self.metadata)
        return self


@runtime_checkable
class RunningHubTransport(Protocol):
    """The RunningHub-facing boundary owned by transport adapters.

    Implementations own endpoint URLs, API key/wallet resolution, HTTP
    polling, RunningHub status-code semantics and output extraction.
    ``next_event`` returning ``None`` means the task stream finished without an
    explicit terminal event.
    """

    async def submit(self, call: RunningHubCall) -> RunningHubSubmission: ...

    async def next_event(self, submission: RunningHubSubmission) -> RunningHubRawEvent | None: ...

    async def cancel(self, submission: RunningHubSubmission) -> bool: ...

    async def close(self, submission: RunningHubSubmission) -> None: ...


@dataclass
class _ExecutionState:
    request: ExecutionRequest
    call: RunningHubCall
    submission: RunningHubSubmission
    status: str = "running"
    sequence: int = 0
    outputs: list[ExecutionOutput] = field(default_factory=list)
    result: ExecutionResult | None = None
    cancel_event: ExecutionEvent | None = None
    wake: asyncio.Event = field(default_factory=asyncio.Event)
    terminal_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    cleaned: bool = False


class RunningHubExecutor:
    """Adapt one RunningHub task run to the generic Executor lifecycle.

    RunningHub is one executor route here, not the owner of a Canvas runtime:
    the executor consumes only the resolved route, the execution profile, and
    the projected inputs.
    """

    executor_ref = RUNNINGHUB_EXECUTOR_REF

    def __init__(
        self,
        *,
        transport: RunningHubTransport,
        route_resolver: RouteResolver,
        profile: ExecutionProfile | None = None,
        timeout_seconds: float | None = None,
        cancel_timeout_seconds: float | None = None,
    ):
        if not isinstance(transport, RunningHubTransport):
            raise TypeError("RunningHubExecutor requires a RunningHubTransport")
        if not callable(route_resolver):
            raise TypeError("RunningHubExecutor requires a route resolver")
        if profile is not None and profile.executor_ref != RUNNINGHUB_EXECUTOR_REF:
            raise ValueError("RunningHubExecutor requires a runninghub execution profile")
        if profile is not None:
            if timeout_seconds is not None and timeout_seconds != profile.timeout_seconds:
                raise ValueError("timeout_seconds must match the execution profile")
            if cancel_timeout_seconds is not None and cancel_timeout_seconds != profile.cancel_timeout_seconds:
                raise ValueError("cancel_timeout_seconds must match the execution profile")
        timeout_seconds = profile.timeout_seconds if profile is not None else (DEFAULT_RUNNINGHUB_TIMEOUT_SECONDS if timeout_seconds is None else timeout_seconds)
        cancel_timeout_seconds = profile.cancel_timeout_seconds if profile is not None else (DEFAULT_RUNNINGHUB_CANCEL_TIMEOUT_SECONDS if cancel_timeout_seconds is None else cancel_timeout_seconds)
        if timeout_seconds <= 0:
            raise ValueError("RunningHub timeout_seconds must be positive")
        if cancel_timeout_seconds <= 0:
            raise ValueError("RunningHub cancel_timeout_seconds must be positive")
        self._transport = transport
        self._route_resolver = route_resolver
        self._profile = profile
        self._timeout_seconds = timeout_seconds
        self._cancel_timeout_seconds = cancel_timeout_seconds
        self._prepared: dict[str, tuple[ExecutionRequest, RunningHubCall]] = {}
        self._states: dict[str, _ExecutionState] = {}

    async def prepare(self, request: ExecutionRequest) -> PreparedExecution:
        if request.execution_id in self._states:
            raise RunningHubExecutorError(f"execution is already prepared: {request.execution_id}")
        if request.execution_id in self._prepared:
            raise RunningHubExecutorError(f"execution is already prepared: {request.execution_id}")
        if self._profile is not None and request.execution_profile_ref not in {
            self._profile.id,
            f"{self._profile.id}@{self._profile.version}",
        }:
            raise RunningHubExecutorError("execution request does not use the configured execution profile")
        call, route = self._build_call(request)
        self._prepared[request.execution_id] = (request, call)
        return PreparedExecution(
            execution_id=request.execution_id,
            executor_ref=self.executor_ref,
            metadata={
                "runtime_route": RUNNINGHUB_RUNTIME_ROUTE,
                "route_ref": call.route_ref,
                "connection_ref": call.connection_ref or "",
                "input_roles": tuple(binding.role for binding in route.node_bindings),
            },
        )

    async def start(self, prepared: PreparedExecution) -> ExecutionHandle:
        self._require_prepared(prepared)
        entry = self._prepared.pop(prepared.execution_id, None)
        if entry is None:
            raise RunningHubExecutorError(f"execution was not prepared: {prepared.execution_id}")
        request, call = entry
        try:
            submission = await self._within_timeout(self._transport.submit(call), self._timeout_seconds)
        except (RunningHubTransportError, asyncio.TimeoutError) as error:
            raise RunningHubExecutorError(str(error)) from error
        if not isinstance(submission, RunningHubSubmission):
            raise RunningHubExecutorError("runninghub transport returned an invalid submission")
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
                    event = self._terminal_event(state, "failed", "RunningHub execution timed out")
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
                    event = self._terminal_event(state, "failed", "RunningHub execution timed out")
                yield event
                break
            if wake_task in done:
                continue
            async with state.terminal_lock:
                if state.cancel_event is not None or state.result is not None:
                    continue
                if queue_task.exception() is not None:
                    error = queue_task.exception()
                    event = self._terminal_event(state, "failed", str(error) or "RunningHub execution failed")
                else:
                    raw = queue_task.result()
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
            except (RunningHubTransportError, asyncio.TimeoutError):
                return CancelResult(execution_id=handle.execution_id, accepted=False, status="unknown")
            if not accepted:
                return CancelResult(execution_id=handle.execution_id, accepted=False, status="unknown")
            state.status = "cancelled"
            state.result = ExecutionResult(execution_id=handle.execution_id, status="cancelled", outputs=tuple(state.outputs))
            state.cancel_event = self._event(state, "cancelled", "cancelled", message="RunningHub execution cancelled")
        state.wake.set()
        return CancelResult(execution_id=handle.execution_id, accepted=True, status="cancelled")

    async def status(self, handle: ExecutionHandle) -> ExecutionStatusSnapshot:
        state = self._state(handle)
        status = state.result.status if state.result is not None else state.status
        return ExecutionStatusSnapshot(execution_id=handle.execution_id, status=status)

    async def result(self, handle: ExecutionHandle) -> ExecutionResult:
        state = self._state(handle)
        if state.result is None:
            raise RunningHubExecutorError("runninghub execution has not reached a terminal state")
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
            metadata={"runtime_route": RUNNINGHUB_RUNTIME_ROUTE},
        )

    def _build_call(self, request: ExecutionRequest) -> tuple[RunningHubCall, RunningHubRoute]:
        reference = self._resolve_reference(request)
        route = self._route_resolver(reference)
        if route is None:
            raise RunningHubExecutorError(f"runninghub route is not available: {reference.ref}")
        if route.kind != reference.kind or route.route_id != reference.route_id or route.version != reference.version:
            raise RunningHubExecutorError(f"runninghub route version mismatch: {reference.ref}")
        node_info = self._build_node_info(request, route)
        parameters = dict(self._profile.default_params) if self._profile is not None else {}
        parameters.update(request.config)
        connection_ref = self._config_value(request, "connection_ref")
        if not isinstance(connection_ref, str) or not connection_ref:
            connection_ref = self._profile.runtime_connection_ref if self._profile is not None else None
        call = RunningHubCall(
            execution_id=request.execution_id,
            idempotency_key=request.idempotency_key,
            route_kind=route.kind,
            route_id=route.route_id,
            route_version=route.version,
            connection_ref=connection_ref,
            node_info=node_info,
            parameters=parameters,
        )
        return call, route

    def _resolve_reference(self, request: ExecutionRequest) -> RunningHubRouteRef:
        raw_reference = self._config_value(request, "route_ref")
        if raw_reference is None and self._profile is not None:
            raw_reference = self._profile.default_params.get("route_ref")
        if raw_reference is None:
            raise RunningHubExecutorError("runninghub execution requires a route reference")
        try:
            return RunningHubRouteRef.parse(raw_reference)
        except ValueError as error:
            raise RunningHubExecutorError(str(error)) from error

    def _build_node_info(self, request: ExecutionRequest, route: RunningHubRoute) -> tuple[RunningHubNodeInfo, ...]:
        bindings = {binding.role: binding for binding in route.node_bindings}
        supplied: set[str] = set()
        entries: list[RunningHubNodeInfo] = []
        for item in request.inputs:
            role = self._role_for(request, item)
            binding = bindings.get(role)
            if binding is None:
                raise RunningHubExecutorError(f"runninghub route has no node binding for role: {role}")
            entries.append(RunningHubNodeInfo(node_id=binding.node_id, field_name=binding.field_name, value=item.value))
            supplied.add(role)
        for binding in route.node_bindings:
            if binding.required and binding.role not in supplied:
                raise RunningHubExecutorError(f"runninghub route is missing required input role: {binding.role}")
        return tuple(entries)

    @staticmethod
    def _config_value(request: ExecutionRequest, key: str) -> Any:
        """Read a call setting from the request config or its nested parameters.

        ``ExecutionService`` nests the frozen input projection parameters under
        ``config["parameters"]``, so both shapes resolve identically.
        """
        if key in request.config:
            return request.config[key]
        parameters = request.config.get("parameters")
        if isinstance(parameters, dict) and key in parameters:
            return parameters[key]
        return None

    @staticmethod
    def _role_for(request: ExecutionRequest, item: ExecutionInput) -> str:
        declared = RunningHubExecutor._config_value(request, "input_roles")
        if isinstance(declared, dict) and item.name in declared:
            role = declared[item.name]
            if isinstance(role, str) and role:
                return role
        return item.name

    def _require_prepared(self, prepared: PreparedExecution) -> None:
        if prepared.executor_ref != self.executor_ref:
            raise RunningHubExecutorError("prepared execution belongs to another executor")
        if prepared.execution_id in self._states:
            raise RunningHubExecutorError(f"execution is already started: {prepared.execution_id}")

    def _state(self, handle: ExecutionHandle) -> _ExecutionState:
        if handle.executor_ref != self.executor_ref:
            raise RunningHubExecutorError("execution handle belongs to another executor")
        try:
            return self._states[handle.execution_id]
        except KeyError as error:
            raise RunningHubExecutorError(f"execution is not active: {handle.execution_id}") from error

    @staticmethod
    async def _within_timeout(awaitable, timeout: float):
        return await asyncio.wait_for(awaitable, timeout=timeout)

    def _map_event(self, state: _ExecutionState, raw: RunningHubRawEvent) -> ExecutionEvent:
        outputs = self._outputs(state, raw)
        if raw.kind == "queued":
            return self._event(state, "progress", "running", message="RunningHub task queued", raw=raw)
        if raw.kind == "running":
            return self._event(state, "progress", "running", message="RunningHub task running", raw=raw)
        if raw.kind == "progress":
            return self._event(state, "progress", "running", message=raw.message or "RunningHub task progress", raw=raw)
        if raw.kind == "output":
            return self._event(state, "partial_result", "running", message=raw.message, raw=raw, outputs=outputs)
        if raw.kind == "completed":
            return self._terminal_event(state, "succeeded", raw.message, outputs, raw=raw)
        if raw.kind == "failed":
            return self._terminal_event(state, "failed", raw.message or "RunningHub execution failed", outputs, raw=raw)
        return self._terminal_event(state, "cancelled", raw.message, outputs, raw=raw)

    def _outputs(self, state: _ExecutionState, raw: RunningHubRawEvent) -> tuple[ExecutionOutput, ...]:
        if not raw.items:
            return ()
        outputs = []
        for item in raw.items:
            output = ExecutionOutput(name=item.name or f"{item.kind}.{len(state.outputs) + 1}", value=self._output_value(item))
            state.outputs.append(output)
            outputs.append(output)
        return tuple(outputs)

    @staticmethod
    def _output_value(item: RunningHubOutputItem) -> Any:
        if item.kind == "text" and item.text is not None:
            return item.text
        reference: dict[str, Any] = {"kind": item.kind, "url": item.url}
        if item.filename is not None:
            reference["filename"] = item.filename
        return reference

    def _event(self, state: _ExecutionState, kind, status, *, message=None, outputs=(), raw=None):
        metadata: dict[str, Any] = {"runtime_route": RUNNINGHUB_RUNTIME_ROUTE, "route_ref": state.call.route_ref}
        if raw is not None and raw.code is not None:
            metadata["provider_code"] = raw.code
        event = ExecutionEvent(
            execution_id=state.request.execution_id,
            sequence=state.sequence,
            kind=kind,
            status=status,
            outputs=outputs,
            message=message if isinstance(message, str) else None,
            metadata=metadata,
        )
        state.sequence += 1
        return event

    def _terminal_event(self, state: _ExecutionState, status, message, outputs=(), raw=None):
        if status == "failed":
            state.status = "failed"
            state.result = ExecutionResult(
                execution_id=state.request.execution_id,
                status="failed",
                outputs=tuple(state.outputs),
                error=message or "RunningHub execution failed",
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
            )
            kind = "completed"
        return self._event(state, kind, status, message=message, outputs=outputs, raw=raw)

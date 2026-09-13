"""MCP capability execution behind the provider-neutral Executor contract.

Before this seam the product had no Workbench owner for MCP execution at all:
the only place MCP appeared was as an allow-listed CLI sub-command name in the
Codex / Antigravity pass-through, so an MCP call could only ever be an ad-hoc
call owned by whichever surface happened to issue it.

:class:`MCPExecutor` owns the Workbench side of one MCP capability invocation
instead: it maps an explicit connection reference, an explicit capability
reference (``tool:<name>``, ``prompt:<name>`` or ``resource:<name>``) and the
deterministic capability-kind to MCP-action mapping onto one :class:`MCPCall`,
translates Workbench input roles into MCP action arguments through the
capability's binding table, and normalizes MCP results, progress and errors
into typed :class:`ExecutionEvent` / :class:`ExecutionOutput` values.

MCP transport (server process or HTTP/stdio setup, the initialize handshake,
JSON-RPC framing, capability listing) stays behind the injected
:class:`MCPTransport` port, so no MCP client library, transport detail or
credential reaches the domain or this seam.

Integration references are carried as opaque values only.  The Workbench
Integration boundary that will own integration definitions and live
connections arrives in a later round; until then this seam forwards the
reference it is given and never invents, resolves or replaces one.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Callable, Literal, Mapping, Protocol, runtime_checkable

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


MCP_EXECUTOR_REF = "mcp"
MCP_RUNTIME_ROUTE = "mcp"
DEFAULT_MCP_TIMEOUT_SECONDS = 300.0
DEFAULT_MCP_CANCEL_TIMEOUT_SECONDS = 15.0

MCPCapabilityKind = Literal["tool", "prompt", "resource"]
MCPActionKind = Literal["call_tool", "get_prompt", "read_resource"]
MCPOutputKind = Literal["text", "image", "audio", "resource", "link", "json"]
MCPRawEventKind = Literal["accepted", "progress", "output", "completed", "failed", "cancelled"]

# The single deterministic capability-kind to MCP-action mapping.  A caller
# cannot request an arbitrary action, and a call can never carry an action that
# disagrees with its capability kind.
CAPABILITY_ACTIONS: Mapping[MCPCapabilityKind, MCPActionKind] = MappingProxyType(
    {
        "tool": "call_tool",
        "prompt": "get_prompt",
        "resource": "read_resource",
    }
)

CapabilityResolver = Callable[["MCPCapabilityRef"], "MCPCapability | None"]


class MCPExecutorError(RuntimeError):
    """A bounded failure at the MCP executor boundary."""


class MCPTransportError(RuntimeError):
    """A bounded failure raised by an MCP transport implementation."""


class _SeamModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class MCPCapabilityRef(_SeamModel):
    """Exact reference to one capability of one MCP server connection."""

    kind: MCPCapabilityKind
    name: OpaqueId

    @property
    def ref(self) -> str:
        return f"{self.kind}:{self.name}"

    @classmethod
    def parse(cls, value: Any) -> "MCPCapabilityRef":
        """Accept ``kind:name`` or an explicit mapping.

        A missing or unknown kind is an error rather than a guess: the seam
        never substitutes another capability kind.
        """
        if isinstance(value, MCPCapabilityRef):
            return value
        if isinstance(value, dict):
            kind = value.get("kind")
            name = value.get("name")
            if kind not in CAPABILITY_ACTIONS:
                raise ValueError("MCP capability reference requires kind tool, prompt or resource")
            if not isinstance(name, str) or not name.strip():
                raise ValueError("MCP capability reference requires a name")
            return cls(kind=kind, name=name.strip())
        if not isinstance(value, str) or not value.strip():
            raise ValueError("MCP capability reference must be a string or mapping")
        text = value.strip()
        head, separator, tail = text.partition(":")
        if not separator or not head or not tail:
            raise ValueError("MCP capability reference requires kind:name")
        if head not in CAPABILITY_ACTIONS:
            raise ValueError("MCP capability reference requires kind tool, prompt or resource")
        return cls(kind=head, name=tail)


class MCPInputBinding(_SeamModel):
    """Map one Workbench input role onto one MCP action argument."""

    role: OpaqueId
    argument: OpaqueId
    required: bool = True


class MCPCapability(_SeamModel):
    """One immutable resolved MCP capability declaration."""

    kind: MCPCapabilityKind
    name: OpaqueId
    connection_ref: OpaqueId | None = None
    title: str = ""
    input_bindings: tuple[MCPInputBinding, ...] = ()
    integration_ref: OpaqueId | None = None

    @model_validator(mode="after")
    def validate_capability(self):
        roles = [binding.role for binding in self.input_bindings]
        if len(roles) != len(set(roles)):
            raise ValueError("MCP capability input bindings must have unique roles")
        arguments = [binding.argument for binding in self.input_bindings]
        if len(arguments) != len(set(arguments)):
            raise ValueError("MCP capability input bindings must have unique arguments")
        return self

    @property
    def ref(self) -> MCPCapabilityRef:
        return MCPCapabilityRef(kind=self.kind, name=self.name)

    @property
    def action(self) -> MCPActionKind:
        return CAPABILITY_ACTIONS[self.kind]


class MCPOutputItem(_SeamModel):
    """One normalized MCP content item declared by the transport."""

    kind: MCPOutputKind
    name: OpaqueId | None = None
    text: str | None = None
    uri: OpaqueId | None = None
    mime_type: OpaqueId | None = None
    data: Any = None


class MCPRawEvent(_SeamModel):
    """One MCP-shaped event before Workbench normalization.

    MCP reports a failed capability call inside a successful transport
    response (``isError``) rather than as a transport failure, so both signals
    are carried explicitly: ``is_error`` normalizes to a failed execution and
    ``error_code`` is an MCP / JSON-RPC code kept in metadata only.
    """

    kind: MCPRawEventKind
    is_error: bool = False
    error_code: int | None = None
    items: tuple[MCPOutputItem, ...] = ()
    message: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_event(self):
        assert_safe_metadata(self.metadata)
        return self


class MCPSubmission(_SeamModel):
    """Transport-owned acceptance token for one submitted MCP invocation."""

    invocation_id: OpaqueId
    status: Literal["accepted", "running"] = "accepted"
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_metadata(self):
        assert_safe_metadata(self.metadata)
        return self


class MCPCall(_SeamModel):
    """One provider-neutral MCP capability invocation.

    ``arguments`` carries the mapped capability payload and is therefore not
    scanned for credential-looking keys: an MCP tool may legitimately declare
    an argument with such a name.  ``parameters`` carries profile/config
    passthrough and is scanned, because that is where a credential would be
    smuggled across the boundary.
    """

    execution_id: OpaqueId
    idempotency_key: OpaqueId
    capability_kind: MCPCapabilityKind
    capability_name: OpaqueId
    action: MCPActionKind
    connection_ref: OpaqueId | None = None
    integration_ref: OpaqueId | None = None
    arguments: dict[str, Any] = Field(default_factory=dict)
    parameters: dict[str, Any] = Field(default_factory=dict)
    capabilities: tuple[OpaqueId, ...] = ()

    @model_validator(mode="after")
    def validate_call(self):
        expected = CAPABILITY_ACTIONS[self.capability_kind]
        if self.action != expected:
            raise ValueError(f"MCP action must be {expected} for capability kind {self.capability_kind}")
        assert_safe_metadata(self.parameters, path="parameters")
        return self

    @property
    def capability_ref(self) -> str:
        return f"{self.capability_kind}:{self.capability_name}"


@runtime_checkable
class MCPTransport(Protocol):
    """The MCP-facing boundary owned by transport adapters.

    Implementations own server process or HTTP/stdio setup, the initialize
    handshake, JSON-RPC framing, capability listing and credential resolution.
    ``next_event`` returning ``None`` means the invocation stream finished
    without an explicit terminal event.
    """

    async def invoke(self, call: MCPCall) -> MCPSubmission: ...

    async def next_event(self, submission: MCPSubmission) -> MCPRawEvent | None: ...

    async def cancel(self, submission: MCPSubmission) -> bool: ...

    async def close(self, submission: MCPSubmission) -> None: ...


@dataclass
class _ExecutionState:
    request: ExecutionRequest
    call: MCPCall
    submission: MCPSubmission
    status: str = "running"
    sequence: int = 0
    outputs: list[ExecutionOutput] = field(default_factory=list)
    result: ExecutionResult | None = None
    cancel_event: ExecutionEvent | None = None
    wake: asyncio.Event = field(default_factory=asyncio.Event)
    terminal_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    cleaned: bool = False


class MCPExecutor:
    """Adapt one MCP capability invocation to the generic Executor lifecycle.

    MCP is one executor route here, not the owner of a Canvas runtime or of
    Integration definitions: the executor consumes only the resolved
    capability, the execution profile, and the projected inputs.
    """

    executor_ref = MCP_EXECUTOR_REF

    def __init__(
        self,
        *,
        transport: MCPTransport,
        capability_resolver: CapabilityResolver,
        profile: ExecutionProfile | None = None,
        timeout_seconds: float | None = None,
        cancel_timeout_seconds: float | None = None,
    ):
        if not isinstance(transport, MCPTransport):
            raise TypeError("MCPExecutor requires an MCPTransport")
        if not callable(capability_resolver):
            raise TypeError("MCPExecutor requires a capability resolver")
        if profile is not None and profile.executor_ref != MCP_EXECUTOR_REF:
            raise ValueError("MCPExecutor requires an mcp execution profile")
        if profile is not None:
            if timeout_seconds is not None and timeout_seconds != profile.timeout_seconds:
                raise ValueError("timeout_seconds must match the execution profile")
            if cancel_timeout_seconds is not None and cancel_timeout_seconds != profile.cancel_timeout_seconds:
                raise ValueError("cancel_timeout_seconds must match the execution profile")
        timeout_seconds = profile.timeout_seconds if profile is not None else (DEFAULT_MCP_TIMEOUT_SECONDS if timeout_seconds is None else timeout_seconds)
        cancel_timeout_seconds = profile.cancel_timeout_seconds if profile is not None else (DEFAULT_MCP_CANCEL_TIMEOUT_SECONDS if cancel_timeout_seconds is None else cancel_timeout_seconds)
        if timeout_seconds <= 0:
            raise ValueError("MCP timeout_seconds must be positive")
        if cancel_timeout_seconds <= 0:
            raise ValueError("MCP cancel_timeout_seconds must be positive")
        self._transport = transport
        self._capability_resolver = capability_resolver
        self._profile = profile
        self._timeout_seconds = timeout_seconds
        self._cancel_timeout_seconds = cancel_timeout_seconds
        self._prepared: dict[str, tuple[ExecutionRequest, MCPCall]] = {}
        self._states: dict[str, _ExecutionState] = {}

    async def prepare(self, request: ExecutionRequest) -> PreparedExecution:
        if request.execution_id in self._states:
            raise MCPExecutorError(f"execution is already prepared: {request.execution_id}")
        if request.execution_id in self._prepared:
            raise MCPExecutorError(f"execution is already prepared: {request.execution_id}")
        if self._profile is not None and request.execution_profile_ref not in {
            self._profile.id,
            f"{self._profile.id}@{self._profile.version}",
        }:
            raise MCPExecutorError("execution request does not use the configured execution profile")
        call, capability, provenance = self._build_call(request)
        self._prepared[request.execution_id] = (request, call)
        return PreparedExecution(
            execution_id=request.execution_id,
            executor_ref=self.executor_ref,
            metadata={
                "runtime_route": MCP_RUNTIME_ROUTE,
                "capability_ref": call.capability_ref,
                "action": call.action,
                "connection_ref": call.connection_ref or "",
                "requested_connection_ref": provenance["requested_connection_ref"],
                "connection_source": provenance["connection_source"],
                "integration_ref": call.integration_ref or "",
                "input_roles": tuple(binding.role for binding in capability.input_bindings),
            },
        )

    async def start(self, prepared: PreparedExecution) -> ExecutionHandle:
        self._require_prepared(prepared)
        entry = self._prepared.pop(prepared.execution_id, None)
        if entry is None:
            raise MCPExecutorError(f"execution was not prepared: {prepared.execution_id}")
        request, call = entry
        try:
            submission = await self._within_timeout(self._transport.invoke(call), self._timeout_seconds)
        except (MCPTransportError, asyncio.TimeoutError) as error:
            raise MCPExecutorError(str(error)) from error
        if not isinstance(submission, MCPSubmission):
            raise MCPExecutorError("mcp transport returned an invalid submission")
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
                    event = self._terminal_event(state, "failed", "MCP execution timed out")
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
                    event = self._terminal_event(state, "failed", "MCP execution timed out")
                yield event
                break
            if wake_task in done:
                continue
            async with state.terminal_lock:
                if state.cancel_event is not None or state.result is not None:
                    continue
                if queue_task.exception() is not None:
                    error = queue_task.exception()
                    event = self._terminal_event(state, "failed", str(error) or "MCP execution failed")
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
            except (MCPTransportError, asyncio.TimeoutError):
                return CancelResult(execution_id=handle.execution_id, accepted=False, status="unknown")
            if not accepted:
                return CancelResult(execution_id=handle.execution_id, accepted=False, status="unknown")
            state.status = "cancelled"
            state.result = ExecutionResult(execution_id=handle.execution_id, status="cancelled", outputs=tuple(state.outputs))
            state.cancel_event = self._event(state, "cancelled", "cancelled", message="MCP execution cancelled")
        state.wake.set()
        return CancelResult(execution_id=handle.execution_id, accepted=True, status="cancelled")

    async def status(self, handle: ExecutionHandle) -> ExecutionStatusSnapshot:
        state = self._state(handle)
        status = state.result.status if state.result is not None else state.status
        return ExecutionStatusSnapshot(execution_id=handle.execution_id, status=status)

    async def result(self, handle: ExecutionHandle) -> ExecutionResult:
        state = self._state(handle)
        if state.result is None:
            raise MCPExecutorError("mcp execution has not reached a terminal state")
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
            metadata={"runtime_route": MCP_RUNTIME_ROUTE},
        )

    def _build_call(self, request: ExecutionRequest) -> tuple[MCPCall, MCPCapability, dict[str, str]]:
        reference = self._resolve_capability_ref(request)
        capability = self._capability_resolver(reference)
        if capability is None:
            raise MCPExecutorError(f"mcp capability is not available: {reference.ref}")
        if capability.kind != reference.kind or capability.name != reference.name:
            raise MCPExecutorError(f"mcp capability reference mismatch: {reference.ref}")
        arguments = self._build_arguments(request, capability)
        parameters = dict(self._profile.default_params) if self._profile is not None else {}
        parameters.update(request.config)
        connection_ref, requested_connection_ref, connection_source = self._resolve_connection(request, capability)
        integration_ref = self._config_value(request, "integration_ref")
        if not isinstance(integration_ref, str) or not integration_ref:
            integration_ref = capability.integration_ref
        call = MCPCall(
            execution_id=request.execution_id,
            idempotency_key=request.idempotency_key,
            capability_kind=capability.kind,
            capability_name=capability.name,
            action=capability.action,
            connection_ref=connection_ref,
            integration_ref=integration_ref,
            arguments=arguments,
            parameters=parameters,
        )
        return call, capability, {
            "requested_connection_ref": requested_connection_ref or "",
            "connection_source": connection_source,
        }

    def _resolve_connection(self, request: ExecutionRequest, capability: MCPCapability) -> tuple[str | None, str | None, str]:
        """Resolve the connection without letting catalog metadata override it.

        The execution configuration is the requested connection and always
        wins: an explicit call setting first, then the execution profile's
        ``runtime_connection_ref``.  A capability declaration only fills a
        connection the configuration left unspecified, and the source is
        returned so that fill-in is recorded rather than silent.
        """
        requested = self._config_value(request, "connection_ref")
        if not isinstance(requested, str) or not requested:
            requested = self._profile.runtime_connection_ref if self._profile is not None else None
        if isinstance(requested, str) and requested:
            return requested, requested, "request"
        if capability.connection_ref:
            return capability.connection_ref, None, "capability"
        return None, None, ""

    def _resolve_capability_ref(self, request: ExecutionRequest) -> MCPCapabilityRef:
        raw_reference = self._config_value(request, "capability_ref")
        if raw_reference is None and self._profile is not None:
            raw_reference = self._profile.default_params.get("capability_ref")
        if raw_reference is None:
            raise MCPExecutorError("mcp execution requires a capability reference")
        try:
            return MCPCapabilityRef.parse(raw_reference)
        except ValueError as error:
            raise MCPExecutorError(str(error)) from error

    def _build_arguments(self, request: ExecutionRequest, capability: MCPCapability) -> dict[str, Any]:
        bindings = {binding.role: binding for binding in capability.input_bindings}
        supplied: set[str] = set()
        arguments: dict[str, Any] = {}
        for item in request.inputs:
            role = self._role_for(request, item)
            binding = bindings.get(role)
            if binding is None:
                raise MCPExecutorError(f"mcp capability has no argument binding for role: {role}")
            arguments[binding.argument] = item.value
            supplied.add(role)
        for binding in capability.input_bindings:
            if binding.required and binding.role not in supplied:
                raise MCPExecutorError(f"mcp capability is missing required input role: {binding.role}")
        return arguments

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
        declared = MCPExecutor._config_value(request, "input_roles")
        if isinstance(declared, dict) and item.name in declared:
            role = declared[item.name]
            if isinstance(role, str) and role:
                return role
        return item.name

    def _require_prepared(self, prepared: PreparedExecution) -> None:
        if prepared.executor_ref != self.executor_ref:
            raise MCPExecutorError("prepared execution belongs to another executor")
        if prepared.execution_id in self._states:
            raise MCPExecutorError(f"execution is already started: {prepared.execution_id}")

    def _state(self, handle: ExecutionHandle) -> _ExecutionState:
        if handle.executor_ref != self.executor_ref:
            raise MCPExecutorError("execution handle belongs to another executor")
        try:
            return self._states[handle.execution_id]
        except KeyError as error:
            raise MCPExecutorError(f"execution is not active: {handle.execution_id}") from error

    @staticmethod
    async def _within_timeout(awaitable, timeout: float):
        return await asyncio.wait_for(awaitable, timeout=timeout)

    def _map_event(self, state: _ExecutionState, raw: MCPRawEvent) -> ExecutionEvent:
        outputs = self._outputs(state, raw)
        if raw.kind == "accepted":
            return self._event(state, "progress", "running", message="MCP invocation accepted", raw=raw)
        if raw.kind == "progress":
            return self._event(state, "progress", "running", message=raw.message or "MCP invocation progress", raw=raw)
        if raw.kind == "output":
            return self._event(state, "partial_result", "running", message=raw.message, raw=raw, outputs=outputs)
        if raw.kind == "completed":
            if raw.is_error:
                return self._terminal_event(state, "failed", raw.message or "MCP capability reported an error", outputs, raw=raw)
            return self._terminal_event(state, "succeeded", raw.message, outputs, raw=raw)
        if raw.kind == "failed":
            return self._terminal_event(state, "failed", raw.message or "MCP execution failed", outputs, raw=raw)
        return self._terminal_event(state, "cancelled", raw.message, outputs, raw=raw)

    def _outputs(self, state: _ExecutionState, raw: MCPRawEvent) -> tuple[ExecutionOutput, ...]:
        if not raw.items:
            return ()
        outputs = []
        for item in raw.items:
            output = ExecutionOutput(name=item.name or f"{item.kind}.{len(state.outputs) + 1}", value=self._output_value(item))
            state.outputs.append(output)
            outputs.append(output)
        return tuple(outputs)

    @staticmethod
    def _output_value(item: MCPOutputItem) -> Any:
        if item.kind == "text" and item.text is not None:
            return item.text
        reference: dict[str, Any] = {"kind": item.kind}
        if item.uri is not None:
            reference["uri"] = item.uri
        if item.mime_type is not None:
            reference["mime_type"] = item.mime_type
        if item.data is not None:
            reference["data"] = item.data
        return reference

    def _event(self, state: _ExecutionState, kind, status, *, message=None, outputs=(), raw=None):
        metadata: dict[str, Any] = {
            "runtime_route": MCP_RUNTIME_ROUTE,
            "capability_ref": state.call.capability_ref,
            "action": state.call.action,
        }
        if raw is not None and raw.error_code is not None:
            metadata["error_code"] = raw.error_code
        if raw is not None and raw.is_error:
            metadata["is_error"] = True
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
                error=message or "MCP execution failed",
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

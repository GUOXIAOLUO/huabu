"""ComfyUI workflow execution behind the provider-neutral Executor contract.

Before this seam, ComfyUI execution existed only as Canvas-shaped behavior: a
task payload carried a workflow graph next to Canvas node state, and progress
and outputs were interpreted in that Canvas context.  :class:`ComfyUIExecutor`
owns the Workbench side of one ComfyUI run instead: it resolves a versioned
workflow reference and the configured execution profile, maps Workbench input
roles onto ComfyUI node input slots, and normalizes ComfyUI progress and output
events into typed :class:`ExecutionEvent` / :class:`ExecutionOutput` values.

This adapter deliberately owns no Canvas graph: it never recreates or walks a
Canvas node tree, and it takes no provider-shaped Canvas node dependency.
ComfyUI transport (HTTP/WebSocket, backend selection, prompt submission,
history polling) stays behind the injected :class:`ComfyUITransport` port, so
no provider SDK or secret material reaches the domain.
"""

from __future__ import annotations

import asyncio
import copy
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


COMFYUI_EXECUTOR_REF = "comfyui"
COMFYUI_RUNTIME_ROUTE = "comfyui"
DEFAULT_COMFYUI_TIMEOUT_SECONDS = 900.0
DEFAULT_COMFYUI_CANCEL_TIMEOUT_SECONDS = 15.0

ComfyUIOutputKind = Literal["image", "video", "audio", "text", "file"]
ComfyUIRawEventKind = Literal["queued", "executing", "progress", "output", "completed", "failed", "cancelled"]

WorkflowResolver = Callable[["ComfyUIWorkflowRef"], "ComfyUIWorkflow | None"]


class ComfyUIExecutorError(RuntimeError):
    """A bounded failure at the ComfyUI executor boundary."""


class ComfyUITransportError(RuntimeError):
    """A bounded failure raised by a ComfyUI transport implementation."""


class _SeamModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class ComfyUIWorkflowRef(_SeamModel):
    """Exact reference to one immutable ComfyUI workflow version."""

    workflow_id: OpaqueId
    version: int = Field(ge=1)

    @property
    def ref(self) -> str:
        return f"{self.workflow_id}@{self.version}"

    @classmethod
    def parse(cls, value: Any) -> "ComfyUIWorkflowRef":
        """Accept ``id@version``, ``id``, or an explicit mapping.

        A missing version is an error rather than an implied "latest": the
        executor never silently substitutes another workflow version.
        """
        if isinstance(value, ComfyUIWorkflowRef):
            return value
        if isinstance(value, dict):
            workflow_id = value.get("workflow_id") or value.get("id")
            version = value.get("version")
            if not isinstance(workflow_id, str) or not workflow_id.strip():
                raise ValueError("ComfyUI workflow reference requires a workflow_id")
            if not isinstance(version, int) or isinstance(version, bool) or version < 1:
                raise ValueError("ComfyUI workflow reference requires a positive integer version")
            return cls(workflow_id=workflow_id.strip(), version=version)
        if not isinstance(value, str) or not value.strip():
            raise ValueError("ComfyUI workflow reference must be a string or mapping")
        text = value.strip()
        workflow_id, _, raw_version = text.rpartition("@")
        if not workflow_id or not raw_version:
            raise ValueError("ComfyUI workflow reference requires an explicit version: workflow_id@version")
        try:
            version = int(raw_version)
        except ValueError as error:
            raise ValueError(f"ComfyUI workflow reference has an invalid version: {text}") from error
        if version < 1:
            raise ValueError("ComfyUI workflow reference requires a positive integer version")
        return cls(workflow_id=workflow_id, version=version)


class ComfyUIInputBinding(_SeamModel):
    """Map one Workbench input role onto one ComfyUI node input slot."""

    role: OpaqueId
    node_id: OpaqueId
    input_name: OpaqueId
    required: bool = True


class ComfyUIWorkflow(_SeamModel):
    """One immutable ComfyUI workflow version with its role binding table.

    ``graph`` is the ComfyUI API prompt graph.  It carries no secret material:
    credentials belong to the runtime connection, not to a workflow graph.
    """

    id: OpaqueId
    version: int = Field(ge=1)
    title: str = ""
    graph: dict[str, Any] = Field(default_factory=dict)
    input_bindings: tuple[ComfyUIInputBinding, ...] = ()

    @model_validator(mode="after")
    def validate_workflow(self):
        assert_safe_metadata(self.graph, path="graph")
        roles = [binding.role for binding in self.input_bindings]
        if len(roles) != len(set(roles)):
            raise ValueError("ComfyUI workflow input bindings must have unique roles")
        return self

    @property
    def ref(self) -> ComfyUIWorkflowRef:
        return ComfyUIWorkflowRef(workflow_id=self.id, version=self.version)


class ComfyUICall(_SeamModel):
    """One provider-neutral ComfyUI prompt call."""

    execution_id: OpaqueId
    idempotency_key: OpaqueId
    workflow_id: OpaqueId
    workflow_version: int = Field(ge=1)
    connection_ref: OpaqueId | None = None
    graph: dict[str, Any] = Field(default_factory=dict)
    inputs: tuple[ExecutionInput, ...] = ()
    parameters: dict[str, Any] = Field(default_factory=dict)
    capabilities: tuple[OpaqueId, ...] = ()

    @model_validator(mode="after")
    def validate_call(self):
        assert_safe_metadata(self.graph, path="graph")
        assert_safe_metadata(self.parameters, path="parameters")
        return self

    @property
    def workflow_ref(self) -> str:
        """Exact workflow version reference of this call."""
        return f"{self.workflow_id}@{self.workflow_version}"


class ComfyUISubmission(_SeamModel):
    """Transport-owned acceptance token for one submitted ComfyUI prompt."""

    prompt_id: OpaqueId
    status: Literal["queued", "running"] = "queued"
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_metadata(self):
        assert_safe_metadata(self.metadata)
        return self


class ComfyUIOutputItem(_SeamModel):
    """One normalized ComfyUI output item declared by the transport."""

    kind: ComfyUIOutputKind
    filename: OpaqueId
    subfolder: str = ""
    item_type: OpaqueId = "output"
    url: str | None = None
    text: str | None = None
    name: OpaqueId | None = None

    @model_validator(mode="after")
    def validate_item(self):
        if self.kind == "text" and self.text is None and self.url is None:
            raise ValueError("ComfyUI text output items require text or a url")
        return self


class ComfyUIRawEvent(_SeamModel):
    """One ComfyUI-shaped event before Workbench normalization."""

    kind: ComfyUIRawEventKind
    node_id: str | None = None
    class_type: str | None = None
    value: int | None = None
    maximum: int | None = None
    items: tuple[ComfyUIOutputItem, ...] = ()
    message: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_event(self):
        assert_safe_metadata(self.metadata)
        return self


@runtime_checkable
class ComfyUITransport(Protocol):
    """The ComfyUI-facing boundary owned by transport adapters.

    Implementations own backend selection, HTTP/WebSocket details, prompt
    submission, history polling and output classification.  ``next_event``
    returning ``None`` means the ComfyUI stream finished without an explicit
    terminal event.
    """

    async def submit(self, call: ComfyUICall) -> ComfyUISubmission: ...

    async def next_event(self, submission: ComfyUISubmission) -> ComfyUIRawEvent | None: ...

    async def cancel(self, submission: ComfyUISubmission) -> bool: ...

    async def close(self, submission: ComfyUISubmission) -> None: ...


@dataclass
class _ExecutionState:
    request: ExecutionRequest
    call: ComfyUICall
    submission: ComfyUISubmission
    status: str = "running"
    sequence: int = 0
    outputs: list[ExecutionOutput] = field(default_factory=list)
    result: ExecutionResult | None = None
    cancel_event: ExecutionEvent | None = None
    wake: asyncio.Event = field(default_factory=asyncio.Event)
    terminal_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    cleaned: bool = False


class ComfyUIExecutor:
    """Adapt one ComfyUI workflow run to the generic Executor lifecycle."""

    executor_ref = COMFYUI_EXECUTOR_REF

    def __init__(
        self,
        *,
        transport: ComfyUITransport,
        workflow_resolver: WorkflowResolver,
        profile: ExecutionProfile | None = None,
        timeout_seconds: float | None = None,
        cancel_timeout_seconds: float | None = None,
    ):
        if not isinstance(transport, ComfyUITransport):
            raise TypeError("ComfyUIExecutor requires a ComfyUITransport")
        if not callable(workflow_resolver):
            raise TypeError("ComfyUIExecutor requires a workflow resolver")
        if profile is not None and profile.executor_ref != COMFYUI_EXECUTOR_REF:
            raise ValueError("ComfyUIExecutor requires a comfyui execution profile")
        if profile is not None:
            if timeout_seconds is not None and timeout_seconds != profile.timeout_seconds:
                raise ValueError("timeout_seconds must match the execution profile")
            if cancel_timeout_seconds is not None and cancel_timeout_seconds != profile.cancel_timeout_seconds:
                raise ValueError("cancel_timeout_seconds must match the execution profile")
        timeout_seconds = profile.timeout_seconds if profile is not None else (DEFAULT_COMFYUI_TIMEOUT_SECONDS if timeout_seconds is None else timeout_seconds)
        cancel_timeout_seconds = profile.cancel_timeout_seconds if profile is not None else (DEFAULT_COMFYUI_CANCEL_TIMEOUT_SECONDS if cancel_timeout_seconds is None else cancel_timeout_seconds)
        if timeout_seconds <= 0:
            raise ValueError("ComfyUI timeout_seconds must be positive")
        if cancel_timeout_seconds <= 0:
            raise ValueError("ComfyUI cancel_timeout_seconds must be positive")
        self._transport = transport
        self._workflow_resolver = workflow_resolver
        self._profile = profile
        self._timeout_seconds = timeout_seconds
        self._cancel_timeout_seconds = cancel_timeout_seconds
        self._prepared: dict[str, tuple[ExecutionRequest, ComfyUICall]] = {}
        self._states: dict[str, _ExecutionState] = {}

    async def prepare(self, request: ExecutionRequest) -> PreparedExecution:
        if request.execution_id in self._states:
            raise ComfyUIExecutorError(f"execution is already prepared: {request.execution_id}")
        if request.execution_id in self._prepared:
            raise ComfyUIExecutorError(f"execution is already prepared: {request.execution_id}")
        if self._profile is not None and request.execution_profile_ref not in {
            self._profile.id,
            f"{self._profile.id}@{self._profile.version}",
        }:
            raise ComfyUIExecutorError("execution request does not use the configured execution profile")
        call, workflow = self._build_call(request)
        self._prepared[request.execution_id] = (request, call)
        return PreparedExecution(
            execution_id=request.execution_id,
            executor_ref=self.executor_ref,
            metadata={
                "runtime_route": COMFYUI_RUNTIME_ROUTE,
                "workflow_ref": call.workflow_ref,
                "connection_ref": call.connection_ref or "",
                "input_roles": tuple(binding.role for binding in workflow.input_bindings),
            },
        )

    async def start(self, prepared: PreparedExecution) -> ExecutionHandle:
        self._require_prepared(prepared)
        entry = self._prepared.pop(prepared.execution_id, None)
        if entry is None:
            raise ComfyUIExecutorError(f"execution was not prepared: {prepared.execution_id}")
        request, call = entry
        try:
            submission = await self._within_timeout(self._transport.submit(call), self._timeout_seconds)
        except (ComfyUITransportError, asyncio.TimeoutError) as error:
            raise ComfyUIExecutorError(str(error)) from error
        if not isinstance(submission, ComfyUISubmission):
            raise ComfyUIExecutorError("comfyui transport returned an invalid submission")
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
                    event = self._terminal_event(state, "failed", "ComfyUI execution timed out")
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
                    event = self._terminal_event(state, "failed", "ComfyUI execution timed out")
                yield event
                break
            if wake_task in done:
                continue
            async with state.terminal_lock:
                if state.cancel_event is not None or state.result is not None:
                    continue
                if queue_task.exception() is not None:
                    error = queue_task.exception()
                    event = self._terminal_event(state, "failed", str(error) or "ComfyUI execution failed")
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
            except (ComfyUITransportError, asyncio.TimeoutError):
                return CancelResult(execution_id=handle.execution_id, accepted=False, status="unknown")
            if not accepted:
                return CancelResult(execution_id=handle.execution_id, accepted=False, status="unknown")
            state.status = "cancelled"
            state.result = ExecutionResult(execution_id=handle.execution_id, status="cancelled", outputs=tuple(state.outputs))
            state.cancel_event = self._event(state, "cancelled", "cancelled", message="ComfyUI execution cancelled")
        state.wake.set()
        return CancelResult(execution_id=handle.execution_id, accepted=True, status="cancelled")

    async def status(self, handle: ExecutionHandle) -> ExecutionStatusSnapshot:
        state = self._state(handle)
        status = state.result.status if state.result is not None else state.status
        return ExecutionStatusSnapshot(execution_id=handle.execution_id, status=status)

    async def result(self, handle: ExecutionHandle) -> ExecutionResult:
        state = self._state(handle)
        if state.result is None:
            raise ComfyUIExecutorError("comfyui execution has not reached a terminal state")
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
            metadata={"runtime_route": COMFYUI_RUNTIME_ROUTE},
        )

    def _build_call(self, request: ExecutionRequest) -> tuple[ComfyUICall, ComfyUIWorkflow]:
        reference = self._resolve_reference(request)
        workflow = self._workflow_resolver(reference)
        if workflow is None:
            raise ComfyUIExecutorError(f"comfyui workflow is not available: {reference.ref}")
        if workflow.id != reference.workflow_id or workflow.version != reference.version:
            raise ComfyUIExecutorError(f"comfyui workflow version mismatch: {reference.ref}")
        graph = self._inject_inputs(request, workflow)
        parameters = dict(self._profile.default_params) if self._profile is not None else {}
        parameters.update(request.config)
        connection_ref = self._config_value(request, "connection_ref")
        if not isinstance(connection_ref, str) or not connection_ref:
            connection_ref = self._profile.runtime_connection_ref if self._profile is not None else None
        call = ComfyUICall(
            execution_id=request.execution_id,
            idempotency_key=request.idempotency_key,
            workflow_id=workflow.id,
            workflow_version=workflow.version,
            connection_ref=connection_ref,
            graph=graph,
            inputs=request.inputs,
            parameters=parameters,
        )
        return call, workflow

    def _resolve_reference(self, request: ExecutionRequest) -> ComfyUIWorkflowRef:
        raw_reference = self._config_value(request, "workflow_ref")
        if raw_reference is None and self._profile is not None:
            raw_reference = self._profile.default_params.get("workflow_ref")
        if raw_reference is None:
            raise ComfyUIExecutorError("comfyui execution requires a workflow reference")
        try:
            return ComfyUIWorkflowRef.parse(raw_reference)
        except ValueError as error:
            raise ComfyUIExecutorError(str(error)) from error

    def _inject_inputs(self, request: ExecutionRequest, workflow: ComfyUIWorkflow) -> dict[str, Any]:
        graph = copy.deepcopy(dict(workflow.graph))
        bindings = {binding.role: binding for binding in workflow.input_bindings}
        supplied: set[str] = set()
        for item in request.inputs:
            role = self._role_for(request, item)
            binding = bindings.get(role)
            if binding is None:
                raise ComfyUIExecutorError(f"comfyui workflow has no input binding for role: {role}")
            node = graph.get(binding.node_id)
            if not isinstance(node, dict):
                raise ComfyUIExecutorError(f"comfyui workflow graph is missing node: {binding.node_id}")
            node_inputs = node.get("inputs")
            if node_inputs is None:
                node_inputs = {}
                node["inputs"] = node_inputs
            if not isinstance(node_inputs, dict):
                raise ComfyUIExecutorError(f"comfyui workflow node inputs are invalid: {binding.node_id}")
            node_inputs[binding.input_name] = item.value
            supplied.add(role)
        for binding in workflow.input_bindings:
            if binding.required and binding.role not in supplied:
                raise ComfyUIExecutorError(f"comfyui workflow is missing required input role: {binding.role}")
        return graph

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
        declared = ComfyUIExecutor._config_value(request, "input_roles")
        if isinstance(declared, dict) and item.name in declared:
            role = declared[item.name]
            if isinstance(role, str) and role:
                return role
        return item.name

    def _require_prepared(self, prepared: PreparedExecution) -> None:
        if prepared.executor_ref != self.executor_ref:
            raise ComfyUIExecutorError("prepared execution belongs to another executor")
        if prepared.execution_id in self._states:
            raise ComfyUIExecutorError(f"execution is already started: {prepared.execution_id}")

    def _state(self, handle: ExecutionHandle) -> _ExecutionState:
        if handle.executor_ref != self.executor_ref:
            raise ComfyUIExecutorError("execution handle belongs to another executor")
        try:
            return self._states[handle.execution_id]
        except KeyError as error:
            raise ComfyUIExecutorError(f"execution is not active: {handle.execution_id}") from error

    @staticmethod
    async def _within_timeout(awaitable, timeout: float):
        return await asyncio.wait_for(awaitable, timeout=timeout)

    def _map_event(self, state: _ExecutionState, raw: ComfyUIRawEvent) -> ExecutionEvent:
        outputs = self._outputs(state, raw)
        if raw.kind == "queued":
            return self._event(state, "progress", "running", message="ComfyUI prompt queued")
        if raw.kind == "executing":
            return self._event(state, "progress", "running", message=f"ComfyUI node {raw.node_id}", node=raw)
        if raw.kind == "progress":
            return self._event(state, "progress", "running", message=self._progress_message(raw), node=raw)
        if raw.kind == "output":
            return self._event(state, "partial_result", "running", message=raw.message, node=raw, outputs=outputs)
        if raw.kind == "completed":
            return self._terminal_event(state, "succeeded", raw.message, outputs)
        if raw.kind == "failed":
            return self._terminal_event(state, "failed", raw.message or "ComfyUI execution failed", outputs)
        return self._terminal_event(state, "cancelled", raw.message, outputs)

    def _outputs(self, state: _ExecutionState, raw: ComfyUIRawEvent) -> tuple[ExecutionOutput, ...]:
        if not raw.items:
            return ()
        outputs = []
        for item in raw.items:
            output = ExecutionOutput(name=item.name or f"{item.kind}.{len(state.outputs) + 1}", value=self._output_value(item))
            state.outputs.append(output)
            outputs.append(output)
        return tuple(outputs)

    @staticmethod
    def _output_value(item: ComfyUIOutputItem) -> Any:
        if item.kind == "text" and item.text is not None:
            return item.text
        reference: dict[str, Any] = {
            "kind": item.kind,
            "filename": item.filename,
            "subfolder": item.subfolder,
            "item_type": item.item_type,
        }
        if item.url is not None:
            reference["url"] = item.url
        return reference

    @staticmethod
    def _progress_message(raw: ComfyUIRawEvent) -> str:
        if raw.value is None:
            return "ComfyUI progress"
        if raw.maximum and raw.maximum > 0:
            percent = max(0, min(100, round(raw.value / raw.maximum * 100)))
            return f"ComfyUI progress {percent}%"
        return f"ComfyUI progress {raw.value}"

    def _event(self, state: _ExecutionState, kind, status, *, message=None, outputs=(), node=None):
        metadata: dict[str, Any] = {"runtime_route": COMFYUI_RUNTIME_ROUTE, "workflow_ref": state.call.workflow_ref}
        if node is not None:
            if node.node_id is not None:
                metadata["node_id"] = node.node_id
            if node.class_type is not None:
                metadata["class_type"] = node.class_type
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

    def _terminal_event(self, state: _ExecutionState, status, message, outputs=()):
        if status == "failed":
            state.status = "failed"
            state.result = ExecutionResult(
                execution_id=state.request.execution_id,
                status="failed",
                outputs=tuple(state.outputs),
                error=message or "ComfyUI execution failed",
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
        return self._event(state, kind, status, message=message, outputs=outputs)

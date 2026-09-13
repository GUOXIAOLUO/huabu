"""Thin Codex Harness adapter for the provider-neutral Executor contract."""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from workbench.domain.execution import (
    CancelResult,
    ExecutionEvent,
    ExecutionHandle,
    ExecutionInput,
    ExecutionOutput,
    ExecutionRequest,
    ExecutionResult,
    ExecutionStatusSnapshot,
    ExecutorHealth,
    ExecutionProfile,
    PreparedExecution,
)

from .bridge import CodexBridge, CodexBridgeError, HarnessLaunchPolicy
from .events import RuntimeEvent
from .protocol import ThreadStartResult, TurnStartResult


CODEX_HARNESS_EXECUTOR_REF = "codex-harness"


class CodexHarnessExecutorError(RuntimeError):
    """A bounded failure at the Codex-to-Executor adapter boundary."""


BridgeFactory = Callable[[HarnessLaunchPolicy], CodexBridge]


@dataclass
class _ExecutionState:
    request: ExecutionRequest
    bridge: CodexBridge
    thread_id: str
    turn_id: str
    status: str = "running"
    sequence: int = 0
    outputs: list[ExecutionOutput] = field(default_factory=list)
    result: ExecutionResult | None = None
    cancel_event: ExecutionEvent | None = None
    wake: asyncio.Event = field(default_factory=asyncio.Event)
    terminal_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    cleaned: bool = False


class CodexHarnessExecutor:
    """Adapt one Codex Harness turn to the generic Executor lifecycle.

    The bridge owns protocol transport, authentication, sandbox policy and
    Codex's internal loop.  This adapter only owns lifecycle translation for a
    Workbench execution and never selects a replacement model or executor.
    """

    executor_ref = CODEX_HARNESS_EXECUTOR_REF

    def __init__(
        self,
        *,
        workspace_root: str | Path,
        profile: ExecutionProfile | None = None,
        timeout_seconds: float | None = None,
        cancel_timeout_seconds: float | None = None,
        bridge_factory: BridgeFactory = CodexBridge,
    ):
        if profile is not None and profile.executor_ref != CODEX_HARNESS_EXECUTOR_REF:
            raise ValueError("CodexHarnessExecutor requires a codex-harness execution profile")
        if profile is not None:
            if timeout_seconds is not None and timeout_seconds != profile.timeout_seconds:
                raise ValueError("timeout_seconds must match the execution profile")
            if cancel_timeout_seconds is not None and cancel_timeout_seconds != profile.cancel_timeout_seconds:
                raise ValueError("cancel_timeout_seconds must match the execution profile")
        timeout_seconds = profile.timeout_seconds if profile is not None else (300.0 if timeout_seconds is None else timeout_seconds)
        cancel_timeout_seconds = profile.cancel_timeout_seconds if profile is not None else (10.0 if cancel_timeout_seconds is None else cancel_timeout_seconds)
        if timeout_seconds <= 0:
            raise ValueError("Codex Harness timeout_seconds must be positive")
        if cancel_timeout_seconds <= 0:
            raise ValueError("Codex Harness cancel_timeout_seconds must be positive")
        self._workspace_root = Path(workspace_root)
        self._timeout_seconds = timeout_seconds
        self._cancel_timeout_seconds = cancel_timeout_seconds
        self._bridge_factory = bridge_factory
        self._profile = profile
        self._prepared: dict[str, ExecutionRequest] = {}
        self._states: dict[str, _ExecutionState] = {}

    async def prepare(self, request: ExecutionRequest) -> PreparedExecution:
        if request.execution_id in self._states:
            raise CodexHarnessExecutorError(f"execution is already prepared: {request.execution_id}")
        if request.execution_id in self._prepared:
            raise CodexHarnessExecutorError(f"execution is already prepared: {request.execution_id}")
        if self._profile is not None and request.execution_profile_ref not in {
            self._profile.id,
            f"{self._profile.id}@{self._profile.version}",
        }:
            raise CodexHarnessExecutorError("execution request does not use the configured execution profile")
        self._prepared[request.execution_id] = request
        return PreparedExecution(
            execution_id=request.execution_id,
            executor_ref=self.executor_ref,
            metadata={"sandbox": "read-only", "protocol": "v2"},
        )

    async def start(self, prepared: PreparedExecution) -> ExecutionHandle:
        self._require_prepared(prepared)
        request = self._prepared.pop(prepared.execution_id, None)
        if request is None:
            raise CodexHarnessExecutorError(f"execution was not prepared: {prepared.execution_id}")
        cwd = request.config.get("cwd")
        requested_thread = request.config.get("thread_id")
        if cwd is not None and not isinstance(cwd, str):
            raise CodexHarnessExecutorError("Codex execution cwd must be a string")
        if requested_thread is not None and not isinstance(requested_thread, str):
            raise CodexHarnessExecutorError("Codex thread_id must be a string")
        policy = HarnessLaunchPolicy(
            workspace_root=self._workspace_root,
            timeout_seconds=self._timeout_seconds,
        )
        bridge = self._bridge_factory(policy)
        try:
            await self._within_timeout(bridge.start(), self._timeout_seconds)
            thread: ThreadStartResult = await self._within_timeout(
                bridge.resume_thread(requested_thread, cwd) if requested_thread else bridge.create_thread(cwd),
                self._timeout_seconds,
            )
            prompt = self._prompt_text(request)
            turn: TurnStartResult = await self._within_timeout(
                bridge.start_turn(thread.thread.id, prompt, cwd),
                self._timeout_seconds,
            )
        except (CodexBridgeError, asyncio.TimeoutError, ValueError) as error:
            await bridge.shutdown()
            raise CodexHarnessExecutorError(str(error)) from error
        state = _ExecutionState(
            request=request,
            bridge=bridge,
            thread_id=thread.thread.id,
            turn_id=turn.turn.id,
        )
        self._states[request.execution_id] = state
        return ExecutionHandle(execution_id=request.execution_id, executor_ref=self.executor_ref)

    async def stream(self, handle: ExecutionHandle):
        state = self._state(handle)
        deadline = asyncio.get_running_loop().time() + self._timeout_seconds
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
                    event = self._terminal_event(state, "failed", "Codex Harness execution timed out")
                yield event
                break
            queue_task = asyncio.create_task(state.bridge.events.get())
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
                    try:
                        await self._within_timeout(
                            state.bridge.interrupt_turn(state.thread_id, state.turn_id),
                            self._cancel_timeout_seconds,
                        )
                    except (CodexBridgeError, asyncio.TimeoutError):
                        pass
                    if state.cancel_event is not None or state.result is not None:
                        continue
                    event = self._terminal_event(state, "failed", "Codex Harness execution timed out")
                yield event
                break
            if wake_task in done:
                continue
            runtime_event = queue_task.result()
            async with state.terminal_lock:
                event = self._map_event(state, runtime_event)
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
                await self._within_timeout(
                    state.bridge.interrupt_turn(state.thread_id, state.turn_id),
                    self._cancel_timeout_seconds,
                )
            except (CodexBridgeError, asyncio.TimeoutError):
                return CancelResult(execution_id=handle.execution_id, accepted=False, status="unknown")
            if state.result is not None:
                return CancelResult(
                    execution_id=handle.execution_id,
                    accepted=state.result.status == "cancelled",
                    status=state.result.status,
                )
            state.status = "cancelled"
            state.result = ExecutionResult(execution_id=handle.execution_id, status="cancelled", outputs=tuple(state.outputs))
            state.cancel_event = self._event(state, "cancelled", "cancelled", message="Codex execution cancelled")
        state.wake.set()
        return CancelResult(execution_id=handle.execution_id, accepted=True, status="cancelled")

    async def status(self, handle: ExecutionHandle) -> ExecutionStatusSnapshot:
        state = self._state(handle)
        status = state.result.status if state.result is not None else state.status
        return ExecutionStatusSnapshot(execution_id=handle.execution_id, status=status)

    async def result(self, handle: ExecutionHandle) -> ExecutionResult:
        state = self._state(handle)
        if state.result is None:
            raise CodexHarnessExecutorError("Codex execution has not reached a terminal state")
        return state.result

    async def cleanup(self, handle: ExecutionHandle) -> None:
        state = self._state(handle)
        if state.cleaned:
            return
        state.cleaned = True
        await state.bridge.shutdown()
        self._states.pop(handle.execution_id, None)

    async def health(self) -> ExecutorHealth:
        return ExecutorHealth(
            executor_ref=self.executor_ref,
            status="healthy",
            metadata={"protocol": "v2", "sandbox": "read-only"},
        )

    def _require_prepared(self, prepared: PreparedExecution) -> None:
        if prepared.executor_ref != self.executor_ref:
            raise CodexHarnessExecutorError("prepared execution belongs to another executor")
        if prepared.execution_id in self._states:
            raise CodexHarnessExecutorError(f"execution is already started: {prepared.execution_id}")

    def _state(self, handle: ExecutionHandle) -> _ExecutionState:
        if handle.executor_ref != self.executor_ref:
            raise CodexHarnessExecutorError("execution handle belongs to another executor")
        try:
            return self._states[handle.execution_id]
        except KeyError as error:
            raise CodexHarnessExecutorError(f"execution is not active: {handle.execution_id}") from error

    @staticmethod
    async def _within_timeout(awaitable, timeout: float):
        return await asyncio.wait_for(awaitable, timeout=timeout)

    @staticmethod
    def _prompt_text(request: ExecutionRequest) -> str:
        configured = request.config.get("prompt")
        if isinstance(configured, str):
            return configured
        if len(request.inputs) == 1 and isinstance(request.inputs[0].value, str):
            return request.inputs[0].value
        values = {item.name: item.value for item in request.inputs}
        return json.dumps(values, ensure_ascii=False, default=str)

    def _map_event(self, state: _ExecutionState, runtime_event: RuntimeEvent) -> ExecutionEvent:
        payload = dict(runtime_event.payload)
        message = payload.get("message") or payload.get("reason") or payload.get("error")
        outputs: tuple[ExecutionOutput, ...] = ()
        if runtime_event.kind == "output" and isinstance(payload.get("text"), str):
            output = ExecutionOutput(name="text", value=payload["text"])
            state.outputs.append(output)
            outputs = (output,)
        if runtime_event.operation == "turn" and runtime_event.status == "started":
            return self._event(state, "started", "running", message=message, outputs=outputs)
        if runtime_event.operation == "turn" and runtime_event.status == "completed":
            state.status = "succeeded"
            state.result = ExecutionResult(execution_id=state.request.execution_id, status="succeeded", outputs=tuple(state.outputs))
            return self._event(state, "completed", "succeeded", message=message, outputs=outputs)
        if runtime_event.operation == "turn" and runtime_event.status == "cancelled":
            return self._terminal_event(state, "cancelled", message or "Codex execution cancelled")
        if runtime_event.kind == "error":
            return self._terminal_event(state, "failed", message or "Codex execution failed")
        if runtime_event.kind == "output":
            return self._event(state, "partial_result", "running", message=message, outputs=outputs)
        return self._event(state, "progress", "running", message=message, outputs=outputs)

    def _event(self, state: _ExecutionState, kind, status, *, message=None, outputs=()):
        event = ExecutionEvent(
            execution_id=state.request.execution_id,
            sequence=state.sequence,
            kind=kind,
            status=status,
            outputs=outputs,
            message=message if isinstance(message, str) else None,
            metadata={"operation": "turn" if kind in {"started", "completed"} else "runtime"},
        )
        state.sequence += 1
        return event

    def _terminal_event(self, state: _ExecutionState, status, message):
        if status == "failed":
            state.status = "failed"
            state.result = ExecutionResult(execution_id=state.request.execution_id, status="failed", outputs=tuple(state.outputs), error=message)
            kind = "failed"
        else:
            state.status = "cancelled"
            state.result = ExecutionResult(execution_id=state.request.execution_id, status="cancelled", outputs=tuple(state.outputs))
            kind = "cancelled"
        return self._event(state, kind, status, message=message, outputs=())

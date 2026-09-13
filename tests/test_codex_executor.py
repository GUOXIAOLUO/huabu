import asyncio
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

from workbench.application.execution_event_service import ExecutionEventService
from workbench.application.execution_service import ExecutionControlRegistry, ExecutionService
from workbench.codex.executor import CodexHarnessExecutor
from workbench.codex.protocol import InitializeResult, ThreadStartResult, TurnStartResult
from workbench.codex.events import RuntimeEvent
from workbench.domain.execution import ExecutionInput, ExecutionInputProjection, ExecutionPolicy, ExecutionProfile, ExecutionRequest, ExecutionRun
from workbench.domain.project.models import ProjectRecord
from workbench.repositories.execution_attempt_repository import SqliteExecutionAttemptRepository
from workbench.repositories.execution_event_repository import SqliteExecutionEventRepository
from workbench.repositories.execution_run_repository import SqliteExecutionRunRepository
from workbench.repositories.sqlite_project_canvas_repository import SqliteProjectCanvasRepository


class FakeCodexBridge:
    def __init__(self, policy, *, emit_events=True):
        self.policy = policy
        self.emit_events = emit_events
        self.events = asyncio.Queue()
        self.resumed_thread = None
        self.interrupts = []
        self.shutdown_calls = 0

    async def start(self):
        return InitializeResult(protocolVersion="2")

    async def create_thread(self, cwd=None):
        return ThreadStartResult.model_validate({"thread": {"id": "thread-1"}})

    async def resume_thread(self, thread_id, cwd=None):
        self.resumed_thread = thread_id
        return ThreadStartResult.model_validate({"thread": {"id": thread_id}})

    async def start_turn(self, thread_id, text, cwd=None):
        self.prompt = text
        if self.emit_events:
            await self.events.put(RuntimeEvent("lifecycle", "started", "turn", {"turn": {"id": "turn-1"}}))
            await self.events.put(RuntimeEvent("output", "completed", "item", {"item": {"id": "item-1", "type": "agentMessage"}, "text": "answer"}))
            await self.events.put(RuntimeEvent("lifecycle", "completed", "turn", {"turn": {"id": "turn-1"}}))
        return TurnStartResult.model_validate({"turn": {"id": "turn-1"}})

    async def interrupt_turn(self, thread_id, turn_id):
        self.interrupts.append((thread_id, turn_id))
        return {}

    async def shutdown(self):
        self.shutdown_calls += 1

    async def health(self):
        return {"running": True, "protocol": "2"}


class BlockingStartBridge(FakeCodexBridge):
    def __init__(self, policy, started, release):
        super().__init__(policy, emit_events=False)
        self.started = started
        self.release = release

    async def start_turn(self, thread_id, text, cwd=None):
        self.started.set()
        await self.release.wait()
        return await super().start_turn(thread_id, text, cwd)


class TimeoutRaceBridge(FakeCodexBridge):
    def __init__(self, policy, started, release):
        super().__init__(policy, emit_events=False)
        self.started = started
        self.release = release
        self.interrupt_calls = 0

    async def interrupt_turn(self, thread_id, turn_id):
        self.interrupt_calls += 1
        if self.interrupt_calls == 1:
            self.started.set()
            await self.release.wait()
        return await super().interrupt_turn(thread_id, turn_id)


class CodexHarnessExecutorTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.bridges = []

    def executor(self, *, timeout_seconds=1, emit_events=True):
        def factory(policy):
            bridge = FakeCodexBridge(policy, emit_events=emit_events)
            self.bridges.append(bridge)
            return bridge

        return CodexHarnessExecutor(
            workspace_root=tempfile.gettempdir(),
            timeout_seconds=timeout_seconds,
            cancel_timeout_seconds=0.1,
            bridge_factory=factory,
        )

    async def test_maps_bridge_events_and_preserves_read_only_policy(self):
        executor = self.executor()
        request = ExecutionRequest(
            execution_id="execution-1",
            idempotency_key="idempotency-1",
            inputs=(ExecutionInput(name="prompt", value="hello"),),
            config={"prompt": "hello", "thread_id": "thread-existing"},
        )
        prepared = await executor.prepare(request)
        handle = await executor.start(prepared)
        events = [event async for event in executor.stream(handle)]
        result = await executor.result(handle)
        await executor.cleanup(handle)

        bridge = self.bridges[0]
        self.assertEqual([event.kind for event in events], ["started", "partial_result", "completed"])
        self.assertEqual(result.outputs[0].value, "answer")
        self.assertEqual(bridge.resumed_thread, "thread-existing")
        self.assertEqual(bridge.policy.thread_options()["sandbox"], "read-only")
        self.assertEqual(bridge.policy.turn_options()["sandboxPolicy"], {"type": "readOnly", "networkAccess": False})
        self.assertEqual(bridge.shutdown_calls, 1)

    async def test_cancel_is_explicit_and_repeatable(self):
        executor = self.executor(emit_events=False)
        request = ExecutionRequest(execution_id="execution-2", idempotency_key="idempotency-2")
        handle = await executor.start(await executor.prepare(request))

        first = await executor.cancel(handle)
        second = await executor.cancel(handle)
        status = await executor.status(handle)

        self.assertEqual((first.accepted, first.status, second.status, status.status), (True, "cancelled", "cancelled", "cancelled"))
        self.assertEqual(self.bridges[0].interrupts, [("thread-1", "turn-1")])
        await executor.cleanup(handle)

    async def test_cancel_interrupts_a_waiting_stream(self):
        executor = self.executor(emit_events=False)
        request = ExecutionRequest(execution_id="execution-cancel", idempotency_key="idempotency-cancel")
        handle = await executor.start(await executor.prepare(request))
        stream = executor.stream(handle).__aiter__()
        waiting = asyncio.create_task(stream.__anext__())
        await asyncio.sleep(0)

        await executor.cancel(handle)
        event = await asyncio.wait_for(waiting, timeout=0.2)

        self.assertEqual((event.kind, event.status), ("cancelled", "cancelled"))
        await executor.cleanup(handle)

    async def test_cancel_wakes_stream_even_when_bridge_event_queue_is_full(self):
        def factory(policy):
            bridge = FakeCodexBridge(policy, emit_events=False)
            bridge.events = asyncio.Queue(maxsize=1)
            return bridge

        executor = CodexHarnessExecutor(
            workspace_root=tempfile.gettempdir(), bridge_factory=factory, timeout_seconds=0.2,
        )
        request = ExecutionRequest(execution_id="execution-full", idempotency_key="idempotency-full")
        handle = await executor.start(await executor.prepare(request))
        bridge = executor._states[handle.execution_id].bridge
        await bridge.events.put(RuntimeEvent("progress", "running", "runtime", {"progress": 1}))
        stream = executor.stream(handle).__aiter__()
        await stream.__anext__()
        waiting = asyncio.create_task(stream.__anext__())
        await asyncio.sleep(0)

        await executor.cancel(handle)
        event = await asyncio.wait_for(waiting, timeout=0.2)

        self.assertEqual((event.kind, event.status), ("cancelled", "cancelled"))
        await executor.cleanup(handle)

    async def test_stream_timeout_becomes_typed_failed_result(self):
        executor = self.executor(timeout_seconds=0.02, emit_events=False)
        request = ExecutionRequest(execution_id="execution-3", idempotency_key="idempotency-3")
        handle = await executor.start(await executor.prepare(request))

        events = [event async for event in executor.stream(handle)]
        result = await executor.result(handle)

        self.assertEqual((events[-1].kind, events[-1].status, result.status), ("failed", "failed", "failed"))
        self.assertIn("timed out", result.error)
        self.assertEqual(self.bridges[0].interrupts, [("thread-1", "turn-1")])
        await executor.cleanup(handle)

    async def test_timeout_interrupt_owns_terminal_decision_against_cancel(self):
        started = asyncio.Event()
        release = asyncio.Event()
        bridges = []

        def factory(policy):
            bridge = TimeoutRaceBridge(policy, started, release)
            bridges.append(bridge)
            return bridge

        executor = CodexHarnessExecutor(
            workspace_root=tempfile.gettempdir(),
            timeout_seconds=0.01,
            cancel_timeout_seconds=0.2,
            bridge_factory=factory,
        )
        request = ExecutionRequest(execution_id="execution-timeout-race", idempotency_key="idempotency-timeout-race")
        handle = await executor.start(await executor.prepare(request))
        stream = executor.stream(handle).__aiter__()
        streaming = asyncio.create_task(stream.__anext__())
        await asyncio.wait_for(started.wait(), timeout=0.2)

        cancelling = asyncio.create_task(executor.cancel(handle))
        with self.assertRaises(asyncio.TimeoutError):
            await asyncio.wait_for(asyncio.shield(cancelling), timeout=0.05)
        cancel_result = await cancelling
        release.set()
        event = await asyncio.wait_for(streaming, timeout=0.2)

        self.assertEqual((cancel_result.accepted, cancel_result.status, event.kind, event.status), (False, "failed", "failed", "failed"))
        self.assertEqual((await executor.result(handle)).status, "failed")
        self.assertEqual(bridges[0].interrupt_calls, 1)
        await executor.cleanup(handle)

    async def test_timeout_terminal_state_cannot_be_overwritten_by_delayed_cancel(self):
        started = asyncio.Event()
        release_timeout = asyncio.Event()
        bridges = []

        def factory(policy):
            bridge = TimeoutRaceBridge(policy, started, release_timeout)
            bridges.append(bridge)
            return bridge

        executor = CodexHarnessExecutor(
            workspace_root=tempfile.gettempdir(),
            timeout_seconds=0.01,
            cancel_timeout_seconds=0.2,
            bridge_factory=factory,
        )
        request = ExecutionRequest(execution_id="execution-timeout-wins", idempotency_key="idempotency-timeout-wins")
        handle = await executor.start(await executor.prepare(request))
        stream = executor.stream(handle).__aiter__()
        streaming = asyncio.create_task(stream.__anext__())
        await asyncio.wait_for(started.wait(), timeout=0.2)
        cancelling = asyncio.create_task(executor.cancel(handle))

        release_timeout.set()
        timeout_event = await asyncio.wait_for(streaming, timeout=0.2)
        self.assertEqual((timeout_event.kind, timeout_event.status), ("failed", "failed"))

        cancel_result = await cancelling
        self.assertEqual((cancel_result.accepted, cancel_result.status), (False, "failed"))
        self.assertEqual((await executor.result(handle)).status, "failed")
        self.assertEqual(bridges[0].interrupt_calls, 1)
        await executor.cleanup(handle)

    def test_profile_is_the_timeout_and_executor_identity_authority(self):
        profile = ExecutionProfile(
            id="profile-1", version=1, name="Codex", executor_ref="codex-harness",
            timeout_seconds=0.25, cancel_timeout_seconds=0.1,
        )
        configured = CodexHarnessExecutor(
            workspace_root=tempfile.gettempdir(), profile=profile, bridge_factory=lambda policy: FakeCodexBridge(policy)
        )
        self.assertEqual((configured._timeout_seconds, configured._cancel_timeout_seconds), (0.25, 0.1))
        with self.assertRaises(ValueError):
            CodexHarnessExecutor(workspace_root=tempfile.gettempdir(), profile=profile, timeout_seconds=1)


class CodexHarnessExecutionServiceTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.database = Path(self.temp.name) / "workbench.sqlite3"
        self.now = datetime(2026, 9, 12, tzinfo=UTC)
        SqliteProjectCanvasRepository(self.database, clock=lambda: self.now).create_project(ProjectRecord(
            id="project-1", name="Project", workspace_id="local", created_by="owner",
            created_at=self.now, updated_at=self.now,
        ))
        self.runs = SqliteExecutionRunRepository(self.database, clock=lambda: self.now)
        self.attempts = SqliteExecutionAttemptRepository(self.database, clock=lambda: self.now)
        self.events = ExecutionEventService(
            SqliteExecutionEventRepository(self.database, clock=lambda: self.now),
            actor_id="owner",
            id_factory=iter(["event-1", "event-2", "event-3"]).__next__,
            clock=lambda: self.now,
        )

    def tearDown(self):
        self.temp.cleanup()

    async def test_generic_task_runs_through_execution_service_and_persists_lifecycle(self):
        run = ExecutionRun(
            id="run-1", project_id="project-1", task_id="task-1", execution_profile_ref="profile@1",
            policy=ExecutionPolicy(),
            input_projection=ExecutionInputProjection(inputs=[{
                "input_id": "input-1", "binding_id": "binding-1", "target": "task.prompt",
                "role": "prompt", "order": 0, "source_type": "literal", "source_ref": "literal-1",
                "value": "hello", "source_snapshot": "hello",
            }]),
            created_at=self.now,
        )
        self.runs.create(run, actor_id="owner")
        executor = CodexHarnessExecutor(
            workspace_root=self.temp.name,
            bridge_factory=lambda policy: FakeCodexBridge(policy),
        )
        service = ExecutionService(
            self.runs,
            self.attempts,
            actor_id="owner",
            event_service=self.events,
            id_factory=iter(["attempt-1", "idempotency-1"]).__next__,
            clock=lambda: self.now,
        )

        result = await service.execute_run("run-1", executor=executor)

        self.assertEqual((result.status, result.outputs[0].value), ("succeeded", "answer"))
        self.assertEqual(self.runs.get("run-1", actor_id="owner").status, "succeeded")
        attempt = self.attempts.get("attempt-1", actor_id="owner")
        self.assertEqual((attempt.status, attempt.summary["output_count"]), ("succeeded", 1))
        persisted = self.events.stream("run-1")
        self.assertEqual([event.event_type for event in persisted], ["started", "partial_result", "completed"])

    async def test_execution_service_cancel_uses_the_active_codex_handle(self):
        run = ExecutionRun(
            id="run-cancel", project_id="project-1", task_id="task-cancel", execution_profile_ref="profile@1",
            policy=ExecutionPolicy(),
            input_projection=ExecutionInputProjection(inputs=[{
                "input_id": "input-1", "binding_id": "binding-1", "target": "task.prompt",
                "role": "prompt", "order": 0, "source_type": "literal", "source_ref": "literal-1",
                "value": "hello", "source_snapshot": "hello",
            }]),
            created_at=self.now,
        )
        self.runs.create(run, actor_id="owner")
        bridges = []

        def factory(policy):
            bridge = FakeCodexBridge(policy, emit_events=False)
            bridges.append(bridge)
            return bridge

        executor = CodexHarnessExecutor(workspace_root=self.temp.name, bridge_factory=factory)
        service = ExecutionService(
            self.runs,
            self.attempts,
            actor_id="owner",
            id_factory=iter(["attempt-cancel", "idempotency-cancel"]).__next__,
            clock=lambda: self.now,
        )
        running = asyncio.create_task(service.execute("run-cancel", executor=executor))
        for _ in range(20):
            if "attempt-cancel" in service._active_controls:
                break
            await asyncio.sleep(0)

        cancelled = await service.cancel_run("run-cancel")
        result = await running

        self.assertEqual((cancelled.status, result.status), ("cancelled", "cancelled"))
        self.assertEqual(self.attempts.get("attempt-cancel", actor_id="owner").status, "cancelled")
        self.assertEqual(bridges[0].interrupts, [("thread-1", "turn-1")])

    async def test_execution_service_cancel_is_safe_before_codex_handle_exists(self):
        run = ExecutionRun(
            id="run-starting", project_id="project-1", task_id="task-starting", execution_profile_ref="profile@1",
            policy=ExecutionPolicy(),
            input_projection=ExecutionInputProjection(inputs=[]),
            created_at=self.now,
        )
        self.runs.create(run, actor_id="owner")
        started = asyncio.Event()
        release = asyncio.Event()
        bridges = []

        def factory(policy):
            bridge = BlockingStartBridge(policy, started, release)
            bridges.append(bridge)
            return bridge

        executor = CodexHarnessExecutor(workspace_root=self.temp.name, bridge_factory=factory)
        service = ExecutionService(
            self.runs,
            self.attempts,
            actor_id="owner",
            id_factory=iter(["attempt-starting", "idempotency-starting"]).__next__,
            clock=lambda: self.now,
        )
        running = asyncio.create_task(service.execute("run-starting", executor=executor))
        await asyncio.wait_for(started.wait(), timeout=0.2)
        cancelled = await service.cancel_run("run-starting")
        release.set()
        result = await running

        self.assertEqual((cancelled.status, result.status), ("cancelled", "cancelled"))
        self.assertEqual(self.attempts.get("attempt-starting", actor_id="owner").status, "cancelled")
        self.assertEqual(bridges[0].interrupts, [("thread-1", "turn-1")])

    async def test_request_scoped_services_share_active_controls_for_cancel(self):
        run = ExecutionRun(
            id="run-shared", project_id="project-1", task_id="task-shared", execution_profile_ref="profile@1",
            policy=ExecutionPolicy(), input_projection=ExecutionInputProjection(inputs=[]), created_at=self.now,
        )
        self.runs.create(run, actor_id="owner")
        bridges = []

        def factory(policy):
            bridge = FakeCodexBridge(policy, emit_events=False)
            bridges.append(bridge)
            return bridge

        executor = CodexHarnessExecutor(workspace_root=self.temp.name, bridge_factory=factory)
        registry = ExecutionControlRegistry()
        running_service = ExecutionService(
            self.runs, self.attempts, actor_id="owner", control_registry=registry,
            id_factory=iter(["attempt-shared", "idempotency-shared"]).__next__, clock=lambda: self.now,
        )
        request_service = ExecutionService(
            self.runs, self.attempts, actor_id="owner", control_registry=registry, clock=lambda: self.now,
        )
        running = asyncio.create_task(running_service.execute("run-shared", executor=executor))
        for _ in range(20):
            if "attempt-shared" in registry:
                break
            await asyncio.sleep(0)

        cancelled = await request_service.cancel_run("run-shared")
        result = await running

        self.assertEqual((cancelled.status, result.status), ("cancelled", "cancelled"))
        self.assertEqual(bridges[0].interrupts, [("thread-1", "turn-1")])


if __name__ == "__main__":
    unittest.main()

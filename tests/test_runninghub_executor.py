"""Focused tests for the R8-14 RunningHubExecutor route."""

import ast
import asyncio
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

from workbench.application.execution_event_service import ExecutionEventService
from workbench.application.execution_service import ExecutionService
from workbench.application.executor_registry import ExecutorRegistration, ExecutorRegistry
from workbench.domain.execution import (
    ExecutionHandle,
    ExecutionInput,
    ExecutionInputProjection,
    ExecutionPolicy,
    ExecutionProfile,
    ExecutionRequest,
    ExecutionRun,
    Executor,
)
from workbench.domain.project.models import ProjectRecord
from workbench.repositories.execution_attempt_repository import SqliteExecutionAttemptRepository
from workbench.repositories.execution_event_repository import SqliteExecutionEventRepository
from workbench.repositories.execution_run_repository import SqliteExecutionRunRepository
from workbench.repositories.sqlite_project_canvas_repository import SqliteProjectCanvasRepository
from workbench.runninghub import (
    RUNNINGHUB_EXECUTOR_REF,
    RunningHubCall,
    RunningHubExecutor,
    RunningHubExecutorError,
    RunningHubNodeBinding,
    RunningHubOutputItem,
    RunningHubRawEvent,
    RunningHubRoute,
    RunningHubRouteRef,
    RunningHubSubmission,
    RunningHubTransportError,
)


FORBIDDEN_PROVIDER_SDK_IMPORTS = (
    "openai",
    "anthropic",
    "httpx",
    "requests",
    "boto3",
    "cohere",
    "replicate",
    "together",
    "mistralai",
    "google.generativeai",
    "urllib",
    "http.client",
    "socket",
)
# DoD: RunningHub must be an executor route, not a Canvas runtime owner.
FORBIDDEN_BOUNDARY_MARKERS = ("canvas", "legacy")


def _imported_modules(path: Path, root: Path) -> set[str]:
    """Absolute dotted module names referenced by imports in one file."""
    package_parts = path.parent.relative_to(root).parts
    modules: set[str] = set()
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
            if node.level:
                base = package_parts[: len(package_parts) - (node.level - 1)] if node.level > 1 else package_parts
                modules.add(".".join([*base, node.module]))
    return modules


def sample_route(**overrides):
    payload = {
        "kind": "ai_app",
        "route_id": "webapp-1",
        "version": 2,
        "title": "Poster generator",
        "node_bindings": (
            RunningHubNodeBinding(role="prompt", node_id="3", field_name="text"),
            RunningHubNodeBinding(role="seed", node_id="5", field_name="seed", required=False),
        ),
    }
    payload.update(overrides)
    return RunningHubRoute(**payload)


class FakeRunningHubTransport:
    """Minimal RunningHub-facing transport double."""

    def __init__(self, events=(), *, fail_submit=False, accept_cancel=True, hang=False):
        self.calls: list[RunningHubCall] = []
        self.events = list(events)
        self.fail_submit = fail_submit
        self.accept_cancel = accept_cancel
        self.hang = hang
        self.release = asyncio.Event()
        self.cancel_calls = 0
        self.closed = 0

    async def submit(self, call):
        self.calls.append(call)
        if self.fail_submit:
            raise RunningHubTransportError("runninghub rejected the task")
        return RunningHubSubmission(task_id=f"task-{len(self.calls)}")

    async def next_event(self, submission):
        if self.hang:
            await self.release.wait()
        if not self.events:
            return None
        return self.events.pop(0)

    async def cancel(self, submission):
        self.cancel_calls += 1
        return self.accept_cancel

    async def close(self, submission):
        self.closed += 1


class RunningHubExecutorRouteTests(unittest.IsolatedAsyncioTestCase):
    def executor(self, *, route=None, transport=None, profile=None, timeout_seconds=1.0):
        resolved = route if route is not None else sample_route()
        self.transport = transport if transport is not None else FakeRunningHubTransport()
        budgets = {} if profile is not None else {"timeout_seconds": timeout_seconds, "cancel_timeout_seconds": 0.1}
        return RunningHubExecutor(
            transport=self.transport,
            route_resolver=lambda ref: resolved if ref.ref == resolved.ref.ref else None,
            profile=profile,
            **budgets,
        )

    def request(self, **overrides):
        payload = {
            "execution_id": "execution-1",
            "idempotency_key": "idempotency-1",
            "inputs": (ExecutionInput(name="prompt", value="a poster"),),
            "config": {"route_ref": "ai_app:webapp-1@2"},
        }
        payload.update(overrides)
        return ExecutionRequest(**payload)

    async def test_route_and_profile_references_are_resolved(self):
        profile = ExecutionProfile(
            id="profile-rh", version=1, name="RunningHub", executor_ref=RUNNINGHUB_EXECUTOR_REF,
            runtime_connection_ref="runninghub-openapi", default_params={"route_ref": "ai_app:webapp-1@2"},
        )
        executor = self.executor(profile=profile)
        request = self.request(execution_profile_ref="profile-rh@1", config={})

        prepared = await executor.prepare(request)
        handle = await executor.start(prepared)
        call = self.transport.calls[0]

        self.assertEqual(prepared.executor_ref, RUNNINGHUB_EXECUTOR_REF)
        self.assertEqual(call.route_ref, "ai_app:webapp-1@2")
        self.assertEqual(call.connection_ref, "runninghub-openapi")
        self.assertEqual(prepared.metadata["route_ref"], "ai_app:webapp-1@2")
        self.assertEqual(prepared.metadata["input_roles"], ("prompt", "seed"))
        self.assertEqual(
            [(entry.node_id, entry.field_name, entry.value) for entry in call.node_info],
            [("3", "text", "a poster")],
        )
        self.assertEqual(handle.execution_id, request.execution_id)

    async def test_missing_route_reference_is_rejected(self):
        executor = self.executor()

        with self.assertRaises(RunningHubExecutorError) as caught:
            await executor.prepare(self.request(config={}))
        self.assertIn("route reference", str(caught.exception))
        self.assertEqual(self.transport.calls, [])

    def test_route_reference_rules_are_strict(self):
        self.assertEqual(RunningHubRouteRef.parse("workflow:wf-9@4").ref, "workflow:wf-9@4")
        with self.assertRaises(ValueError):
            RunningHubRouteRef.parse("ai_app:webapp-1")
        with self.assertRaises(ValueError):
            RunningHubRouteRef.parse("webapp-1@2")
        with self.assertRaises(ValueError):
            RunningHubRouteRef.parse("other:webapp-1@2")
        self.assertEqual(RunningHubRouteRef.parse({"kind": "workflow", "route_id": "w", "version": 1}).ref, "workflow:w@1")

    async def test_route_version_mismatch_is_not_substituted(self):
        route = sample_route(version=5)
        executor = RunningHubExecutor(
            transport=FakeRunningHubTransport(),
            route_resolver=lambda ref: route if ref.route_id == route.route_id and ref.kind == route.kind else None,
            timeout_seconds=1.0,
            cancel_timeout_seconds=0.1,
        )

        with self.assertRaises(RunningHubExecutorError) as caught:
            await executor.prepare(self.request())
        self.assertIn("version mismatch", str(caught.exception))
        self.assertEqual(executor._prepared, {})

    async def test_unknown_route_is_rejected(self):
        executor = RunningHubExecutor(
            transport=FakeRunningHubTransport(),
            route_resolver=lambda ref: None,
            timeout_seconds=1.0,
            cancel_timeout_seconds=0.1,
        )

        with self.assertRaises(RunningHubExecutorError) as caught:
            await executor.prepare(self.request())
        self.assertIn("not available", str(caught.exception))

    async def test_unknown_role_and_missing_required_role_are_rejected(self):
        executor = self.executor()

        with self.assertRaises(RunningHubExecutorError) as caught:
            await executor.prepare(self.request(inputs=(ExecutionInput(name="caption", value="x"),)))
        self.assertIn("no node binding for role", str(caught.exception))

        with self.assertRaises(RunningHubExecutorError) as caught:
            await executor.prepare(self.request(inputs=(ExecutionInput(name="seed", value=7),)))
        self.assertIn("missing required input role", str(caught.exception))

    async def test_declared_input_roles_map_onto_node_fields(self):
        executor = self.executor()
        request = self.request(
            inputs=(ExecutionInput(name="input-1", value="a cat"), ExecutionInput(name="input-2", value=42)),
            config={
                "route_ref": "ai_app:webapp-1@2",
                "input_roles": {"input-1": "prompt", "input-2": "seed"},
            },
        )

        await executor.start(await executor.prepare(request))

        self.assertEqual(
            [(entry.node_id, entry.field_name, entry.value) for entry in self.transport.calls[0].node_info],
            [("3", "text", "a cat"), ("5", "seed", 42)],
        )

    async def test_status_and_output_events_are_normalized(self):
        transport = FakeRunningHubTransport(events=[
            RunningHubRawEvent(kind="queued", code=813),
            RunningHubRawEvent(kind="running", code=804),
            RunningHubRawEvent(kind="completed", code=0, items=(
                RunningHubOutputItem(kind="image", url="https://files.example.test/a.png", filename="a.png"),
                RunningHubOutputItem(kind="image", url="https://files.example.test/b.png", name="poster"),
            )),
        ])
        executor = self.executor(transport=transport)

        handle = await executor.start(await executor.prepare(self.request()))
        events = [event async for event in executor.stream(handle)]
        result = await executor.result(handle)

        self.assertEqual([event.kind for event in events], ["started", "progress", "progress", "completed"])
        self.assertEqual(events[1].message, "RunningHub task queued")
        self.assertEqual(events[1].metadata["provider_code"], 813)
        self.assertEqual(events[2].message, "RunningHub task running")
        self.assertEqual([output.name for output in result.outputs], ["image.1", "poster"])
        self.assertEqual(result.outputs[0].value, {"kind": "image", "url": "https://files.example.test/a.png", "filename": "a.png"})
        self.assertEqual(result.status, "succeeded")
        await executor.cleanup(handle)

    async def test_failed_event_becomes_typed_failed_result(self):
        transport = FakeRunningHubTransport(events=[RunningHubRawEvent(kind="failed", code=805, message="out of memory")])
        executor = self.executor(transport=transport)

        handle = await executor.start(await executor.prepare(self.request()))
        events = [event async for event in executor.stream(handle)]
        result = await executor.result(handle)

        self.assertEqual((events[-1].kind, result.status, result.error), ("failed", "failed", "out of memory"))
        self.assertEqual(events[-1].metadata["provider_code"], 805)
        await executor.cleanup(handle)

    async def test_partial_output_and_stream_end_completion(self):
        transport = FakeRunningHubTransport(events=[
            RunningHubRawEvent(kind="output", items=(RunningHubOutputItem(kind="image", url="https://files.example.test/a.png"),)),
        ])
        executor = self.executor(transport=transport)

        handle = await executor.start(await executor.prepare(self.request()))
        events = [event async for event in executor.stream(handle)]
        result = await executor.result(handle)

        self.assertEqual(events[1].kind, "partial_result")
        self.assertEqual(events[-1].kind, "completed")
        self.assertEqual((result.status, len(result.outputs)), ("succeeded", 1))
        await executor.cleanup(handle)

    async def test_transport_failure_becomes_typed_failed_result(self):
        class FailingTransport(FakeRunningHubTransport):
            async def next_event(self, submission):
                raise RunningHubTransportError("runninghub polling failed")

        executor = self.executor(transport=FailingTransport())

        handle = await executor.start(await executor.prepare(self.request()))
        events = [event async for event in executor.stream(handle)]
        result = await executor.result(handle)

        self.assertEqual((events[-1].kind, result.status, result.error), ("failed", "failed", "runninghub polling failed"))
        await executor.cleanup(handle)

    async def test_stream_timeout_becomes_typed_failed_result(self):
        executor = self.executor(transport=FakeRunningHubTransport(hang=True), timeout_seconds=0.05)

        handle = await executor.start(await executor.prepare(self.request()))
        events = [event async for event in executor.stream(handle)]
        result = await executor.result(handle)

        self.assertEqual((events[-1].kind, events[-1].status, result.status), ("failed", "failed", "failed"))
        self.assertIn("timed out", result.error)
        await executor.cleanup(handle)

    async def test_submit_failure_reports_before_any_execution_state(self):
        executor = self.executor(transport=FakeRunningHubTransport(fail_submit=True))
        prepared = await executor.prepare(self.request())

        with self.assertRaises(RunningHubExecutorError) as caught:
            await executor.start(prepared)
        self.assertIn("runninghub rejected the task", str(caught.exception))

    async def test_cancel_is_explicit_repeatable_and_terminal(self):
        executor = self.executor(transport=FakeRunningHubTransport(hang=True))

        handle = await executor.start(await executor.prepare(self.request()))
        first = await executor.cancel(handle)
        second = await executor.cancel(handle)
        status = await executor.status(handle)
        result = await executor.result(handle)

        self.assertEqual(
            (first.accepted, first.status, second.status, status.status, result.status),
            (True, "cancelled", "cancelled", "cancelled", "cancelled"),
        )
        self.assertEqual(self.transport.cancel_calls, 1)
        await executor.cleanup(handle)

    async def test_cancel_interrupts_a_waiting_stream(self):
        executor = self.executor(transport=FakeRunningHubTransport(hang=True))

        handle = await executor.start(await executor.prepare(self.request()))
        stream = executor.stream(handle).__aiter__()
        await stream.__anext__()
        waiting = asyncio.create_task(stream.__anext__())
        await asyncio.sleep(0)

        await executor.cancel(handle)
        event = await asyncio.wait_for(waiting, timeout=0.5)

        self.assertEqual((event.kind, event.status), ("cancelled", "cancelled"))
        await executor.cleanup(handle)

    async def test_unaccepted_cancellation_is_reported_explicitly(self):
        executor = self.executor(transport=FakeRunningHubTransport(hang=True, accept_cancel=False))

        handle = await executor.start(await executor.prepare(self.request()))
        cancel_result = await executor.cancel(handle)
        status = await executor.status(handle)

        self.assertEqual((cancel_result.accepted, cancel_result.status, status.status), (False, "unknown", "running"))
        self.transport.release.set()
        await executor.cleanup(handle)

    async def test_prepare_start_and_unknown_execution_are_bounded(self):
        executor = self.executor()
        prepared = await executor.prepare(self.request())

        with self.assertRaises(RunningHubExecutorError):
            await executor.prepare(self.request())
        handle = await executor.start(prepared)
        with self.assertRaises(RunningHubExecutorError):
            await executor.start(prepared)
        with self.assertRaises(RunningHubExecutorError):
            await executor.result(ExecutionHandle(execution_id="other", executor_ref=RUNNINGHUB_EXECUTOR_REF))
        with self.assertRaises(RunningHubExecutorError):
            await executor.result(ExecutionHandle(execution_id=handle.execution_id, executor_ref="comfyui"))

        self.assertEqual((await executor.health()).status, "healthy")
        await executor.cleanup(handle)

    def test_profile_is_the_timeout_and_executor_identity_authority(self):
        profile = ExecutionProfile(
            id="profile-rh", version=1, name="RunningHub", executor_ref=RUNNINGHUB_EXECUTOR_REF,
            timeout_seconds=42.5, cancel_timeout_seconds=2.5,
        )
        configured = RunningHubExecutor(
            transport=FakeRunningHubTransport(), route_resolver=lambda ref: sample_route(), profile=profile,
        )
        self.assertEqual((configured._timeout_seconds, configured._cancel_timeout_seconds), (42.5, 2.5))

        with self.assertRaises(ValueError):
            RunningHubExecutor(
                transport=FakeRunningHubTransport(), route_resolver=lambda ref: None,
                profile=profile, timeout_seconds=1,
            )
        with self.assertRaises(ValueError):
            RunningHubExecutor(
                transport=FakeRunningHubTransport(), route_resolver=lambda ref: None,
                profile=ExecutionProfile(id="p", version=1, name="Comfy", executor_ref="comfyui"),
            )

    def test_route_seam_rejects_duplicate_roles_and_credential_parameters(self):
        with self.assertRaises(ValueError):
            sample_route(node_bindings=(
                RunningHubNodeBinding(role="prompt", node_id="3", field_name="text"),
                RunningHubNodeBinding(role="prompt", node_id="4", field_name="text"),
            ))
        with self.assertRaises(ValueError):
            RunningHubCall(
                execution_id="execution-1",
                idempotency_key="idempotency-1",
                route_kind="ai_app",
                route_id="webapp-1",
                route_version=2,
                parameters={"api_key": "must-not-cross-the-boundary"},
            )

    def test_seam_has_no_canvas_or_provider_sdk_dependency(self):
        root = Path(__file__).resolve().parent.parent
        violations = []
        for path in sorted((root / "workbench" / "runninghub").rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            for module in _imported_modules(path, root):
                lowered = module.lower()
                if module in FORBIDDEN_PROVIDER_SDK_IMPORTS or module.split(".")[0] in FORBIDDEN_PROVIDER_SDK_IMPORTS:
                    violations.append(f"{path.relative_to(root)} -> provider sdk {module}")
                if any(marker in lowered for marker in FORBIDDEN_BOUNDARY_MARKERS):
                    violations.append(f"{path.relative_to(root)} -> canvas/legacy {module}")
        self.assertEqual(violations, [])


class RunningHubExecutorRegistryTests(unittest.IsolatedAsyncioTestCase):
    async def test_registry_resolves_the_runninghub_runtime_route_without_substitution(self):
        executor = RunningHubExecutor(
            transport=FakeRunningHubTransport(), route_resolver=lambda ref: sample_route(),
        )
        self.assertIsInstance(executor, Executor)
        registry = ExecutorRegistry((
            ExecutorRegistration(
                executor=executor,
                capabilities=("image",),
                runtime_routes=("runninghub",),
                execution_profiles=("profile-rh@1",),
            ),
        ))

        resolved = registry.resolve(runtime_route_ref="runninghub", execution_profile_ref="profile-rh@1", required_capabilities=("image",))
        other = registry.resolve(runtime_route_ref="comfyui")

        self.assertTrue(resolved.resolved)
        self.assertEqual(resolved.executor.executor_ref, RUNNINGHUB_EXECUTOR_REF)
        self.assertFalse(other.resolved)
        self.assertEqual(other.reason, "runtime_route_unavailable")


class RunningHubExecutionServiceTests(unittest.IsolatedAsyncioTestCase):
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
            id_factory=iter(["event-1", "event-2", "event-3", "event-4", "event-5"]).__next__,
            clock=lambda: self.now,
        )

    def tearDown(self):
        self.temp.cleanup()

    def profile(self):
        return ExecutionProfile(
            id="profile-rh", version=1, name="RunningHub", executor_ref=RUNNINGHUB_EXECUTOR_REF,
            runtime_connection_ref="runninghub-openapi",
            default_params={"route_ref": "ai_app:webapp-1@2"},
        )

    def run_record(self, run_id: str, task_id: str):
        return ExecutionRun(
            id=run_id, project_id="project-1", task_id=task_id, execution_profile_ref="profile-rh@1",
            policy=ExecutionPolicy(),
            input_projection=ExecutionInputProjection(
                inputs=[{
                    "input_id": "input-1", "binding_id": "binding-1", "target": "route.prompt",
                    "role": "prompt", "order": 0, "source_type": "literal", "source_ref": "literal-1",
                    "value": "a poster", "source_snapshot": "a poster",
                }],
                parameters={"input_roles": {"input-1": "prompt"}},
            ),
            created_at=self.now,
        )

    def executor(self, transport):
        return RunningHubExecutor(
            transport=transport,
            route_resolver=lambda ref: sample_route() if ref.ref == "ai_app:webapp-1@2" else None,
            profile=self.profile(),
        )

    async def test_task_runs_as_an_executor_route_not_a_canvas_runtime(self):
        self.runs.create(self.run_record("run-rh", "task-rh"), actor_id="owner")
        transport = FakeRunningHubTransport(events=[
            RunningHubRawEvent(kind="queued", code=813),
            RunningHubRawEvent(kind="running", code=804),
            RunningHubRawEvent(kind="completed", code=0, items=(
                RunningHubOutputItem(kind="image", url="https://files.example.test/poster.png", filename="poster.png"),
            )),
        ])
        service = ExecutionService(
            self.runs,
            self.attempts,
            actor_id="owner",
            event_service=self.events,
            id_factory=iter(["attempt-rh", "idempotency-rh"]).__next__,
            clock=lambda: self.now,
        )

        result = await service.execute_run("run-rh", executor=self.executor(transport))

        self.assertEqual(result.status, "succeeded")
        self.assertEqual(result.outputs[0].value["url"], "https://files.example.test/poster.png")
        self.assertEqual(self.runs.get("run-rh", actor_id="owner").status, "succeeded")
        attempt = self.attempts.get("attempt-rh", actor_id="owner")
        self.assertEqual((attempt.status, attempt.summary["output_count"], attempt.summary["executor_ref"]), ("succeeded", 1, RUNNINGHUB_EXECUTOR_REF))
        self.assertEqual(
            [event.event_type for event in self.events.stream("run-rh")],
            ["started", "progress", "progress", "completed"],
        )
        call = transport.calls[0]
        self.assertEqual((call.route_ref, call.connection_ref), ("ai_app:webapp-1@2", "runninghub-openapi"))
        self.assertEqual([(entry.node_id, entry.field_name, entry.value) for entry in call.node_info], [("3", "text", "a poster")])

    async def test_execution_service_cancel_uses_the_active_runninghub_handle(self):
        self.runs.create(self.run_record("run-cancel", "task-rh"), actor_id="owner")
        transport = FakeRunningHubTransport(hang=True)
        service = ExecutionService(
            self.runs,
            self.attempts,
            actor_id="owner",
            id_factory=iter(["attempt-cancel", "idempotency-cancel"]).__next__,
            clock=lambda: self.now,
        )

        running = asyncio.create_task(service.execute("run-cancel", executor=self.executor(transport)))
        for _ in range(20):
            if "attempt-cancel" in service._active_controls:
                break
            await asyncio.sleep(0)

        cancelled = await service.cancel_run("run-cancel")
        result = await running

        self.assertEqual((cancelled.status, result.status), ("cancelled", "cancelled"))
        self.assertEqual(self.attempts.get("attempt-cancel", actor_id="owner").status, "cancelled")
        self.assertEqual(transport.cancel_calls, 1)


if __name__ == "__main__":
    unittest.main()

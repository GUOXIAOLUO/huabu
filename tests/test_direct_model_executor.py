"""Focused tests for the R8-12 DirectModelExecutor route."""

import ast
import asyncio
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

from workbench.application.execution_event_service import ExecutionEventService
from workbench.application.execution_service import ExecutionService
from workbench.application.executor_registry import ExecutorRegistration, ExecutorRegistry
from workbench.direct_model import (
    DIRECT_MODEL_EXECUTOR_REF,
    DirectModelCall,
    DirectModelExecutor,
    DirectModelExecutorError,
    DirectModelRawEvent,
    DirectModelSubmission,
    DirectModelTransport,
    DirectModelTransportError,
)
from workbench.domain.availability import ModelAvailability
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
from workbench.domain.provider import CredentialRef, ProviderConnection
from workbench.repositories.execution_attempt_repository import SqliteExecutionAttemptRepository
from workbench.repositories.execution_event_repository import SqliteExecutionEventRepository
from workbench.repositories.execution_run_repository import SqliteExecutionRunRepository
from workbench.repositories.sqlite_project_canvas_repository import SqliteProjectCanvasRepository


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
)


def available_provider_route(**overrides):
    payload = {
        "id": "availability-1",
        "model_ref": "model-1",
        "route_type": "provider",
        "route_ref": "connection-1",
        "executor_type": "model_api",
        "normalized_capabilities": ("text",),
        "enabled": True,
        "status": "available",
    }
    payload.update(overrides)
    return ModelAvailability(**payload)


def active_connection(**overrides):
    payload = {
        "id": "connection-1",
        "provider_id": "provider-1",
        "ref": "provider-1/default",
        "config": {"endpoint": "https://api.example.test/v1"},
        "credential_ref": CredentialRef(id="credential-1"),
        "status": "active",
    }
    payload.update(overrides)
    return ProviderConnection(**payload)


class FakeDirectModelTransport:
    """Minimal provider-facing transport double."""

    def __init__(self, events=(), *, fail_submit=False, accept_cancel=True, hang=False):
        self.calls: list[DirectModelCall] = []
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
            raise DirectModelTransportError("provider rejected the call")
        return DirectModelSubmission(submission_id=f"submission-{len(self.calls)}")

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


class DirectModelRouteTests(unittest.IsolatedAsyncioTestCase):
    def executor(self, *, availability=None, connection=None, transport=None, profile=None, timeout_seconds=1.0):
        resolved_availability = availability if availability is not None else available_provider_route()
        resolved_connection = connection if connection is not None else active_connection()
        self.transport = transport if transport is not None else FakeDirectModelTransport()
        budgets = {} if profile is not None else {"timeout_seconds": timeout_seconds, "cancel_timeout_seconds": 0.1}
        return DirectModelExecutor(
            transport=self.transport,
            availability_resolver=lambda ref: resolved_availability if ref == resolved_availability.id else None,
            connection_resolver=lambda ref: resolved_connection if ref == resolved_connection.id else None,
            profile=profile,
            **budgets,
        )

    def request(self, **overrides):
        payload = {
            "execution_id": "execution-1",
            "idempotency_key": "idempotency-1",
            "inputs": (ExecutionInput(name="prompt", value="hello"),),
            "config": {"task_id": "task-1"},
            "model_availability_ref": "availability-1",
        }
        payload.update(overrides)
        return ExecutionRequest(**payload)

    async def test_provider_route_is_resolved_through_availability_and_connection(self):
        profile = ExecutionProfile(
            id="profile-1", version=1, name="Direct", executor_ref=DIRECT_MODEL_EXECUTOR_REF,
            default_params={"temperature": 0.2},
        )
        executor = self.executor(profile=profile)
        request = self.request(execution_profile_ref="profile-1@1")

        prepared = await executor.prepare(request)
        handle = await executor.start(prepared)

        self.assertEqual(prepared.executor_ref, DIRECT_MODEL_EXECUTOR_REF)
        self.assertEqual(
            prepared.metadata,
            {
                "route_type": "provider",
                "model_ref": "model-1",
                "provider_id": "provider-1",
                "connection_ref": "connection-1",
                "executor_type": "model_api",
            },
        )
        call = self.transport.calls[0]
        self.assertEqual(
            (call.model_ref, call.provider_id, call.connection_ref, call.credential_ref, call.availability_ref),
            ("model-1", "provider-1", "connection-1", "credential-1", "availability-1"),
        )
        self.assertEqual(call.inputs[0].value, "hello")
        self.assertEqual(call.parameters, {"temperature": 0.2, "task_id": "task-1"})
        self.assertEqual(call.connection_config, {"endpoint": "https://api.example.test/v1"})
        self.assertEqual(call.capabilities, ("text",))
        self.assertEqual(call.idempotency_key, "idempotency-1")
        self.assertEqual(handle.execution_id, request.execution_id)

    async def test_runtime_routes_belong_to_another_executor(self):
        executor = self.executor(availability=available_provider_route(route_type="runtime", route_ref="codex"))

        with self.assertRaises(DirectModelExecutorError) as caught:
            await executor.prepare(self.request())

        self.assertIn("provider route", str(caught.exception))
        self.assertEqual(self.transport.calls, [])

    async def test_missing_availability_reference_is_rejected(self):
        executor = self.executor()

        with self.assertRaises(DirectModelExecutorError) as caught:
            await executor.prepare(self.request(model_availability_ref=None))

        self.assertIn("model availability reference", str(caught.exception))
        self.assertEqual(self.transport.calls, [])

    async def test_unknown_availability_and_connection_are_rejected(self):
        executor = self.executor()

        with self.assertRaises(DirectModelExecutorError) as caught:
            await executor.prepare(self.request(model_availability_ref="missing-availability"))
        self.assertIn("not available", str(caught.exception))

        disconnected = DirectModelExecutor(
            transport=FakeDirectModelTransport(),
            availability_resolver=lambda ref: available_provider_route(),
            connection_resolver=lambda ref: None,
            timeout_seconds=1.0,
            cancel_timeout_seconds=0.1,
        )
        with self.assertRaises(DirectModelExecutorError) as caught:
            await disconnected.prepare(self.request())
        self.assertIn("not configured", str(caught.exception))
        self.assertEqual(disconnected._prepared, {})

    async def test_disabled_availability_and_unusable_connection_are_rejected(self):
        disabled = self.executor(availability=available_provider_route(enabled=False))
        with self.assertRaises(DirectModelExecutorError) as caught:
            await disabled.prepare(self.request())
        self.assertIn("disabled", str(caught.exception))

        unavailable = self.executor(availability=available_provider_route(status="unavailable"))
        with self.assertRaises(DirectModelExecutorError) as caught:
            await unavailable.prepare(self.request())
        self.assertIn("unavailable", str(caught.exception))

        broken = self.executor(connection=active_connection(status="error"))
        with self.assertRaises(DirectModelExecutorError) as caught:
            await broken.prepare(self.request())
        self.assertIn("not usable", str(caught.exception))

    async def test_events_are_normalized_and_outputs_accumulate(self):
        transport = FakeDirectModelTransport(events=[
            DirectModelRawEvent(kind="progress", message="queued"),
            DirectModelRawEvent(kind="partial_result", value="draft"),
            DirectModelRawEvent(kind="completed", value="final", usage={"characters": 24}),
        ])
        executor = self.executor(transport=transport)

        handle = await executor.start(await executor.prepare(self.request()))
        events = [event async for event in executor.stream(handle)]
        result = await executor.result(handle)
        await executor.cleanup(handle)

        self.assertEqual([event.kind for event in events], ["started", "progress", "partial_result", "completed"])
        self.assertEqual([event.sequence for event in events], [0, 1, 2, 3])
        self.assertEqual([event.status for event in events], ["running", "running", "running", "succeeded"])
        self.assertEqual([output.value for output in result.outputs], ["draft", "final"])
        self.assertEqual({output.name for output in result.outputs}, {"text"})
        self.assertEqual(events[-1].outputs[0].value, "final")
        self.assertEqual(result.usage, {"characters": 24})
        self.assertEqual(transport.closed, 1)

    async def test_named_outputs_keep_their_normalized_name(self):
        transport = FakeDirectModelTransport(events=[
            DirectModelRawEvent(kind="completed", name="image_url", value="https://cdn.example.test/a.png"),
        ])
        executor = self.executor(transport=transport)

        handle = await executor.start(await executor.prepare(self.request()))
        events = [event async for event in executor.stream(handle)]
        result = await executor.result(handle)

        self.assertEqual(result.outputs[0].name, "image_url")
        self.assertEqual(events[-1].outputs[0].name, "image_url")
        await executor.cleanup(handle)

    async def test_stream_without_terminal_event_still_completes(self):
        transport = FakeDirectModelTransport(events=[DirectModelRawEvent(kind="partial_result", value="draft")])
        executor = self.executor(transport=transport)

        handle = await executor.start(await executor.prepare(self.request()))
        events = [event async for event in executor.stream(handle)]
        result = await executor.result(handle)

        self.assertEqual(events[-1].kind, "completed")
        self.assertEqual((result.status, result.outputs[0].value), ("succeeded", "draft"))
        await executor.cleanup(handle)

    async def test_failed_event_becomes_typed_failed_result(self):
        transport = FakeDirectModelTransport(events=[DirectModelRawEvent(kind="failed", message="upstream 500")])
        executor = self.executor(transport=transport)

        handle = await executor.start(await executor.prepare(self.request()))
        events = [event async for event in executor.stream(handle)]
        result = await executor.result(handle)

        self.assertEqual((events[-1].kind, result.status, result.error), ("failed", "failed", "upstream 500"))
        await executor.cleanup(handle)

    async def test_transport_failure_becomes_typed_failed_result(self):
        class FailingTransport(FakeDirectModelTransport):
            async def next_event(self, submission):
                raise DirectModelTransportError("connection reset")

        executor = self.executor(transport=FailingTransport())

        handle = await executor.start(await executor.prepare(self.request()))
        events = [event async for event in executor.stream(handle)]
        result = await executor.result(handle)

        self.assertEqual((events[-1].kind, result.status, result.error), ("failed", "failed", "connection reset"))
        await executor.cleanup(handle)

    async def test_stream_timeout_becomes_typed_failed_result(self):
        executor = self.executor(transport=FakeDirectModelTransport(hang=True), timeout_seconds=0.05)

        handle = await executor.start(await executor.prepare(self.request()))
        events = [event async for event in executor.stream(handle)]
        result = await executor.result(handle)

        self.assertEqual((events[-1].kind, events[-1].status, result.status), ("failed", "failed", "failed"))
        self.assertIn("timed out", result.error)
        await executor.cleanup(handle)

    async def test_submit_failure_reports_before_any_execution_state(self):
        executor = self.executor(transport=FakeDirectModelTransport(fail_submit=True))
        prepared = await executor.prepare(self.request())

        with self.assertRaises(DirectModelExecutorError) as caught:
            await executor.start(prepared)
        self.assertIn("provider rejected the call", str(caught.exception))

    async def test_cancel_is_explicit_repeatable_and_terminal(self):
        executor = self.executor(transport=FakeDirectModelTransport(hang=True))

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
        transport = FakeDirectModelTransport(hang=True)
        executor = self.executor(transport=transport)

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
        executor = self.executor(transport=FakeDirectModelTransport(hang=True, accept_cancel=False))

        handle = await executor.start(await executor.prepare(self.request()))
        cancel_result = await executor.cancel(handle)
        status = await executor.status(handle)

        self.assertEqual((cancel_result.accepted, cancel_result.status, status.status), (False, "unknown", "running"))
        self.transport.release.set()
        await executor.cleanup(handle)

    async def test_prepare_start_and_unknown_execution_are_bounded(self):
        executor = self.executor(transport=FakeDirectModelTransport())
        prepared = await executor.prepare(self.request())

        with self.assertRaises(DirectModelExecutorError):
            await executor.prepare(self.request())
        handle = await executor.start(prepared)
        with self.assertRaises(DirectModelExecutorError):
            await executor.start(prepared)
        with self.assertRaises(DirectModelExecutorError):
            await executor.result(ExecutionHandle(execution_id="other", executor_ref=DIRECT_MODEL_EXECUTOR_REF))
        with self.assertRaises(DirectModelExecutorError):
            await executor.result(ExecutionHandle(execution_id=handle.execution_id, executor_ref="codex-harness"))

        self.assertEqual((await executor.health()).status, "healthy")
        await executor.cleanup(handle)

    def test_profile_is_the_timeout_and_executor_identity_authority(self):
        profile = ExecutionProfile(
            id="profile-1", version=1, name="Direct", executor_ref=DIRECT_MODEL_EXECUTOR_REF,
            timeout_seconds=0.25, cancel_timeout_seconds=0.1,
        )
        configured = DirectModelExecutor(
            transport=FakeDirectModelTransport(),
            availability_resolver=lambda ref: available_provider_route(),
            connection_resolver=lambda ref: active_connection(),
            profile=profile,
        )
        self.assertEqual((configured._timeout_seconds, configured._cancel_timeout_seconds), (0.25, 0.1))

        with self.assertRaises(ValueError):
            DirectModelExecutor(
                transport=FakeDirectModelTransport(),
                availability_resolver=lambda ref: None,
                connection_resolver=lambda ref: None,
                profile=profile,
                timeout_seconds=1,
            )
        with self.assertRaises(ValueError):
            DirectModelExecutor(
                transport=FakeDirectModelTransport(),
                availability_resolver=lambda ref: None,
                connection_resolver=lambda ref: None,
                profile=ExecutionProfile(id="p", version=1, name="Codex", executor_ref="codex-harness"),
            )

    def test_transport_port_and_call_boundary_reject_credential_material(self):
        self.assertTrue(issubclass(DirectModelTransport, object))
        self.assertTrue(hasattr(DirectModelTransport, "submit"))
        with self.assertRaises(ValueError):
            DirectModelCall(
                execution_id="execution-1",
                idempotency_key="idempotency-1",
                availability_ref="availability-1",
                model_ref="model-1",
                provider_id="provider-1",
                connection_ref="connection-1",
                parameters={"api_key": "must-not-cross-the-boundary"},
            )
        with self.assertRaises(ValueError):
            DirectModelRawEvent(kind="completed", usage={"access_token": "must-not-cross-the-boundary"})

    def test_no_provider_sdk_leaks_into_domain_or_the_direct_model_boundary(self):
        root = Path(__file__).resolve().parent.parent
        violations = []
        for relative in ("workbench/domain", "workbench/application", "workbench/direct_model"):
            for path in sorted((root / relative).rglob("*.py")):
                if "__pycache__" in path.parts:
                    continue
                for module in _imported_modules(path, root):
                    if module in FORBIDDEN_PROVIDER_SDK_IMPORTS or module.split(".")[0] in FORBIDDEN_PROVIDER_SDK_IMPORTS:
                        violations.append(f"{path.relative_to(root)} -> {module}")
        self.assertEqual(violations, [])


class DirectModelExecutorRegistryTests(unittest.IsolatedAsyncioTestCase):
    async def test_registry_resolves_the_provider_route_without_substitution(self):
        executor = DirectModelExecutor(
            transport=FakeDirectModelTransport(),
            availability_resolver=lambda ref: available_provider_route(),
            connection_resolver=lambda ref: active_connection(),
        )
        self.assertIsInstance(executor, Executor)
        registry = ExecutorRegistry((
            ExecutorRegistration(
                executor=executor,
                capabilities=("text",),
                runtime_routes=("provider",),
                execution_profiles=("profile-1@1",),
            ),
        ))

        resolved = registry.resolve(runtime_route_ref="provider", execution_profile_ref="profile-1@1", required_capabilities=("text",))
        runtime = registry.resolve(runtime_route_ref="runtime")

        self.assertTrue(resolved.resolved)
        self.assertEqual(resolved.executor.executor_ref, DIRECT_MODEL_EXECUTOR_REF)
        self.assertFalse(runtime.resolved)
        self.assertEqual(runtime.reason, "runtime_route_unavailable")


class DirectModelExecutionServiceTests(unittest.IsolatedAsyncioTestCase):
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
            id_factory=iter(["event-1", "event-2", "event-3", "event-4"]).__next__,
            clock=lambda: self.now,
        )

    def tearDown(self):
        self.temp.cleanup()

    def run_record(self, run_id: str, task_id: str):
        return ExecutionRun(
            id=run_id, project_id="project-1", task_id=task_id, execution_profile_ref="profile-1@1",
            policy=ExecutionPolicy(),
            input_projection=ExecutionInputProjection(
                inputs=[{
                    "input_id": "input-1", "binding_id": "binding-1", "target": "task.prompt",
                    "role": "prompt", "order": 0, "source_type": "literal", "source_ref": "literal-1",
                    "value": "hello", "source_snapshot": "hello",
                }],
                model_availability_ref="availability-1",
            ),
            created_at=self.now,
        )

    def executor(self, transport):
        return DirectModelExecutor(
            transport=transport,
            availability_resolver=lambda ref: available_provider_route() if ref == "availability-1" else None,
            connection_resolver=lambda ref: active_connection() if ref == "connection-1" else None,
            timeout_seconds=1.0,
            cancel_timeout_seconds=0.1,
        )

    async def test_generic_task_runs_through_execution_service_and_persists_lifecycle(self):
        self.runs.create(self.run_record("run-1", "task-1"), actor_id="owner")
        transport = FakeDirectModelTransport(events=[
            DirectModelRawEvent(kind="partial_result", value="draft"),
            DirectModelRawEvent(kind="completed", value="answer"),
        ])
        service = ExecutionService(
            self.runs,
            self.attempts,
            actor_id="owner",
            event_service=self.events,
            id_factory=iter(["attempt-1", "idempotency-1"]).__next__,
            clock=lambda: self.now,
        )

        result = await service.execute_run("run-1", executor=self.executor(transport))

        self.assertEqual((result.status, [output.value for output in result.outputs]), ("succeeded", ["draft", "answer"]))
        self.assertEqual(self.runs.get("run-1", actor_id="owner").status, "succeeded")
        attempt = self.attempts.get("attempt-1", actor_id="owner")
        self.assertEqual((attempt.status, attempt.summary["output_count"], attempt.summary["executor_ref"]), ("succeeded", 2, DIRECT_MODEL_EXECUTOR_REF))
        self.assertEqual([event.event_type for event in self.events.stream("run-1")], ["started", "partial_result", "completed"])
        self.assertEqual(transport.calls[0].model_ref, "model-1")

    async def test_execution_service_cancel_uses_the_active_direct_model_handle(self):
        self.runs.create(self.run_record("run-cancel", "task-cancel"), actor_id="owner")
        transport = FakeDirectModelTransport(hang=True)
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

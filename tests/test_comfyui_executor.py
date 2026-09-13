"""Focused tests for the R8-13 ComfyUIExecutor seam."""

import ast
import asyncio
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

from workbench.application.execution_event_service import ExecutionEventService
from workbench.application.execution_service import ExecutionService
from workbench.application.executor_registry import ExecutorRegistration, ExecutorRegistry
from workbench.comfyui import (
    COMFYUI_EXECUTOR_REF,
    ComfyUICall,
    ComfyUIExecutor,
    ComfyUIExecutorError,
    ComfyUIInputBinding,
    ComfyUIOutputItem,
    ComfyUIRawEvent,
    ComfyUISubmission,
    ComfyUITransport,
    ComfyUITransportError,
    ComfyUIWorkflow,
    ComfyUIWorkflowRef,
)
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
# DoD: a ComfyUI execution must not depend on provider-shaped Canvas node code.
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


def sample_workflow(**overrides):
    payload = {
        "id": "workflow-1",
        "version": 3,
        "title": "Text to image",
        "graph": {
            "1": {"class_type": "CLIPTextEncode", "inputs": {"text": "placeholder"}},
            "2": {"class_type": "KSampler", "inputs": {"seed": 1, "steps": 20}},
            "3": {"class_type": "SaveImage", "inputs": {}},
        },
        "input_bindings": (
            ComfyUIInputBinding(role="prompt", node_id="1", input_name="text"),
            ComfyUIInputBinding(role="seed", node_id="2", input_name="seed", required=False),
        ),
    }
    payload.update(overrides)
    return ComfyUIWorkflow(**payload)


class FakeComfyUITransport:
    """Minimal ComfyUI-facing transport double."""

    def __init__(self, events=(), *, fail_submit=False, accept_cancel=True, hang=False):
        self.calls: list[ComfyUICall] = []
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
            raise ComfyUITransportError("comfyui rejected the prompt")
        return ComfyUISubmission(prompt_id=f"prompt-{len(self.calls)}")

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


class ComfyUIExecutorRouteTests(unittest.IsolatedAsyncioTestCase):
    def executor(self, *, workflow=None, transport=None, profile=None, timeout_seconds=1.0):
        resolved = workflow if workflow is not None else sample_workflow()
        self.transport = transport if transport is not None else FakeComfyUITransport()
        budgets = {} if profile is not None else {"timeout_seconds": timeout_seconds, "cancel_timeout_seconds": 0.1}
        return ComfyUIExecutor(
            transport=self.transport,
            workflow_resolver=lambda ref: resolved if ref.workflow_id == resolved.id and ref.version == resolved.version else None,
            profile=profile,
            **budgets,
        )

    def request(self, **overrides):
        payload = {
            "execution_id": "execution-1",
            "idempotency_key": "idempotency-1",
            "inputs": (ExecutionInput(name="prompt", value="a cat"),),
            "config": {"workflow_ref": "workflow-1@3"},
        }
        payload.update(overrides)
        return ExecutionRequest(**payload)

    async def test_workflow_and_profile_references_are_resolved_without_mutating_the_workflow(self):
        workflow = sample_workflow()
        profile = ExecutionProfile(
            id="profile-comfy", version=1, name="Comfy", executor_ref=COMFYUI_EXECUTOR_REF,
            runtime_connection_ref="comfy-backend", default_params={"workflow_ref": "workflow-1@3"},
        )
        executor = self.executor(workflow=workflow, profile=profile)
        request = self.request(execution_profile_ref="profile-comfy@1", config={})

        prepared = await executor.prepare(request)
        await executor.start(prepared)
        call = self.transport.calls[0]

        self.assertEqual(prepared.executor_ref, COMFYUI_EXECUTOR_REF)
        self.assertEqual(call.workflow_ref, "workflow-1@3")
        self.assertEqual(call.connection_ref, "comfy-backend")
        self.assertEqual(prepared.metadata["workflow_ref"], "workflow-1@3")
        self.assertEqual(prepared.metadata["input_roles"], ("prompt", "seed"))
        self.assertEqual(call.graph["1"]["inputs"]["text"], "a cat")
        self.assertEqual(workflow.graph["1"]["inputs"]["text"], "placeholder")

    async def test_missing_workflow_reference_is_rejected(self):
        executor = self.executor()

        with self.assertRaises(ComfyUIExecutorError) as caught:
            await executor.prepare(self.request(config={}))
        self.assertIn("workflow reference", str(caught.exception))
        self.assertEqual(self.transport.calls, [])

    def test_implicit_latest_version_is_rejected(self):
        with self.assertRaises(ValueError):
            ComfyUIWorkflowRef.parse("workflow-1")
        with self.assertRaises(ValueError):
            ComfyUIWorkflowRef.parse("workflow-1@0")
        self.assertEqual(ComfyUIWorkflowRef.parse({"workflow_id": "w", "version": 2}).ref, "w@2")

    async def test_workflow_version_mismatch_is_not_substituted(self):
        # A resolver handed back another version for the requested reference;
        # the executor must refuse instead of running the wrong workflow.
        workflow = sample_workflow(version=4)
        executor = ComfyUIExecutor(
            transport=FakeComfyUITransport(),
            workflow_resolver=lambda ref: workflow if ref.workflow_id == workflow.id else None,
            timeout_seconds=1.0,
            cancel_timeout_seconds=0.1,
        )

        with self.assertRaises(ComfyUIExecutorError) as caught:
            await executor.prepare(self.request())
        self.assertIn("version mismatch", str(caught.exception))
        self.assertEqual(executor._prepared, {})

    async def test_unknown_workflow_is_rejected(self):
        executor = ComfyUIExecutor(
            transport=FakeComfyUITransport(),
            workflow_resolver=lambda ref: None,
            timeout_seconds=1.0,
            cancel_timeout_seconds=0.1,
        )

        with self.assertRaises(ComfyUIExecutorError) as caught:
            await executor.prepare(self.request())
        self.assertIn("not available", str(caught.exception))

    async def test_unknown_role_and_missing_required_role_are_rejected(self):
        executor = self.executor()

        with self.assertRaises(ComfyUIExecutorError) as caught:
            await executor.prepare(self.request(inputs=(ExecutionInput(name="caption", value="x"),)))
        self.assertIn("no input binding for role", str(caught.exception))

        with self.assertRaises(ComfyUIExecutorError) as caught:
            await executor.prepare(self.request(inputs=(ExecutionInput(name="seed", value=7),)))
        self.assertIn("missing required input role", str(caught.exception))

    async def test_declared_input_roles_map_onto_workflow_inputs(self):
        executor = self.executor()
        request = self.request(
            inputs=(ExecutionInput(name="input-1", value="a dog"),),
            config={"workflow_ref": "workflow-1@3", "input_roles": {"input-1": "prompt"}},
        )

        await executor.start(await executor.prepare(request))

        self.assertEqual(self.transport.calls[0].graph["1"]["inputs"]["text"], "a dog")

    async def test_progress_events_are_normalized(self):
        transport = FakeComfyUITransport(events=[
            ComfyUIRawEvent(kind="queued"),
            ComfyUIRawEvent(kind="executing", node_id="2", class_type="KSampler"),
            ComfyUIRawEvent(kind="progress", node_id="2", value=5, maximum=10),
            ComfyUIRawEvent(kind="completed", items=(ComfyUIOutputItem(kind="image", filename="a.png"),)),
        ])
        executor = self.executor(transport=transport)

        handle = await executor.start(await executor.prepare(self.request()))
        events = [event async for event in executor.stream(handle)]
        result = await executor.result(handle)

        self.assertEqual([event.kind for event in events], ["started", "progress", "progress", "progress", "completed"])
        self.assertEqual(events[1].message, "ComfyUI prompt queued")
        self.assertEqual(events[2].message, "ComfyUI node 2")
        self.assertEqual(events[3].message, "ComfyUI progress 50%")
        self.assertEqual(events[2].metadata["node_id"], "2")
        self.assertEqual(events[2].metadata["class_type"], "KSampler")
        self.assertEqual(result.status, "succeeded")
        await executor.cleanup(handle)

    async def test_outputs_are_normalized_by_kind_and_named_deterministically(self):
        transport = FakeComfyUITransport(events=[
            ComfyUIRawEvent(kind="output", node_id="3", items=(
                ComfyUIOutputItem(kind="image", filename="a.png", subfolder="out", url="/api/view?filename=a.png"),
                ComfyUIOutputItem(kind="text", filename="caption.txt", text="a cat", name="caption"),
            )),
            ComfyUIRawEvent(kind="completed"),
        ])
        executor = self.executor(transport=transport)

        handle = await executor.start(await executor.prepare(self.request()))
        events = [event async for event in executor.stream(handle)]
        result = await executor.result(handle)

        self.assertEqual(events[1].kind, "partial_result")
        self.assertEqual([output.name for output in result.outputs], ["image.1", "caption"])
        self.assertEqual(result.outputs[1].value, "a cat")
        self.assertEqual(
            result.outputs[0].value,
            {"kind": "image", "filename": "a.png", "subfolder": "out", "item_type": "output", "url": "/api/view?filename=a.png"},
        )
        await executor.cleanup(handle)

    async def test_failed_event_becomes_typed_failed_result(self):
        transport = FakeComfyUITransport(events=[ComfyUIRawEvent(kind="failed", message="node 2 failed")])
        executor = self.executor(transport=transport)

        handle = await executor.start(await executor.prepare(self.request()))
        events = [event async for event in executor.stream(handle)]
        result = await executor.result(handle)

        self.assertEqual((events[-1].kind, result.status, result.error), ("failed", "failed", "node 2 failed"))
        await executor.cleanup(handle)

    async def test_stream_end_without_terminal_event_completes(self):
        transport = FakeComfyUITransport(events=[
            ComfyUIRawEvent(kind="output", items=(ComfyUIOutputItem(kind="image", filename="a.png"),)),
        ])
        executor = self.executor(transport=transport)

        handle = await executor.start(await executor.prepare(self.request()))
        events = [event async for event in executor.stream(handle)]
        result = await executor.result(handle)

        self.assertEqual(events[-1].kind, "completed")
        self.assertEqual((result.status, len(result.outputs)), ("succeeded", 1))
        await executor.cleanup(handle)

    async def test_transport_failure_becomes_typed_failed_result(self):
        class FailingTransport(FakeComfyUITransport):
            async def next_event(self, submission):
                raise ComfyUITransportError("comfyui websocket closed")

        executor = self.executor(transport=FailingTransport())

        handle = await executor.start(await executor.prepare(self.request()))
        events = [event async for event in executor.stream(handle)]
        result = await executor.result(handle)

        self.assertEqual((events[-1].kind, result.status, result.error), ("failed", "failed", "comfyui websocket closed"))
        await executor.cleanup(handle)

    async def test_stream_timeout_becomes_typed_failed_result(self):
        executor = self.executor(transport=FakeComfyUITransport(hang=True), timeout_seconds=0.05)

        handle = await executor.start(await executor.prepare(self.request()))
        events = [event async for event in executor.stream(handle)]
        result = await executor.result(handle)

        self.assertEqual((events[-1].kind, events[-1].status, result.status), ("failed", "failed", "failed"))
        self.assertIn("timed out", result.error)
        await executor.cleanup(handle)

    async def test_submit_failure_reports_before_any_execution_state(self):
        executor = self.executor(transport=FakeComfyUITransport(fail_submit=True))
        prepared = await executor.prepare(self.request())

        with self.assertRaises(ComfyUIExecutorError) as caught:
            await executor.start(prepared)
        self.assertIn("comfyui rejected the prompt", str(caught.exception))

    async def test_cancel_is_explicit_repeatable_and_terminal(self):
        executor = self.executor(transport=FakeComfyUITransport(hang=True))

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
        executor = self.executor(transport=FakeComfyUITransport(hang=True))

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
        executor = self.executor(transport=FakeComfyUITransport(hang=True, accept_cancel=False))

        handle = await executor.start(await executor.prepare(self.request()))
        cancel_result = await executor.cancel(handle)
        status = await executor.status(handle)

        self.assertEqual((cancel_result.accepted, cancel_result.status, status.status), (False, "unknown", "running"))
        self.transport.release.set()
        await executor.cleanup(handle)

    async def test_prepare_start_and_unknown_execution_are_bounded(self):
        executor = self.executor()
        prepared = await executor.prepare(self.request())

        with self.assertRaises(ComfyUIExecutorError):
            await executor.prepare(self.request())
        handle = await executor.start(prepared)
        with self.assertRaises(ComfyUIExecutorError):
            await executor.start(prepared)
        with self.assertRaises(ComfyUIExecutorError):
            await executor.result(ExecutionHandle(execution_id="other", executor_ref=COMFYUI_EXECUTOR_REF))
        with self.assertRaises(ComfyUIExecutorError):
            await executor.result(ExecutionHandle(execution_id=handle.execution_id, executor_ref="codex-harness"))

        self.assertEqual((await executor.health()).status, "healthy")
        await executor.cleanup(handle)

    def test_profile_is_the_timeout_and_executor_identity_authority(self):
        profile = ExecutionProfile(
            id="profile-comfy", version=1, name="Comfy", executor_ref=COMFYUI_EXECUTOR_REF,
            timeout_seconds=12.5, cancel_timeout_seconds=1.5,
        )
        configured = ComfyUIExecutor(
            transport=FakeComfyUITransport(), workflow_resolver=lambda ref: sample_workflow(), profile=profile,
        )
        self.assertEqual((configured._timeout_seconds, configured._cancel_timeout_seconds), (12.5, 1.5))

        with self.assertRaises(ValueError):
            ComfyUIExecutor(
                transport=FakeComfyUITransport(), workflow_resolver=lambda ref: None,
                profile=profile, timeout_seconds=1,
            )
        with self.assertRaises(ValueError):
            ComfyUIExecutor(
                transport=FakeComfyUITransport(), workflow_resolver=lambda ref: None,
                profile=ExecutionProfile(id="p", version=1, name="Direct", executor_ref="direct-model"),
            )

    def test_workflow_seam_rejects_credentials_and_duplicate_roles(self):
        with self.assertRaises(ValueError):
            sample_workflow(graph={"1": {"class_type": "LoadImage", "inputs": {"api_key": "must-not-be-in-a-graph"}}})
        with self.assertRaises(ValueError):
            sample_workflow(input_bindings=(
                ComfyUIInputBinding(role="prompt", node_id="1", input_name="text"),
                ComfyUIInputBinding(role="prompt", node_id="2", input_name="seed"),
            ))
        with self.assertRaises(ValueError):
            ComfyUIOutputItem(kind="text", filename="a.txt")

    def test_seam_has_no_canvas_or_provider_sdk_dependency(self):
        root = Path(__file__).resolve().parent.parent
        violations = []
        for path in sorted((root / "workbench" / "comfyui").rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            for module in _imported_modules(path, root):
                lowered = module.lower()
                if module in FORBIDDEN_PROVIDER_SDK_IMPORTS or module.split(".")[0] in FORBIDDEN_PROVIDER_SDK_IMPORTS:
                    violations.append(f"{path.relative_to(root)} -> provider sdk {module}")
                if any(marker in lowered for marker in FORBIDDEN_BOUNDARY_MARKERS):
                    violations.append(f"{path.relative_to(root)} -> canvas/legacy {module}")
        self.assertEqual(violations, [])


class ComfyUIExecutorRegistryTests(unittest.IsolatedAsyncioTestCase):
    async def test_registry_resolves_the_comfyui_runtime_route_without_substitution(self):
        executor = ComfyUIExecutor(
            transport=FakeComfyUITransport(), workflow_resolver=lambda ref: sample_workflow(),
        )
        self.assertIsInstance(executor, Executor)
        registry = ExecutorRegistry((
            ExecutorRegistration(
                executor=executor,
                capabilities=("image",),
                runtime_routes=("comfyui",),
                execution_profiles=("profile-comfy@1",),
            ),
        ))

        resolved = registry.resolve(runtime_route_ref="comfyui", execution_profile_ref="profile-comfy@1", required_capabilities=("image",))
        provider_route = registry.resolve(runtime_route_ref="provider")

        self.assertTrue(resolved.resolved)
        self.assertEqual(resolved.executor.executor_ref, COMFYUI_EXECUTOR_REF)
        self.assertFalse(provider_route.resolved)
        self.assertEqual(provider_route.reason, "runtime_route_unavailable")


class ComfyUIExecutionServiceTests(unittest.IsolatedAsyncioTestCase):
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
            id="profile-comfy", version=1, name="Comfy", executor_ref=COMFYUI_EXECUTOR_REF,
            runtime_connection_ref="comfy-backend",
            default_params={"workflow_ref": "workflow-1@3"},
        )

    def run_record(self, run_id: str, task_id: str):
        return ExecutionRun(
            id=run_id, project_id="project-1", task_id=task_id, execution_profile_ref="profile-comfy@1",
            policy=ExecutionPolicy(),
            input_projection=ExecutionInputProjection(
                inputs=[{
                    "input_id": "input-1", "binding_id": "binding-1", "target": "workflow.prompt",
                    "role": "prompt", "order": 0, "source_type": "literal", "source_ref": "literal-1",
                    "value": "a cat", "source_snapshot": "a cat",
                }],
                parameters={"input_roles": {"input-1": "prompt"}},
            ),
            created_at=self.now,
        )

    def executor(self, transport):
        return ComfyUIExecutor(
            transport=transport,
            workflow_resolver=lambda ref: sample_workflow() if ref.ref == "workflow-1@3" else None,
            profile=self.profile(),
        )

    async def test_comfyui_backed_task_runs_without_canvas_node_dependency(self):
        self.runs.create(self.run_record("run-comfy", "skill-comfy"), actor_id="owner")
        transport = FakeComfyUITransport(events=[
            ComfyUIRawEvent(kind="executing", node_id="2", class_type="KSampler"),
            ComfyUIRawEvent(kind="output", node_id="3", items=(ComfyUIOutputItem(kind="image", filename="cat.png"),)),
            ComfyUIRawEvent(kind="completed", items=(ComfyUIOutputItem(kind="image", filename="cat_2.png"),)),
        ])
        service = ExecutionService(
            self.runs,
            self.attempts,
            actor_id="owner",
            event_service=self.events,
            id_factory=iter(["attempt-comfy", "idempotency-comfy"]).__next__,
            clock=lambda: self.now,
        )

        result = await service.execute_run("run-comfy", executor=self.executor(transport))

        self.assertEqual(result.status, "succeeded")
        self.assertEqual([output.value["filename"] for output in result.outputs], ["cat.png", "cat_2.png"])
        self.assertEqual(self.runs.get("run-comfy", actor_id="owner").status, "succeeded")
        attempt = self.attempts.get("attempt-comfy", actor_id="owner")
        self.assertEqual((attempt.status, attempt.summary["output_count"], attempt.summary["executor_ref"]), ("succeeded", 2, COMFYUI_EXECUTOR_REF))
        self.assertEqual([event.event_type for event in self.events.stream("run-comfy")], ["started", "progress", "partial_result", "completed"])
        call = transport.calls[0]
        self.assertEqual((call.workflow_ref, call.connection_ref), ("workflow-1@3", "comfy-backend"))
        self.assertEqual(call.graph["1"]["inputs"]["text"], "a cat")

    async def test_execution_service_cancel_uses_the_active_comfyui_handle(self):
        self.runs.create(self.run_record("run-cancel", "skill-comfy"), actor_id="owner")
        transport = FakeComfyUITransport(hang=True)
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

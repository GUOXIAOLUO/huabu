import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from workbench.api.execution_attempts import create_execution_attempts_router
from workbench.application.execution_attempt_service import ExecutionAttemptService
from workbench.application.execution_service import ExecutionControlRegistry, ExecutionService
from workbench.domain.execution import CancelResult, ExecutionAttempt, ExecutionHandle, ExecutionInputProjection, ExecutionPolicy, ExecutionRun
from workbench.domain.project.models import ProjectRecord
from workbench.repositories.execution_attempt_repository import ExecutionAttemptInvalidTransitionError, ExecutionAttemptStaleRevisionError, SqliteExecutionAttemptRepository
from workbench.repositories.execution_run_repository import SqliteExecutionRunRepository
from workbench.repositories.sqlite_project_canvas_repository import SqliteProjectCanvasRepository


class RunningControlExecutor:
    executor_ref = "fake-running"

    def __init__(self):
        self.calls = 0

    async def cancel(self, handle):
        self.calls += 1
        return CancelResult(execution_id=handle.execution_id, accepted=True, status="cancelled")


class ExecutionAttemptTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.database = Path(self.temp.name) / "workbench.sqlite3"
        self.now = datetime(2026, 9, 12, tzinfo=UTC)
        SqliteProjectCanvasRepository(self.database, clock=lambda: self.now).create_project(ProjectRecord(
            id="project-1", name="Project", workspace_id="local", created_by="owner",
            created_at=self.now, updated_at=self.now,
        ))
        run = ExecutionRun(
            id="run-1", project_id="project-1", task_id="task-1", execution_profile_ref="profile@1",
            policy=ExecutionPolicy(mode="batch", concurrency=2, retry=1),
            input_projection=ExecutionInputProjection(inputs=[{"input_id": "input-1", "binding_id": "binding-1", "target": "task.prompt", "role": "prompt", "order": 0, "source_type": "literal", "source_ref": "literal-1", "value": "one", "source_snapshot": "one"}]),
            created_at=self.now,
        )
        SqliteExecutionRunRepository(self.database, clock=lambda: self.now).create(run, actor_id="owner")

    def tearDown(self):
        self.temp.cleanup()

    def attempt(self, attempt_id, item_index, attempt_number):
        return ExecutionAttempt(id=attempt_id, run_id="run-1", input_id=f"input-{item_index}", item_index=item_index, attempt_number=attempt_number, created_at=self.now)

    def test_histories_are_independent_deterministic_and_persisted(self):
        repository = SqliteExecutionAttemptRepository(self.database, clock=lambda: self.now)
        repository.create(self.attempt("a-2", 0, 2), actor_id="owner")
        repository.create(self.attempt("a-1", 0, 1), actor_id="owner")
        repository.create(self.attempt("b-1", 1, 1), actor_id="owner")
        self.assertEqual([(item.item_index, item.attempt_number) for item in repository.list("run-1", actor_id="owner")], [(0, 1), (0, 2), (1, 1)])
        reopened = SqliteExecutionAttemptRepository(self.database, clock=lambda: self.now)
        self.assertEqual(reopened.get("a-2", actor_id="owner").created_at, self.now)

    def test_status_update_uses_cas_and_validates_attempt_output(self):
        repository = SqliteExecutionAttemptRepository(self.database, clock=lambda: self.now)
        repository.create(self.attempt("a-1", 0, 1), actor_id="owner")
        running = repository.update_status("a-1", status="running", expected_revision=1, actor_id="owner", started_at=self.now)
        succeeded = repository.update_status("a-1", status="succeeded", expected_revision=2, actor_id="owner", output_refs=("artifact-1",), finished_at=self.now)
        self.assertEqual((running.revision, succeeded.status, succeeded.output_refs), (2, "succeeded", ("artifact-1",)))
        with self.assertRaises(ExecutionAttemptStaleRevisionError):
            repository.update_status("a-1", status="failed", expected_revision=1, actor_id="owner")
        with self.assertRaises(ExecutionAttemptInvalidTransitionError):
            repository.update_status("a-1", status="running", expected_revision=3, actor_id="owner")
        with self.assertRaises(TypeError):
            succeeded.summary["changed"] = True

    def test_api_scopes_run_path_and_maps_cas_and_permissions(self):
        def service_factory(actor_id):
            return ExecutionAttemptService(SqliteExecutionAttemptRepository(self.database, clock=lambda: self.now), actor_id=actor_id, id_factory=lambda: "api-attempt", clock=lambda: self.now)

        app = FastAPI()
        app.include_router(create_execution_attempts_router(service_factory=service_factory))
        client = TestClient(app)
        headers = {"X-User-ID": "owner"}
        created = client.post("/api/v1/execution-runs/run-1/attempts", headers=headers, json={"input_id": "input-1", "item_index": 0, "attempt_number": 1})
        self.assertEqual((created.status_code, created.json()["run_id"], created.json()["revision"]), (201, "run-1", 1))
        self.assertEqual(client.get("/api/v1/execution-runs/run-1/attempts", headers=headers).status_code, 200)
        self.assertEqual(client.get("/api/v1/execution-runs/other-run/attempts/api-attempt", headers=headers).status_code, 404)
        changed = client.patch("/api/v1/execution-runs/run-1/attempts/api-attempt/status", headers=headers, json={"expected_revision": 1, "status": "running"})
        self.assertEqual((changed.status_code, changed.json()["status"]), (200, "running"))
        self.assertEqual(client.patch("/api/v1/execution-runs/run-1/attempts/api-attempt/status", headers=headers, json={"expected_revision": 1, "status": "failed"}).status_code, 409)
        self.assertEqual(client.get("/api/v1/execution-runs/run-1/attempts", headers={"X-User-ID": "viewer"}).status_code, 403)

    def test_api_exposes_application_cancel_and_retry_controls(self):
        repository = SqliteExecutionAttemptRepository(self.database, clock=lambda: self.now)
        repository.create(self.attempt("failed-attempt", 0, 1).model_copy(update={"status": "failed"}), actor_id="owner")

        def service_factory(actor_id):
            return ExecutionAttemptService(SqliteExecutionAttemptRepository(self.database, clock=lambda: self.now), actor_id=actor_id, id_factory=lambda: "api-control", clock=lambda: self.now)

        def execution_service_factory(actor_id):
            return ExecutionService(SqliteExecutionRunRepository(self.database, clock=lambda: self.now), SqliteExecutionAttemptRepository(self.database, clock=lambda: self.now), actor_id=actor_id, id_factory=lambda: "api-control", clock=lambda: self.now)

        app = FastAPI()
        app.include_router(create_execution_attempts_router(service_factory=service_factory, execution_service_factory=execution_service_factory))
        client = TestClient(app)
        headers = {"X-User-ID": "owner"}
        retried = client.post("/api/v1/execution-runs/run-1/attempts/failed-attempt/retry", headers=headers)
        self.assertEqual((retried.status_code, retried.json()["attempt_number"], retried.json()["status"]), (201, 2, "prepared"))
        cancelled = client.post("/api/v1/execution-runs/run-1/attempts/api-control/cancel", headers=headers)
        self.assertEqual((cancelled.status_code, cancelled.json()["status"]), (200, "cancelled"))

    def test_api_cancel_resolves_running_executor_from_shared_control_registry(self):
        repository = SqliteExecutionAttemptRepository(self.database, clock=lambda: self.now)
        running = self.attempt("running-attempt", 1, 1).model_copy(update={"status": "running"})
        repository.create(running, actor_id="owner")
        executor = RunningControlExecutor()
        handle = ExecutionHandle(execution_id=running.id, executor_ref=executor.executor_ref)
        registry = ExecutionControlRegistry({running.id: (executor, handle)})

        def service_factory(actor_id):
            return ExecutionAttemptService(SqliteExecutionAttemptRepository(self.database, clock=lambda: self.now), actor_id=actor_id)

        def execution_service_factory(actor_id):
            return ExecutionService(
                SqliteExecutionRunRepository(self.database, clock=lambda: self.now),
                SqliteExecutionAttemptRepository(self.database, clock=lambda: self.now),
                actor_id=actor_id,
                control_registry=registry,
                clock=lambda: self.now,
            )

        app = FastAPI()
        app.include_router(create_execution_attempts_router(service_factory=service_factory, execution_service_factory=execution_service_factory))
        response = TestClient(app).post(
            f"/api/v1/execution-runs/run-1/attempts/{running.id}/cancel",
            headers={"X-User-ID": "owner"},
        )

        self.assertEqual((response.status_code, response.json()["status"], executor.calls), (200, "cancelled", 1))


if __name__ == "__main__":
    unittest.main()

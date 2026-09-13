import tempfile
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from workbench.api.execution_runs import create_execution_runs_router
from workbench.application.execution_input_projection import ExecutionInputProjection
from workbench.application.execution_run_service import ExecutionRunService
from workbench.application.execution_service import ExecutionService
from workbench.domain.execution import ExecutionPolicy, ExecutionRun
from workbench.domain.project.models import ProjectRecord
from workbench.repositories.execution_run_repository import ExecutionRunRepositoryError, ExecutionRunStaleRevisionError, SqliteExecutionRunRepository
from workbench.repositories.execution_attempt_repository import SqliteExecutionAttemptRepository
from workbench.repositories.sqlite_project_canvas_repository import SqliteProjectCanvasRepository


class ExecutionRunTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.database = Path(self.temp.name) / "workbench.sqlite3"
        self.now = datetime(2026, 9, 12, tzinfo=UTC)
        SqliteProjectCanvasRepository(self.database, clock=lambda: self.now).create_project(ProjectRecord(
            id="project-1", name="Project", workspace_id="local", created_by="owner",
            created_at=self.now, updated_at=self.now,
        ))

    def tearDown(self):
        self.temp.cleanup()

    def projection(self, value="before"):
        return ExecutionInputProjection(inputs=[{
            "input_id": "input-1", "binding_id": "binding-1", "target": "task.prompt",
            "role": "prompt", "order": 0, "source_type": "literal", "source_ref": "literal-1",
            "value": value, "source_snapshot": value,
        }])

    def test_run_snapshot_is_immutable_and_survives_repository_reopen(self):
        repository = SqliteExecutionRunRepository(self.database, clock=lambda: self.now)
        run = ExecutionRun(id="run-1", project_id="project-1", task_id="task-1", execution_profile_ref="profile@1", policy=ExecutionPolicy(mode="batch", concurrency=2), input_projection=self.projection(), created_at=self.now)
        repository.create(run, actor_id="owner")
        reopened = SqliteExecutionRunRepository(self.database, clock=lambda: self.now + timedelta(seconds=1))
        restored = reopened.get("run-1", actor_id="owner")
        self.assertEqual(restored, run)
        with self.assertRaises(ValidationError):
            run.status = "running"
        with self.assertRaises(TypeError):
            run.summary["changed"] = True
        with self.assertRaises(TypeError):
            run.input_projection.inputs[0].value["changed"] = True

    def test_status_update_preserves_snapshot_and_rejects_stale_revision(self):
        repository = SqliteExecutionRunRepository(self.database, clock=lambda: self.now)
        run = ExecutionRun(id="run-1", project_id="project-1", task_id="task-1", execution_profile_ref="profile@1", policy=ExecutionPolicy(), input_projection=self.projection(), created_at=self.now)
        repository.create(run, actor_id="owner")
        updated = repository.update_status("run-1", status="running", expected_revision=1, actor_id="owner", started_at=self.now)
        self.assertEqual((updated.status, updated.revision, updated.input_projection), ("running", 2, run.input_projection))
        with self.assertRaises(ExecutionRunStaleRevisionError):
            repository.update_status("run-1", status="failed", expected_revision=1, actor_id="owner")
        with self.assertRaises(ExecutionRunRepositoryError):
            repository.update_status("run-1", status="prepared", expected_revision=2, actor_id="owner")

    def test_api_create_list_get_and_status_survive_reopen(self):
        def service_factory(actor_id):
            return ExecutionRunService(SqliteExecutionRunRepository(self.database, clock=lambda: self.now), actor_id=actor_id, id_factory=lambda: "run-api", clock=lambda: self.now)

        app = FastAPI()
        app.include_router(create_execution_runs_router(service_factory=service_factory))
        client = TestClient(app)
        payload = {"project_id": "project-1", "task_id": "task-1", "execution_profile_ref": "profile@1", "policy": {"mode": "single"}, "input_projection": self.projection().model_dump(mode="json")}
        created = client.post("/api/v1/execution-runs", headers={"X-User-ID": "owner"}, json=payload)
        self.assertEqual((created.status_code, created.json()["status"], created.json()["revision"]), (201, "prepared", 1))
        run_id = created.json()["id"]
        listed = client.get("/api/v1/execution-runs", params={"project_id": "project-1"}, headers={"X-User-ID": "owner"})
        self.assertEqual((listed.status_code, len(listed.json())), (200, 1))
        changed = client.patch(f"/api/v1/execution-runs/{run_id}/status", headers={"X-User-ID": "owner"}, json={"expected_revision": 1, "status": "running"})
        self.assertEqual((changed.status_code, changed.json()["status"], changed.json()["revision"]), (200, "running", 2))
        stale = client.patch(f"/api/v1/execution-runs/{run_id}/status", headers={"X-User-ID": "owner"}, json={"expected_revision": 1, "status": "failed"})
        self.assertEqual(stale.status_code, 409)
        invalid = client.patch(f"/api/v1/execution-runs/{run_id}/status", headers={"X-User-ID": "owner"}, json={"expected_revision": 2, "status": "prepared"})
        self.assertEqual(invalid.status_code, 400)
        self.assertEqual(client.get(f"/api/v1/execution-runs/{run_id}", headers={"X-User-ID": "viewer"}).status_code, 403)

    def test_api_cancel_unknown_run_returns_not_found(self):
        app = FastAPI()
        app.include_router(create_execution_runs_router(
            service_factory=lambda actor_id: ExecutionRunService(SqliteExecutionRunRepository(self.database, clock=lambda: self.now), actor_id=actor_id),
            execution_service_factory=lambda actor_id: ExecutionService(
                SqliteExecutionRunRepository(self.database, clock=lambda: self.now),
                SqliteExecutionAttemptRepository(self.database, clock=lambda: self.now),
                actor_id=actor_id,
            ),
        ))
        response = TestClient(app).post("/api/v1/execution-runs/missing/cancel", headers={"X-User-ID": "owner"})
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()

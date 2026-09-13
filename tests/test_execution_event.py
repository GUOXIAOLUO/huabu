import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from workbench.api.execution_events import create_execution_events_router
from workbench.application.execution_event_service import ExecutionEventService
from workbench.domain.execution import ExecutionEventRecord, ExecutionInputProjection, ExecutionPolicy, ExecutionRun
from workbench.domain.project.models import ProjectRecord
from workbench.repositories.execution_event_repository import ExecutionEventSequenceConflictError, SqliteExecutionEventRepository
from workbench.repositories.execution_run_repository import SqliteExecutionRunRepository
from workbench.repositories.sqlite_project_canvas_repository import SqliteProjectCanvasRepository


class ExecutionEventTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.database = Path(self.temp.name) / "workbench.sqlite3"
        self.now = datetime(2026, 9, 12, tzinfo=UTC)
        SqliteProjectCanvasRepository(self.database, clock=lambda: self.now).create_project(ProjectRecord(
            id="project-1", name="Project", workspace_id="local", created_by="owner", created_at=self.now, updated_at=self.now,
        ))
        run = ExecutionRun(
            id="run-1", project_id="project-1", task_id="task-1", execution_profile_ref="profile@1",
            policy=ExecutionPolicy(), input_projection=ExecutionInputProjection(inputs=[]), created_at=self.now,
        )
        SqliteExecutionRunRepository(self.database, clock=lambda: self.now).create(run, actor_id="owner")

    def tearDown(self):
        self.temp.cleanup()

    def event(self, event_id, sequence, event_type="progress"):
        return ExecutionEventRecord(id=event_id, run_id="run-1", sequence=sequence, event_type=event_type, payload={"sequence": sequence}, occurred_at=self.now)

    def test_normalized_events_are_durable_ordered_and_pollable_after_restart(self):
        repository = SqliteExecutionEventRepository(self.database, clock=lambda: self.now)
        repository.append(self.event("event-1", 1, "started"), actor_id="owner")
        repository.append(self.event("event-2", 2), actor_id="owner")
        with self.assertRaises(ExecutionEventSequenceConflictError):
            repository.append(self.event("event-3", 2), actor_id="owner")
        reopened = SqliteExecutionEventRepository(self.database, clock=lambda: self.now)
        self.assertEqual([event.sequence for event in reopened.list("run-1", actor_id="owner")], [1, 2])
        self.assertEqual([event.sequence for event in reopened.list("run-1", actor_id="owner", after_sequence=1)], [2])

    def test_retention_keeps_latest_bounded_window(self):
        repository = SqliteExecutionEventRepository(self.database, clock=lambda: self.now, max_events_per_run=2)
        for sequence in range(1, 4):
            repository.append(self.event(f"event-{sequence}", sequence), actor_id="owner")
        self.assertEqual([event.sequence for event in repository.list("run-1", actor_id="owner")], [2, 3])

    def test_api_appends_and_polls_with_permission_and_conflict_mapping(self):
        def service_factory(actor_id):
            return ExecutionEventService(SqliteExecutionEventRepository(self.database, clock=lambda: self.now), actor_id=actor_id, id_factory=lambda: "api-event", clock=lambda: self.now)

        app = FastAPI()
        app.include_router(create_execution_events_router(service_factory=service_factory))
        client = TestClient(app)
        owner = {"X-User-ID": "owner"}
        created = client.post("/api/v1/execution-runs/run-1/events", headers=owner, json={"sequence": 1, "event_type": "started", "payload": {"source": "normalized"}})
        self.assertEqual((created.status_code, created.json()["sequence"]), (201, 1))
        self.assertEqual(client.get("/api/v1/execution-runs/run-1/events", headers=owner).json()[0]["event_type"], "started")
        conflict = client.post("/api/v1/execution-runs/run-1/events", headers=owner, json={"sequence": 1, "event_type": "progress"})
        self.assertEqual(conflict.status_code, 409)
        self.assertEqual(client.get("/api/v1/execution-runs/run-1/events", headers={"X-User-ID": "viewer"}).status_code, 403)


if __name__ == "__main__":
    unittest.main()

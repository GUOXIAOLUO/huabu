"""Canonical SQLite persistence for project-owned ExecutionRun records."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Callable, Iterator, Protocol

from workbench.application.authorization import Action, AuthorizationService
from workbench.domain.execution import ExecutionRun, ExecutionRunStatus
from workbench.repositories.sqlite_project_canvas_repository import SqliteProjectCanvasRepository


class ExecutionRunRepositoryError(RuntimeError):
    pass


class ExecutionRunNotFoundError(ExecutionRunRepositoryError):
    pass


class ExecutionRunStaleRevisionError(ExecutionRunRepositoryError):
    def __init__(self, current_revision: int):
        self.current_revision = current_revision
        super().__init__(f"execution run revision is stale; current revision is {current_revision}")


class ExecutionRunInvalidTransitionError(ExecutionRunRepositoryError):
    pass


class _MembershipReader:
    def __init__(self, connection: sqlite3.Connection):
        self._connection = connection

    def member_role(self, project_id: str, actor_id: str) -> str | None:
        row = self._connection.execute(
            "SELECT role FROM project_members WHERE project_id = ? AND actor_id = ?",
            (project_id, actor_id),
        ).fetchone()
        return row["role"] if row else None


class ExecutionRunRepository(Protocol):
    def create(self, run: ExecutionRun, *, actor_id: str) -> ExecutionRun: ...
    def get(self, run_id: str, *, actor_id: str) -> ExecutionRun: ...
    def list(self, project_id: str, *, actor_id: str) -> list[ExecutionRun]: ...
    def update_status(self, run_id: str, *, status: ExecutionRunStatus, expected_revision: int, actor_id: str, started_at: datetime | None = None, finished_at: datetime | None = None, summary: dict[str, object] | None = None) -> ExecutionRun: ...


class SqliteExecutionRunRepository:
    def __init__(self, database_path: str | Path, *, clock: Callable[[], datetime] | None = None):
        self._database_path = Path(database_path)
        self._clock = clock or (lambda: datetime.now(UTC))
        self._projects = SqliteProjectCanvasRepository(self._database_path, clock=self._clock)
        self.migrate()

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        self._database_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self._database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def migrate(self) -> None:
        self._projects.migrate()
        with self._connection() as connection:
            connection.execute(
                """CREATE TABLE IF NOT EXISTS execution_runs (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    status TEXT NOT NULL,
                    revision INTEGER NOT NULL CHECK (revision >= 1),
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(project_id) REFERENCES projects(id)
                )"""
            )
            connection.execute("CREATE INDEX IF NOT EXISTS idx_execution_runs_project ON execution_runs(project_id, created_at, id)")

    @staticmethod
    def _decode(row: sqlite3.Row) -> ExecutionRun:
        return ExecutionRun.model_validate(json.loads(row["payload_json"]))

    def _authorize(self, connection: sqlite3.Connection, actor_id: str, action: Action, project_id: str) -> None:
        AuthorizationService(_MembershipReader(connection)).require(actor_id, action, project_id)

    def _audit(self, connection: sqlite3.Connection, *, event_type: str, run: ExecutionRun, actor_id: str) -> None:
        connection.execute(
            "INSERT INTO audit_outbox(event_type, project_id, canvas_id, actor_id, payload_json, occurred_at) VALUES (?, ?, NULL, ?, ?, ?)",
            (event_type, run.project_id, actor_id, json.dumps({"run_id": run.id, "revision": run.revision, "status": run.status}, sort_keys=True), self._clock().isoformat()),
        )

    def create(self, run: ExecutionRun, *, actor_id: str) -> ExecutionRun:
        with self._connection() as connection:
            self._authorize(connection, actor_id, Action.EXECUTION_EDIT, run.project_id)
            payload = json.dumps(run.model_dump(mode="json"), ensure_ascii=False, sort_keys=True)
            now = self._clock().isoformat()
            try:
                connection.execute("INSERT INTO execution_runs (id, project_id, payload_json, status, revision, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)", (run.id, run.project_id, payload, run.status, run.revision, run.created_at.isoformat(), now))
            except sqlite3.IntegrityError as error:
                raise ExecutionRunRepositoryError(f"execution run already exists: {run.id}") from error
            self._audit(connection, event_type="execution.run.created", run=run, actor_id=actor_id)
            return run

    def get(self, run_id: str, *, actor_id: str) -> ExecutionRun:
        with self._connection() as connection:
            row = connection.execute("SELECT * FROM execution_runs WHERE id = ?", (run_id,)).fetchone()
            if row is None:
                raise ExecutionRunNotFoundError(run_id)
            self._authorize(connection, actor_id, Action.EXECUTION_READ, row["project_id"])
            return self._decode(row)

    def list(self, project_id: str, *, actor_id: str) -> list[ExecutionRun]:
        with self._connection() as connection:
            self._authorize(connection, actor_id, Action.EXECUTION_READ, project_id)
            rows = connection.execute("SELECT * FROM execution_runs WHERE project_id = ? ORDER BY created_at, id", (project_id,)).fetchall()
            return [self._decode(row) for row in rows]

    def update_status(self, run_id: str, *, status: ExecutionRunStatus, expected_revision: int, actor_id: str, started_at: datetime | None = None, finished_at: datetime | None = None, summary: dict[str, object] | None = None) -> ExecutionRun:
        with self._connection() as connection:
            row = connection.execute("SELECT * FROM execution_runs WHERE id = ?", (run_id,)).fetchone()
            if row is None:
                raise ExecutionRunNotFoundError(run_id)
            self._authorize(connection, actor_id, Action.EXECUTION_EDIT, row["project_id"])
            if row["revision"] != expected_revision:
                raise ExecutionRunStaleRevisionError(row["revision"])
            current = self._decode(row)
            if not current.can_transition_to(status):
                raise ExecutionRunInvalidTransitionError(f"invalid execution run status transition: {current.status} -> {status}")
            updated = current.model_copy(update={"status": status, "started_at": started_at if started_at is not None else current.started_at, "finished_at": finished_at if finished_at is not None else current.finished_at, "summary": summary if summary is not None else current.summary, "revision": expected_revision + 1})
            payload = json.dumps(updated.model_dump(mode="json"), ensure_ascii=False, sort_keys=True)
            result = connection.execute("UPDATE execution_runs SET payload_json = ?, status = ?, revision = ?, updated_at = ? WHERE id = ? AND revision = ?", (payload, status, updated.revision, self._clock().isoformat(), run_id, expected_revision))
            if result.rowcount != 1:
                current_row = connection.execute("SELECT revision FROM execution_runs WHERE id = ?", (run_id,)).fetchone()
                raise ExecutionRunStaleRevisionError(current_row["revision"] if current_row else expected_revision)
            self._audit(connection, event_type="execution.run.status_updated", run=updated, actor_id=actor_id)
            return updated

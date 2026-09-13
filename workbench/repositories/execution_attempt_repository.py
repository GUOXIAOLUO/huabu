"""Canonical SQLite persistence for per-item ExecutionAttempt records."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Callable, Iterator, Protocol

from workbench.application.authorization import Action, AuthorizationService
from workbench.domain.execution import ExecutionAttempt, ExecutionAttemptStatus, ExecutionRun
from workbench.repositories.execution_run_repository import SqliteExecutionRunRepository


class ExecutionAttemptRepositoryError(RuntimeError):
    pass


class ExecutionAttemptNotFoundError(ExecutionAttemptRepositoryError):
    pass


class ExecutionAttemptStaleRevisionError(ExecutionAttemptRepositoryError):
    def __init__(self, current_revision: int):
        self.current_revision = current_revision
        super().__init__(f"execution attempt revision is stale; current revision is {current_revision}")


class ExecutionAttemptInvalidTransitionError(ExecutionAttemptRepositoryError):
    pass


class ExecutionAttemptRetryConflictError(ExecutionAttemptRepositoryError):
    pass


class _MembershipReader:
    def __init__(self, connection: sqlite3.Connection):
        self._connection = connection

    def member_role(self, project_id: str, actor_id: str) -> str | None:
        row = self._connection.execute("SELECT role FROM project_members WHERE project_id = ? AND actor_id = ?", (project_id, actor_id)).fetchone()
        return row["role"] if row else None


class ExecutionAttemptRepository(Protocol):
    def create(self, attempt: ExecutionAttempt, *, actor_id: str) -> ExecutionAttempt: ...
    def get(self, attempt_id: str, *, actor_id: str) -> ExecutionAttempt: ...
    def list(self, run_id: str, *, actor_id: str) -> list[ExecutionAttempt]: ...
    def create_retry(self, attempt: ExecutionAttempt, *, source_attempt_id: str, expected_source_revision: int, expected_run_revision: int, actor_id: str) -> ExecutionAttempt: ...
    def update_status(self, attempt_id: str, *, status: ExecutionAttemptStatus, expected_revision: int, actor_id: str, retry_count: int | None = None, error: str | None = None, output_refs: tuple[str, ...] | None = None, started_at: datetime | None = None, finished_at: datetime | None = None, summary: dict[str, object] | None = None) -> ExecutionAttempt: ...


class SqliteExecutionAttemptRepository:
    def __init__(self, database_path: str | Path, *, clock: Callable[[], datetime] | None = None):
        self._database_path = Path(database_path)
        self._clock = clock or (lambda: datetime.now(UTC))
        self._runs = SqliteExecutionRunRepository(self._database_path, clock=self._clock)
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
        self._runs.migrate()
        with self._connection() as connection:
            connection.execute("""CREATE TABLE IF NOT EXISTS execution_attempts (
                id TEXT PRIMARY KEY, run_id TEXT NOT NULL, item_index INTEGER NOT NULL CHECK (item_index >= 0),
                attempt_number INTEGER NOT NULL CHECK (attempt_number >= 1), payload_json TEXT NOT NULL,
                status TEXT NOT NULL, revision INTEGER NOT NULL CHECK (revision >= 1),
                created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
                UNIQUE(run_id, item_index, attempt_number),
                FOREIGN KEY(run_id) REFERENCES execution_runs(id)
            )""")
            connection.execute("CREATE INDEX IF NOT EXISTS idx_execution_attempts_run ON execution_attempts(run_id, item_index, attempt_number, id)")

    @staticmethod
    def _decode(row: sqlite3.Row) -> ExecutionAttempt:
        return ExecutionAttempt.model_validate(json.loads(row["payload_json"]))

    @staticmethod
    def _project_id(connection: sqlite3.Connection, run_id: str) -> str:
        row = connection.execute("SELECT project_id FROM execution_runs WHERE id = ?", (run_id,)).fetchone()
        if row is None: raise ExecutionAttemptNotFoundError(f"execution run not found: {run_id}")
        return row["project_id"]

    def _authorize(self, connection: sqlite3.Connection, actor_id: str, action: Action, project_id: str) -> None:
        AuthorizationService(_MembershipReader(connection)).require(actor_id, action, project_id)

    def _audit(self, connection: sqlite3.Connection, *, event_type: str, run_id: str, actor_id: str, payload: dict[str, object]) -> None:
        connection.execute(
            "INSERT INTO audit_outbox(event_type, project_id, canvas_id, actor_id, payload_json, occurred_at) VALUES (?, ?, NULL, ?, ?, ?)",
            (event_type, self._project_id(connection, run_id), actor_id, json.dumps(payload, sort_keys=True), self._clock().isoformat()),
        )

    def create(self, attempt: ExecutionAttempt, *, actor_id: str) -> ExecutionAttempt:
        with self._connection() as connection:
            self._authorize(connection, actor_id, Action.EXECUTION_EDIT, self._project_id(connection, attempt.run_id))
            payload = json.dumps(attempt.model_dump(mode="json"), ensure_ascii=False, sort_keys=True)
            now = self._clock().isoformat()
            try:
                connection.execute("INSERT INTO execution_attempts (id, run_id, item_index, attempt_number, payload_json, status, revision, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (attempt.id, attempt.run_id, attempt.item_index, attempt.attempt_number, payload, attempt.status, attempt.revision, attempt.created_at.isoformat(), now))
            except sqlite3.IntegrityError as error:
                raise ExecutionAttemptRepositoryError(f"execution attempt already exists: {attempt.id}") from error
            self._audit(connection, event_type="execution.attempt.created", run_id=attempt.run_id, actor_id=actor_id, payload={"attempt_id": attempt.id, "revision": attempt.revision, "status": attempt.status})
            return attempt

    def get(self, attempt_id: str, *, actor_id: str) -> ExecutionAttempt:
        with self._connection() as connection:
            row = connection.execute("SELECT * FROM execution_attempts WHERE id = ?", (attempt_id,)).fetchone()
            if row is None: raise ExecutionAttemptNotFoundError(attempt_id)
            self._authorize(connection, actor_id, Action.EXECUTION_READ, self._project_id(connection, row["run_id"]))
            return self._decode(row)

    def list(self, run_id: str, *, actor_id: str) -> list[ExecutionAttempt]:
        with self._connection() as connection:
            self._authorize(connection, actor_id, Action.EXECUTION_READ, self._project_id(connection, run_id))
            rows = connection.execute("SELECT * FROM execution_attempts WHERE run_id = ? ORDER BY item_index, attempt_number, id", (run_id,)).fetchall()
            return [self._decode(row) for row in rows]

    def create_retry(self, attempt: ExecutionAttempt, *, source_attempt_id: str, expected_source_revision: int, expected_run_revision: int, actor_id: str) -> ExecutionAttempt:
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            source_row = connection.execute("SELECT * FROM execution_attempts WHERE id = ?", (source_attempt_id,)).fetchone()
            if source_row is None:
                raise ExecutionAttemptNotFoundError(source_attempt_id)
            self._authorize(connection, actor_id, Action.EXECUTION_EDIT, self._project_id(connection, source_row["run_id"]))
            run_row = connection.execute("SELECT status, revision, payload_json FROM execution_runs WHERE id = ?", (source_row["run_id"],)).fetchone()
            if run_row is None:
                raise ExecutionAttemptNotFoundError(f"execution run not found: {source_row['run_id']}")
            if run_row["revision"] != expected_run_revision:
                raise ExecutionAttemptRetryConflictError("execution run changed while retrying")
            if run_row["status"] in {"succeeded", "cancelled"}:
                raise ExecutionAttemptRetryConflictError("terminal execution runs cannot create retry attempts")
            if source_row["revision"] != expected_source_revision:
                raise ExecutionAttemptStaleRevisionError(source_row["revision"])
            source = self._decode(source_row)
            if source.status != "failed":
                raise ExecutionAttemptRetryConflictError("only failed attempts can be retried")
            if attempt.status != "prepared" or attempt.revision != 1 or attempt.retry_count != attempt.attempt_number - 1 or attempt.error is not None or attempt.output_refs or attempt.started_at is not None or attempt.finished_at is not None or attempt.summary or attempt.run_id != source.run_id or attempt.input_id != source.input_id or attempt.item_index != source.item_index or attempt.attempt_number != source.attempt_number + 1:
                raise ExecutionAttemptRetryConflictError("retry attempt does not continue the failed item history")
            newer = connection.execute(
                "SELECT 1 FROM execution_attempts WHERE run_id = ? AND item_index = ? AND attempt_number > ? LIMIT 1",
                (source.run_id, source.item_index, source.attempt_number),
            ).fetchone()
            if newer is not None:
                raise ExecutionAttemptRetryConflictError("a newer attempt already exists for this item")
            payload = json.dumps(attempt.model_dump(mode="json"), ensure_ascii=False, sort_keys=True)
            now = self._clock().isoformat()
            try:
                connection.execute("INSERT INTO execution_attempts (id, run_id, item_index, attempt_number, payload_json, status, revision, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (attempt.id, attempt.run_id, attempt.item_index, attempt.attempt_number, payload, attempt.status, attempt.revision, attempt.created_at.isoformat(), now))
            except sqlite3.IntegrityError as error:
                raise ExecutionAttemptRetryConflictError("execution retry conflicts with an existing attempt") from error
            run = ExecutionRun.model_validate(json.loads(run_row["payload_json"]))
            updated_run = run.model_copy(update={"status": "queued" if run.status == "failed" else run.status, "finished_at": None if run.status == "failed" else run.finished_at, "revision": expected_run_revision + 1})
            updated_run_payload = json.dumps(updated_run.model_dump(mode="json"), ensure_ascii=False, sort_keys=True)
            result = connection.execute("UPDATE execution_runs SET payload_json = ?, revision = ?, updated_at = ? WHERE id = ? AND revision = ?", (updated_run_payload, updated_run.revision, self._clock().isoformat(), run.id, expected_run_revision))
            if result.rowcount != 1:
                raise ExecutionAttemptRetryConflictError("execution run changed while retrying")
            self._audit(connection, event_type="execution.attempt.retry_created", run_id=attempt.run_id, actor_id=actor_id, payload={"attempt_id": attempt.id, "source_attempt_id": source_attempt_id, "revision": attempt.revision, "status": attempt.status})
            self._audit(connection, event_type="execution.run.retry_reserved", run_id=attempt.run_id, actor_id=actor_id, payload={"attempt_id": attempt.id, "revision": updated_run.revision, "status": updated_run.status})
            return attempt

    def update_status(self, attempt_id: str, *, status: ExecutionAttemptStatus, expected_revision: int, actor_id: str, retry_count: int | None = None, error: str | None = None, output_refs: tuple[str, ...] | None = None, started_at: datetime | None = None, finished_at: datetime | None = None, summary: dict[str, object] | None = None) -> ExecutionAttempt:
        with self._connection() as connection:
            row = connection.execute("SELECT * FROM execution_attempts WHERE id = ?", (attempt_id,)).fetchone()
            if row is None: raise ExecutionAttemptNotFoundError(attempt_id)
            self._authorize(connection, actor_id, Action.EXECUTION_EDIT, self._project_id(connection, row["run_id"]))
            if row["revision"] != expected_revision: raise ExecutionAttemptStaleRevisionError(row["revision"])
            current = self._decode(row)
            transitions = {"prepared": {"running", "cancelled"}, "running": {"succeeded", "failed", "cancelled"}, "succeeded": set(), "failed": set(), "cancelled": set()}
            if status != current.status and status not in transitions[current.status]: raise ExecutionAttemptInvalidTransitionError(f"invalid execution attempt status transition: {current.status} -> {status}")
            updated_payload = current.model_dump(mode="python")
            updated_payload.update({"status": status, "retry_count": retry_count if retry_count is not None else current.retry_count, "error": error if error is not None else current.error, "output_refs": output_refs if output_refs is not None else current.output_refs, "started_at": started_at if started_at is not None else current.started_at, "finished_at": finished_at if finished_at is not None else current.finished_at, "summary": summary if summary is not None else current.summary, "revision": expected_revision + 1})
            updated = ExecutionAttempt.model_validate(updated_payload)
            payload = json.dumps(updated.model_dump(mode="json"), ensure_ascii=False, sort_keys=True)
            result = connection.execute("UPDATE execution_attempts SET payload_json = ?, status = ?, revision = ?, updated_at = ? WHERE id = ? AND revision = ?", (payload, status, updated.revision, self._clock().isoformat(), attempt_id, expected_revision))
            if result.rowcount != 1:
                latest = connection.execute("SELECT revision FROM execution_attempts WHERE id = ?", (attempt_id,)).fetchone()
                raise ExecutionAttemptStaleRevisionError(latest["revision"] if latest else expected_revision)
            self._audit(connection, event_type="execution.attempt.status_updated", run_id=current.run_id, actor_id=actor_id, payload={"attempt_id": current.id, "from_status": current.status, "status": updated.status, "revision": updated.revision})
            return updated

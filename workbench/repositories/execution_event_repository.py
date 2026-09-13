"""Canonical SQLite persistence and polling for normalized execution events."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Callable, Iterator, Protocol

from workbench.application.authorization import Action, AuthorizationService
from workbench.domain.execution.event import ExecutionEventRecord
from workbench.repositories.execution_attempt_repository import SqliteExecutionAttemptRepository
from workbench.repositories.execution_run_repository import SqliteExecutionRunRepository


class ExecutionEventRepositoryError(RuntimeError):
    pass


class ExecutionEventNotFoundError(ExecutionEventRepositoryError):
    pass


class ExecutionEventSequenceConflictError(ExecutionEventRepositoryError):
    pass


class _MembershipReader:
    def __init__(self, connection: sqlite3.Connection):
        self._connection = connection

    def member_role(self, project_id: str, actor_id: str) -> str | None:
        row = self._connection.execute("SELECT role FROM project_members WHERE project_id = ? AND actor_id = ?", (project_id, actor_id)).fetchone()
        return row["role"] if row else None


class ExecutionEventRepository(Protocol):
    def append(self, event: ExecutionEventRecord, *, actor_id: str) -> ExecutionEventRecord: ...
    def list(self, run_id: str, *, actor_id: str, after_sequence: int = 0, limit: int = 200) -> list[ExecutionEventRecord]: ...


class SqliteExecutionEventRepository:
    def __init__(self, database_path: str | Path, *, clock: Callable[[], datetime] | None = None, max_events_per_run: int = 1000):
        if max_events_per_run < 1:
            raise ValueError("max_events_per_run must be positive")
        self._database_path = Path(database_path)
        self._clock = clock or (lambda: datetime.now(UTC))
        self._runs = SqliteExecutionRunRepository(self._database_path, clock=self._clock)
        self._attempts = SqliteExecutionAttemptRepository(self._database_path, clock=self._clock)
        self._max_events_per_run = max_events_per_run
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
        self._attempts.migrate()
        with self._connection() as connection:
            connection.execute("""CREATE TABLE IF NOT EXISTS execution_events (
                id TEXT PRIMARY KEY, run_id TEXT NOT NULL, attempt_id TEXT,
                sequence INTEGER NOT NULL CHECK (sequence >= 1), payload_json TEXT NOT NULL,
                event_type TEXT NOT NULL, occurred_at TEXT NOT NULL, created_at TEXT NOT NULL,
                UNIQUE(run_id, sequence),
                FOREIGN KEY(run_id) REFERENCES execution_runs(id),
                FOREIGN KEY(attempt_id) REFERENCES execution_attempts(id)
            )""")
            connection.execute("CREATE INDEX IF NOT EXISTS idx_execution_events_run_sequence ON execution_events(run_id, sequence)")

    @staticmethod
    def _decode(row: sqlite3.Row) -> ExecutionEventRecord:
        return ExecutionEventRecord.model_validate(json.loads(row["payload_json"]))

    @staticmethod
    def _project_id(connection: sqlite3.Connection, run_id: str) -> str:
        row = connection.execute("SELECT project_id FROM execution_runs WHERE id = ?", (run_id,)).fetchone()
        if row is None:
            raise ExecutionEventNotFoundError(f"execution run not found: {run_id}")
        return row["project_id"]

    def _authorize(self, connection: sqlite3.Connection, actor_id: str, action: Action, project_id: str) -> None:
        AuthorizationService(_MembershipReader(connection)).require(actor_id, action, project_id)

    def append(self, event: ExecutionEventRecord, *, actor_id: str) -> ExecutionEventRecord:
        with self._connection() as connection:
            self._authorize(connection, actor_id, Action.EXECUTION_EDIT, self._project_id(connection, event.run_id))
            latest = connection.execute("SELECT MAX(sequence) AS sequence FROM execution_events WHERE run_id = ?", (event.run_id,)).fetchone()["sequence"]
            if latest is not None and event.sequence <= latest:
                raise ExecutionEventSequenceConflictError(f"execution event sequence must increase: {event.run_id}/{event.sequence} after {latest}")
            if event.attempt_id is not None:
                attempt = connection.execute("SELECT run_id FROM execution_attempts WHERE id = ?", (event.attempt_id,)).fetchone()
                if attempt is None or attempt["run_id"] != event.run_id:
                    raise ExecutionEventNotFoundError(f"execution attempt not found for run: {event.attempt_id}")
            payload = json.dumps(event.model_dump(mode="json"), ensure_ascii=False, sort_keys=True)
            now = self._clock().isoformat()
            try:
                connection.execute("INSERT INTO execution_events (id, run_id, attempt_id, sequence, payload_json, event_type, occurred_at, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (event.id, event.run_id, event.attempt_id, event.sequence, payload, event.event_type, event.occurred_at.isoformat(), now))
            except sqlite3.IntegrityError as error:
                raise ExecutionEventSequenceConflictError(f"execution event sequence already exists: {event.run_id}/{event.sequence}") from error
            connection.execute("DELETE FROM execution_events WHERE run_id = ? AND sequence NOT IN (SELECT sequence FROM execution_events WHERE run_id = ? ORDER BY sequence DESC LIMIT ?)", (event.run_id, event.run_id, self._max_events_per_run))
            return event

    def list(self, run_id: str, *, actor_id: str, after_sequence: int = 0, limit: int = 200) -> list[ExecutionEventRecord]:
        if after_sequence < 0 or limit < 1:
            raise ValueError("after_sequence must be non-negative and limit must be positive")
        with self._connection() as connection:
            self._authorize(connection, actor_id, Action.EXECUTION_READ, self._project_id(connection, run_id))
            rows = connection.execute("SELECT * FROM execution_events WHERE run_id = ? AND sequence > ? ORDER BY sequence LIMIT ?", (run_id, after_sequence, limit)).fetchall()
            return [self._decode(row) for row in rows]

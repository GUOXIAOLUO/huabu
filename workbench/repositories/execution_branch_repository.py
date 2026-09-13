"""Canonical SQLite persistence for execution branch lineage records."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Callable, Iterator, Protocol

from workbench.application.authorization import Action, AuthorizationService
from workbench.domain.execution import ExecutionBranch
from workbench.repositories.execution_run_repository import SqliteExecutionRunRepository


class ExecutionBranchRepositoryError(RuntimeError):
    pass


class ExecutionBranchNotFoundError(ExecutionBranchRepositoryError):
    pass


class ExecutionBranchConflictError(ExecutionBranchRepositoryError):
    pass


class _MembershipReader:
    def __init__(self, connection: sqlite3.Connection):
        self._connection = connection

    def member_role(self, project_id: str, actor_id: str) -> str | None:
        row = self._connection.execute("SELECT role FROM project_members WHERE project_id = ? AND actor_id = ?", (project_id, actor_id)).fetchone()
        return row["role"] if row else None


class ExecutionBranchRepository(Protocol):
    def create(self, branch: ExecutionBranch, *, actor_id: str) -> ExecutionBranch: ...
    def get(self, branch_id: str, *, actor_id: str) -> ExecutionBranch: ...
    def get_for_run(self, run_id: str, *, actor_id: str) -> ExecutionBranch: ...
    def list_children(self, source_run_id: str, *, actor_id: str) -> list[ExecutionBranch]: ...
    def list_lineage(self, run_id: str, *, actor_id: str) -> list[ExecutionBranch]: ...


class SqliteExecutionBranchRepository:
    # A run has at most one origin, so the walk up the lineage is bounded.
    MAX_LINEAGE_DEPTH = 64

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
            connection.execute("""CREATE TABLE IF NOT EXISTS execution_branches (
                id TEXT PRIMARY KEY, project_id TEXT NOT NULL, run_id TEXT NOT NULL,
                source_run_id TEXT NOT NULL, payload_json TEXT NOT NULL,
                revision INTEGER NOT NULL CHECK (revision >= 1),
                created_at TEXT NOT NULL,
                UNIQUE(run_id),
                FOREIGN KEY(run_id) REFERENCES execution_runs(id),
                FOREIGN KEY(source_run_id) REFERENCES execution_runs(id)
            )""")
            connection.execute("CREATE INDEX IF NOT EXISTS idx_execution_branches_source ON execution_branches(source_run_id, created_at, id)")

    @staticmethod
    def _decode(row: sqlite3.Row) -> ExecutionBranch:
        return ExecutionBranch.model_validate(json.loads(row["payload_json"]))

    def _project_id(self, connection: sqlite3.Connection, run_id: str) -> str:
        row = connection.execute("SELECT project_id FROM execution_runs WHERE id = ?", (run_id,)).fetchone()
        if row is None:
            raise ExecutionBranchNotFoundError(f"execution run not found: {run_id}")
        return row["project_id"]

    def _authorize(self, connection: sqlite3.Connection, actor_id: str, action: Action, project_id: str) -> None:
        AuthorizationService(_MembershipReader(connection)).require(actor_id, action, project_id)

    def _audit(self, connection: sqlite3.Connection, *, event_type: str, project_id: str, actor_id: str, payload: dict[str, object]) -> None:
        connection.execute(
            "INSERT INTO audit_outbox(event_type, project_id, canvas_id, actor_id, payload_json, occurred_at) VALUES (?, ?, NULL, ?, ?, ?)",
            (event_type, project_id, actor_id, json.dumps(payload, sort_keys=True), self._clock().isoformat()),
        )

    def create(self, branch: ExecutionBranch, *, actor_id: str) -> ExecutionBranch:
        with self._connection() as connection:
            project_id = self._project_id(connection, branch.source_run_id)
            if project_id != branch.project_id:
                raise ExecutionBranchConflictError("a branch may not cross projects")
            self._authorize(connection, actor_id, Action.EXECUTION_EDIT, project_id)
            payload = json.dumps(branch.model_dump(mode="json"), ensure_ascii=False, sort_keys=True)
            try:
                connection.execute(
                    "INSERT INTO execution_branches (id, project_id, run_id, source_run_id, payload_json, revision, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (branch.id, branch.project_id, branch.run_id, branch.source_run_id, payload, branch.revision, branch.created_at.isoformat()),
                )
            except sqlite3.IntegrityError as error:
                raise ExecutionBranchConflictError(f"this run already has a lineage: {branch.run_id}") from error
            self._audit(connection, event_type="execution.branch.created", project_id=project_id, actor_id=actor_id, payload={
                "branch_id": branch.id, "run_id": branch.run_id, "source_run_id": branch.source_run_id,
                "kind": branch.kind, "has_result_lineage": branch.has_result_lineage(),
            })
            return branch

    def get(self, branch_id: str, *, actor_id: str) -> ExecutionBranch:
        with self._connection() as connection:
            row = connection.execute("SELECT * FROM execution_branches WHERE id = ?", (branch_id,)).fetchone()
            if row is None:
                raise ExecutionBranchNotFoundError(branch_id)
            self._authorize(connection, actor_id, Action.EXECUTION_READ, row["project_id"])
            return self._decode(row)

    def get_for_run(self, run_id: str, *, actor_id: str) -> ExecutionBranch:
        with self._connection() as connection:
            row = connection.execute("SELECT * FROM execution_branches WHERE run_id = ?", (run_id,)).fetchone()
            if row is None:
                raise ExecutionBranchNotFoundError(run_id)
            self._authorize(connection, actor_id, Action.EXECUTION_READ, row["project_id"])
            return self._decode(row)

    def list_children(self, source_run_id: str, *, actor_id: str) -> list[ExecutionBranch]:
        with self._connection() as connection:
            self._authorize(connection, actor_id, Action.EXECUTION_READ, self._project_id(connection, source_run_id))
            rows = connection.execute("SELECT * FROM execution_branches WHERE source_run_id = ? ORDER BY created_at, id", (source_run_id,)).fetchall()
            return [self._decode(row) for row in rows]

    def list_lineage(self, run_id: str, *, actor_id: str) -> list[ExecutionBranch]:
        """The chain of branches from the root-most ancestor down to this run."""
        with self._connection() as connection:
            self._authorize(connection, actor_id, Action.EXECUTION_READ, self._project_id(connection, run_id))
            chain: list[ExecutionBranch] = []
            seen: set[str] = set()
            cursor = run_id
            for _ in range(self.MAX_LINEAGE_DEPTH):
                row = connection.execute("SELECT * FROM execution_branches WHERE run_id = ?", (cursor,)).fetchone()
                if row is None:
                    break
                branch = self._decode(row)
                if branch.id in seen:
                    break
                seen.add(branch.id)
                chain.append(branch)
                cursor = branch.source_run_id
            return list(reversed(chain))

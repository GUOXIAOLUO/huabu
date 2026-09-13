"""Canonical SQLite persistence for per-result ResultSelection records."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Callable, Iterator, Protocol

from workbench.application.authorization import Action, AuthorizationService
from workbench.domain.execution import ResultSelection
from workbench.repositories.execution_run_repository import SqliteExecutionRunRepository


class ResultSelectionRepositoryError(RuntimeError):
    pass


class ResultSelectionNotFoundError(ResultSelectionRepositoryError):
    pass


class ResultSelectionConflictError(ResultSelectionRepositoryError):
    pass


class ResultSelectionStaleRevisionError(ResultSelectionRepositoryError):
    def __init__(self, current_revision: int):
        self.current_revision = current_revision
        super().__init__(f"result selection revision is stale; current revision is {current_revision}")


class _MembershipReader:
    def __init__(self, connection: sqlite3.Connection):
        self._connection = connection

    def member_role(self, project_id: str, actor_id: str) -> str | None:
        row = self._connection.execute("SELECT role FROM project_members WHERE project_id = ? AND actor_id = ?", (project_id, actor_id)).fetchone()
        return row["role"] if row else None


class ResultSelectionRepository(Protocol):
    def create(self, selection: ResultSelection, *, actor_id: str) -> ResultSelection: ...
    def get(self, selection_id: str, *, actor_id: str) -> ResultSelection: ...
    def list_for_run(self, run_id: str, *, actor_id: str) -> list[ResultSelection]: ...
    def update(self, selection_id: str, *, expected_revision: int, actor_id: str, selected: bool, favorite: bool, rating: int | None, comment: str, metadata: dict[str, object]) -> ResultSelection: ...


class SqliteResultSelectionRepository:
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
            connection.execute("""CREATE TABLE IF NOT EXISTS result_selections (
                id TEXT PRIMARY KEY, run_id TEXT NOT NULL, attempt_id TEXT NOT NULL,
                output_name TEXT NOT NULL, ordinal INTEGER NOT NULL CHECK (ordinal >= 0),
                payload_json TEXT NOT NULL, revision INTEGER NOT NULL CHECK (revision >= 1),
                created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
                UNIQUE(attempt_id, output_name, ordinal),
                FOREIGN KEY(run_id) REFERENCES execution_runs(id)
            )""")
            connection.execute("CREATE INDEX IF NOT EXISTS idx_result_selections_run ON result_selections(run_id, attempt_id, output_name, ordinal, id)")

    @staticmethod
    def _decode(row: sqlite3.Row) -> ResultSelection:
        return ResultSelection.model_validate(json.loads(row["payload_json"]))

    def _project_id(self, connection: sqlite3.Connection, run_id: str) -> str:
        row = connection.execute("SELECT project_id FROM execution_runs WHERE id = ?", (run_id,)).fetchone()
        if row is None:
            raise ResultSelectionNotFoundError(f"execution run not found: {run_id}")
        return row["project_id"]

    def _authorize(self, connection: sqlite3.Connection, actor_id: str, action: Action, project_id: str) -> None:
        AuthorizationService(_MembershipReader(connection)).require(actor_id, action, project_id)

    def _audit(self, connection: sqlite3.Connection, *, event_type: str, run_id: str, actor_id: str, payload: dict[str, object]) -> None:
        connection.execute(
            "INSERT INTO audit_outbox(event_type, project_id, canvas_id, actor_id, payload_json, occurred_at) VALUES (?, ?, NULL, ?, ?, ?)",
            (event_type, self._project_id(connection, run_id), actor_id, json.dumps(payload, sort_keys=True), self._clock().isoformat()),
        )

    def create(self, selection: ResultSelection, *, actor_id: str) -> ResultSelection:
        with self._connection() as connection:
            self._authorize(connection, actor_id, Action.EXECUTION_EDIT, self._project_id(connection, selection.run_id))
            payload = json.dumps(selection.model_dump(mode="json"), ensure_ascii=False, sort_keys=True)
            now = self._clock().isoformat()
            try:
                connection.execute(
                    "INSERT INTO result_selections (id, run_id, attempt_id, output_name, ordinal, payload_json, revision, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (selection.id, selection.run_id, selection.attempt_id, selection.output_name, selection.ordinal, payload, selection.revision, selection.created_at.isoformat(), now),
                )
            except sqlite3.IntegrityError as error:
                raise ResultSelectionConflictError(f"result selection already exists for this result: {selection.attempt_id}:{selection.output_name}:{selection.ordinal}") from error
            self._audit(connection, event_type="execution.result_selection.created", run_id=selection.run_id, actor_id=actor_id, payload={"selection_id": selection.id, "attempt_id": selection.attempt_id, "output_name": selection.output_name, "ordinal": selection.ordinal, "revision": selection.revision})
            return selection

    def get(self, selection_id: str, *, actor_id: str) -> ResultSelection:
        with self._connection() as connection:
            row = connection.execute("SELECT * FROM result_selections WHERE id = ?", (selection_id,)).fetchone()
            if row is None:
                raise ResultSelectionNotFoundError(selection_id)
            self._authorize(connection, actor_id, Action.EXECUTION_READ, self._project_id(connection, row["run_id"]))
            return self._decode(row)

    def list_for_run(self, run_id: str, *, actor_id: str) -> list[ResultSelection]:
        with self._connection() as connection:
            self._authorize(connection, actor_id, Action.EXECUTION_READ, self._project_id(connection, run_id))
            rows = connection.execute("SELECT * FROM result_selections WHERE run_id = ? ORDER BY attempt_id, output_name, ordinal, id", (run_id,)).fetchall()
            return [self._decode(row) for row in rows]

    def update(self, selection_id: str, *, expected_revision: int, actor_id: str, selected: bool, favorite: bool, rating: int | None, comment: str, metadata: dict[str, object]) -> ResultSelection:
        with self._connection() as connection:
            row = connection.execute("SELECT * FROM result_selections WHERE id = ?", (selection_id,)).fetchone()
            if row is None:
                raise ResultSelectionNotFoundError(selection_id)
            self._authorize(connection, actor_id, Action.EXECUTION_EDIT, self._project_id(connection, row["run_id"]))
            if row["revision"] != expected_revision:
                raise ResultSelectionStaleRevisionError(row["revision"])
            current = self._decode(row)
            # The caller restates the whole preference, so a cleared rating is a
            # real value rather than an ambiguous "leave unchanged". Identity is
            # fixed at creation: an update can only restate the user's
            # preference, never re-point the record at another result.
            updated_payload = current.model_dump(mode="python")
            updated_payload.update({
                "selected": selected,
                "favorite": favorite,
                "rating": rating,
                "comment": comment,
                "metadata": metadata,
                "updated_at": self._clock(),
                "revision": expected_revision + 1,
            })
            updated = ResultSelection.model_validate(updated_payload)
            payload = json.dumps(updated.model_dump(mode="json"), ensure_ascii=False, sort_keys=True)
            result = connection.execute(
                "UPDATE result_selections SET payload_json = ?, revision = ?, updated_at = ? WHERE id = ? AND revision = ?",
                (payload, updated.revision, self._clock().isoformat(), selection_id, expected_revision),
            )
            if result.rowcount != 1:
                latest = connection.execute("SELECT revision FROM result_selections WHERE id = ?", (selection_id,)).fetchone()
                raise ResultSelectionStaleRevisionError(latest["revision"] if latest else expected_revision)
            self._audit(connection, event_type="execution.result_selection.updated", run_id=current.run_id, actor_id=actor_id, payload={"selection_id": current.id, "attempt_id": current.attempt_id, "output_name": current.output_name, "ordinal": current.ordinal, "revision": updated.revision, "has_preference": updated.has_preference()})
            return updated

"""Canonical SQLite persistence for project-owned Collections."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Callable, Iterator, Protocol

from workbench.application.authorization import Action, AuthorizationService
from workbench.domain.collection import Collection
from workbench.repositories.sqlite_project_canvas_repository import SqliteProjectCanvasRepository


class CollectionRepositoryError(RuntimeError):
    pass


class CollectionNotFoundError(CollectionRepositoryError):
    pass


class CollectionStaleRevisionError(CollectionRepositoryError):
    def __init__(self, current_revision: int):
        self.current_revision = current_revision
        super().__init__(f"collection revision is stale; current revision is {current_revision}")


class _MembershipReader:
    def __init__(self, connection: sqlite3.Connection):
        self._connection = connection

    def member_role(self, project_id: str, actor_id: str) -> str | None:
        row = self._connection.execute(
            "SELECT role FROM project_members WHERE project_id = ? AND actor_id = ?",
            (project_id, actor_id),
        ).fetchone()
        return row["role"] if row else None


class CollectionRepository(Protocol):
    def create(self, collection: Collection, *, actor_id: str) -> Collection: ...
    def get(self, collection_id: str, *, actor_id: str) -> Collection: ...
    def list(self, project_id: str, *, actor_id: str) -> list[Collection]: ...
    def replace(self, collection: Collection, *, expected_revision: int, actor_id: str) -> Collection: ...
    def delete(self, collection_id: str, *, actor_id: str) -> None: ...


class SqliteCollectionRepository:
    """Store the validated Collection aggregate as the canonical JSON payload."""

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
                """CREATE TABLE IF NOT EXISTS collections (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    revision INTEGER NOT NULL CHECK (revision >= 1),
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(project_id) REFERENCES projects(id)
                )"""
            )
            connection.execute("CREATE INDEX IF NOT EXISTS idx_collections_project ON collections(project_id, id)")

    def _authorize(self, connection: sqlite3.Connection, actor_id: str, action: Action, project_id: str) -> None:
        AuthorizationService(_MembershipReader(connection)).require(actor_id, action, project_id)

    @staticmethod
    def _decode(row: sqlite3.Row) -> Collection:
        return Collection.model_validate(json.loads(row["payload_json"]))

    def _audit(self, connection: sqlite3.Connection, event_type: str, collection: Collection, actor_id: str) -> None:
        connection.execute(
            "INSERT INTO audit_outbox(event_type, project_id, canvas_id, actor_id, payload_json, occurred_at) VALUES (?, ?, NULL, ?, ?, ?)",
            (event_type, collection.project_id, actor_id, json.dumps({"collection_id": collection.id, "revision": collection.revision}, sort_keys=True), self._clock().isoformat()),
        )

    def create(self, collection: Collection, *, actor_id: str) -> Collection:
        with self._connection() as connection:
            self._authorize(connection, actor_id, Action.COLLECTION_EDIT, collection.project_id)
            now = self._clock().isoformat()
            payload = json.dumps(collection.model_dump(mode="json", by_alias=True), ensure_ascii=False, sort_keys=True)
            try:
                connection.execute(
                    "INSERT INTO collections (id, project_id, payload_json, revision, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                    (collection.id, collection.project_id, payload, collection.revision, now, now),
                )
            except sqlite3.IntegrityError as error:
                raise CollectionRepositoryError(f"collection already exists: {collection.id}") from error
            self._audit(connection, "collection.created", collection, actor_id)
            return collection

    def get(self, collection_id: str, *, actor_id: str) -> Collection:
        with self._connection() as connection:
            row = connection.execute("SELECT * FROM collections WHERE id = ?", (collection_id,)).fetchone()
            if row is None:
                raise CollectionNotFoundError(collection_id)
            self._authorize(connection, actor_id, Action.COLLECTION_READ, row["project_id"])
            return self._decode(row)

    def list(self, project_id: str, *, actor_id: str) -> list[Collection]:
        with self._connection() as connection:
            self._authorize(connection, actor_id, Action.COLLECTION_READ, project_id)
            rows = connection.execute("SELECT * FROM collections WHERE project_id = ? ORDER BY id", (project_id,)).fetchall()
            return [self._decode(row) for row in rows]

    def replace(self, collection: Collection, *, expected_revision: int, actor_id: str) -> Collection:
        with self._connection() as connection:
            row = connection.execute("SELECT * FROM collections WHERE id = ?", (collection.id,)).fetchone()
            if row is None:
                raise CollectionNotFoundError(collection.id)
            self._authorize(connection, actor_id, Action.COLLECTION_EDIT, row["project_id"])
            if collection.project_id != row["project_id"]:
                raise CollectionRepositoryError("collection project cannot change")
            if row["revision"] != expected_revision:
                raise CollectionStaleRevisionError(row["revision"])
            updated = collection.model_copy(update={"revision": expected_revision + 1})
            payload = json.dumps(updated.model_dump(mode="json", by_alias=True), ensure_ascii=False, sort_keys=True)
            result = connection.execute(
                "UPDATE collections SET payload_json = ?, revision = ?, updated_at = ? WHERE id = ? AND revision = ?",
                (payload, updated.revision, self._clock().isoformat(), collection.id, expected_revision),
            )
            if result.rowcount != 1:
                current = connection.execute("SELECT revision FROM collections WHERE id = ?", (collection.id,)).fetchone()
                raise CollectionStaleRevisionError(current["revision"] if current else expected_revision)
            self._audit(connection, "collection.updated", updated, actor_id)
            return updated

    def delete(self, collection_id: str, *, actor_id: str) -> None:
        with self._connection() as connection:
            row = connection.execute("SELECT project_id FROM collections WHERE id = ?", (collection_id,)).fetchone()
            if row is None:
                raise CollectionNotFoundError(collection_id)
            self._authorize(connection, actor_id, Action.COLLECTION_EDIT, row["project_id"])
            collection = self._decode(connection.execute("SELECT * FROM collections WHERE id = ?", (collection_id,)).fetchone())
            connection.execute("DELETE FROM collections WHERE id = ?", (collection_id,))
            self._audit(connection, "collection.deleted", collection, actor_id)

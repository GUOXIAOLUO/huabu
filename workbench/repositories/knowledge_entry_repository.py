"""Canonical SQLite persistence and project-scoped queries for KnowledgeEntry."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from workbench.application.authorization import Action, AuthorizationService
from workbench.domain.knowledge import KnowledgeEntry
from workbench.repositories.sqlite_project_canvas_repository import SqliteProjectCanvasRepository


class KnowledgeEntryRepositoryError(RuntimeError):
    pass


class KnowledgeEntryNotFoundError(KnowledgeEntryRepositoryError):
    pass


class KnowledgeEntryConflictError(KnowledgeEntryRepositoryError):
    pass


class _MembershipReader:
    def __init__(self, connection: sqlite3.Connection):
        self._connection = connection

    def member_role(self, project_id: str, actor_id: str) -> str | None:
        row = self._connection.execute(
            "SELECT role FROM project_members WHERE project_id=? AND actor_id=?",
            (project_id, actor_id),
        ).fetchone()
        return row["role"] if row else None


class SqliteKnowledgeEntryRepository:
    """The sole KnowledgeEntry persistence owner; source refs remain explicit ids."""

    def __init__(self, database_path: str | Path):
        self._database_path = Path(database_path)
        self._projects = SqliteProjectCanvasRepository(self._database_path)
        self.migrate()

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        self._database_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self._database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
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
                """
                CREATE TABLE IF NOT EXISTS knowledge_entries (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    FOREIGN KEY(project_id) REFERENCES projects(id)
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_knowledge_entries_project ON knowledge_entries(project_id, id)"
            )

    @staticmethod
    def _authorize(connection: sqlite3.Connection, actor_id: str, action: Action, project_id: str) -> None:
        AuthorizationService(_MembershipReader(connection)).require(actor_id, action, project_id)

    @staticmethod
    def _dump(entry: KnowledgeEntry) -> str:
        return json.dumps(entry.model_dump(mode="json"), ensure_ascii=False, sort_keys=True)

    def create(self, entry: KnowledgeEntry, *, actor_id: str) -> KnowledgeEntry:
        with self._connection() as connection:
            self._authorize(connection, actor_id, Action.PROJECT_EDIT, entry.project_id)
            try:
                connection.execute(
                    "INSERT INTO knowledge_entries(id,project_id,payload_json) VALUES(?,?,?)",
                    (entry.id, entry.project_id, self._dump(entry)),
                )
            except sqlite3.IntegrityError as error:
                raise KnowledgeEntryConflictError(entry.id) from error
        return entry

    def get(self, entry_id: str, *, actor_id: str) -> KnowledgeEntry:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT project_id,payload_json FROM knowledge_entries WHERE id=?", (entry_id,)
            ).fetchone()
            if row is None:
                raise KnowledgeEntryNotFoundError(entry_id)
            self._authorize(connection, actor_id, Action.PROJECT_READ, row["project_id"])
            return KnowledgeEntry.model_validate(json.loads(row["payload_json"]))

    def search(
        self, project_id: str, *, actor_id: str, query: str | None = None,
        tag: str | None = None, scope: str | None = None, source_ref: str | None = None,
    ) -> list[KnowledgeEntry]:
        with self._connection() as connection:
            self._authorize(connection, actor_id, Action.PROJECT_READ, project_id)
            rows = connection.execute(
                "SELECT payload_json FROM knowledge_entries WHERE project_id=? ORDER BY id", (project_id,)
            ).fetchall()
        entries = [KnowledgeEntry.model_validate(json.loads(row["payload_json"])) for row in rows]
        needle = query.strip().casefold() if query else ""
        source_needle = source_ref.strip() if source_ref else ""
        return [entry for entry in entries if (
            (not needle or needle in " ".join((
                entry.content or "",
                json.dumps(entry.structured_payload or {}, ensure_ascii=False),
                json.dumps(entry.metadata or {}, ensure_ascii=False),
                " ".join(entry.tags),
                " ".join(entry.source_refs),
                entry.scope,
            )).casefold())
            and (not tag or tag in entry.tags)
            and (not scope or scope == entry.scope)
            and (not source_needle or source_needle in entry.source_refs)
        )]

    def list(
        self, project_id: str, *, actor_id: str, query: str | None = None,
        tag: str | None = None, scope: str | None = None,
    ) -> list[KnowledgeEntry]:
        """Compatibility alias for callers that only need the project listing."""
        return self.search(project_id, actor_id=actor_id, query=query, tag=tag, scope=scope)

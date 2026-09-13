"""Canonical SQLite persistence for project-owned Prompts and versions."""

from __future__ import annotations

import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Callable, Iterator, Protocol

from workbench.application.authorization import Action, AuthorizationService
from workbench.domain.prompt import PromptDefinition, PromptVersion
from workbench.repositories.sqlite_project_canvas_repository import SqliteProjectCanvasRepository


class PromptRepositoryError(RuntimeError):
    pass


class PromptNotFoundError(PromptRepositoryError):
    pass


class PromptVersionNotFoundError(PromptRepositoryError):
    pass


class PromptRepository(Protocol):
    def list(self, project_id: str, *, actor_id: str) -> list[PromptDefinition]: ...
    def create(self, definition: PromptDefinition, version: PromptVersion, *, actor_id: str) -> PromptDefinition: ...
    def get(self, prompt_id: str, *, actor_id: str) -> PromptDefinition: ...
    def resolve(self, prompt_id: str, version: int, *, actor_id: str) -> PromptVersion: ...
    def create_version(self, prompt_id: str, content: str, metadata: dict, *, actor_id: str) -> PromptVersion: ...


class _MembershipReader:
    def __init__(self, connection: sqlite3.Connection):
        self._connection = connection

    def member_role(self, project_id: str, actor_id: str) -> str | None:
        row = self._connection.execute("SELECT role FROM project_members WHERE project_id=? AND actor_id=?", (project_id, actor_id)).fetchone()
        return row["role"] if row else None


class SqlitePromptRepository:
    """Persist Prompt identity and append-only versions with project authorization."""

    def __init__(self, database_path: str | Path, *, clock: Callable[[], datetime] | None = None, id_factory: Callable[[], str] | None = None):
        self._database_path = Path(database_path)
        self._clock = clock or (lambda: datetime.now(UTC))
        self._id_factory = id_factory or (lambda: uuid.uuid4().hex)
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
            connection.execute("""CREATE TABLE IF NOT EXISTS prompt_definitions (
                id TEXT PRIMARY KEY, project_id TEXT NOT NULL, payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
                FOREIGN KEY(project_id) REFERENCES projects(id)
            )""")
            connection.execute("""CREATE TABLE IF NOT EXISTS prompt_versions (
                prompt_id TEXT NOT NULL, version INTEGER NOT NULL CHECK(version >= 1),
                payload_json TEXT NOT NULL, created_at TEXT NOT NULL,
                PRIMARY KEY(prompt_id, version),
                FOREIGN KEY(prompt_id) REFERENCES prompt_definitions(id)
            )""")
            connection.execute("CREATE INDEX IF NOT EXISTS idx_prompt_definitions_project ON prompt_definitions(project_id, id)")

    def _authorize(self, connection: sqlite3.Connection, actor_id: str, action: Action, project_id: str) -> None:
        AuthorizationService(_MembershipReader(connection)).require(actor_id, action, project_id)

    @staticmethod
    def _definition(row: sqlite3.Row) -> PromptDefinition:
        return PromptDefinition.model_validate(json.loads(row["payload_json"]))

    @staticmethod
    def _version(row: sqlite3.Row) -> PromptVersion:
        return PromptVersion.model_validate(json.loads(row["payload_json"]))

    def create(self, definition: PromptDefinition, version: PromptVersion, *, actor_id: str) -> PromptDefinition:
        if version.prompt_id != definition.id or version.version != 1:
            raise PromptRepositoryError("initial PromptVersion must belong to Prompt and be version 1")
        with self._connection() as connection:
            self._authorize(connection, actor_id, Action.PROMPT_EDIT, definition.project_id)
            now = self._clock().isoformat()
            connection.execute("INSERT INTO prompt_definitions VALUES (?, ?, ?, ?, ?)", (definition.id, definition.project_id, definition.model_dump_json(), now, now))
            connection.execute("INSERT INTO prompt_versions VALUES (?, ?, ?, ?)", (version.prompt_id, version.version, version.model_dump_json(), now))
            connection.execute("INSERT INTO audit_outbox(event_type, project_id, canvas_id, actor_id, payload_json, occurred_at) VALUES (?, ?, NULL, ?, ?, ?)", ("prompt.created", definition.project_id, actor_id, json.dumps({"prompt_id": definition.id, "version": 1}), now))
            return definition

    def list(self, project_id: str, *, actor_id: str) -> list[PromptDefinition]:
        with self._connection() as connection:
            self._authorize(connection, actor_id, Action.PROMPT_READ, project_id)
            rows = connection.execute(
                "SELECT * FROM prompt_definitions WHERE project_id=? ORDER BY id",
                (project_id,),
            ).fetchall()
            definitions = []
            for row in rows:
                definition = self._definition(row)
                latest = connection.execute(
                    "SELECT MAX(version) AS version FROM prompt_versions WHERE prompt_id=?",
                    (definition.id,),
                ).fetchone()["version"]
                definitions.append(definition.model_copy(update={"current_version": int(latest or definition.current_version)}))
            return definitions

    def get(self, prompt_id: str, *, actor_id: str) -> PromptDefinition:
        with self._connection() as connection:
            row = connection.execute("SELECT * FROM prompt_definitions WHERE id=?", (prompt_id,)).fetchone()
            if row is None: raise PromptNotFoundError(prompt_id)
            self._authorize(connection, actor_id, Action.PROMPT_READ, row["project_id"])
            current = self._definition(row)
            latest = connection.execute("SELECT MAX(version) AS version FROM prompt_versions WHERE prompt_id=?", (prompt_id,)).fetchone()["version"]
            return current.model_copy(update={"current_version": int(latest or current.current_version)})

    def resolve(self, prompt_id: str, version: int, *, actor_id: str) -> PromptVersion:
        with self._connection() as connection:
            row = connection.execute("SELECT d.project_id, v.* FROM prompt_definitions d JOIN prompt_versions v ON v.prompt_id=d.id WHERE d.id=? AND v.version=?", (prompt_id, version)).fetchone()
            if row is None: raise PromptVersionNotFoundError(f"{prompt_id}:{version}")
            self._authorize(connection, actor_id, Action.PROMPT_READ, row["project_id"])
            return self._version(row)

    def create_version(self, prompt_id: str, content: str, metadata: dict, *, actor_id: str) -> PromptVersion:
        with self._connection() as connection:
            row = connection.execute("SELECT project_id FROM prompt_definitions WHERE id=?", (prompt_id,)).fetchone()
            if row is None: raise PromptNotFoundError(prompt_id)
            self._authorize(connection, actor_id, Action.PROMPT_EDIT, row["project_id"])
            current = connection.execute("SELECT COALESCE(MAX(version), 0) + 1 AS version FROM prompt_versions WHERE prompt_id=?", (prompt_id,)).fetchone()["version"]
            version = PromptVersion(prompt_id=prompt_id, version=int(current), content=content, created_by=actor_id, created_at=self._clock(), metadata=metadata)
            now = self._clock().isoformat()
            connection.execute("INSERT INTO prompt_versions VALUES (?, ?, ?, ?)", (prompt_id, version.version, version.model_dump_json(), now))
            connection.execute("UPDATE prompt_definitions SET updated_at=? WHERE id=?", (now, prompt_id))
            connection.execute("INSERT INTO audit_outbox(event_type, project_id, canvas_id, actor_id, payload_json, occurred_at) VALUES (?, ?, NULL, ?, ?, ?)", ("prompt.version_created", row["project_id"], actor_id, json.dumps({"prompt_id": prompt_id, "version": version.version}), now))
            return version

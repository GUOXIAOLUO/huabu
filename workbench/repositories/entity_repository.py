"""Canonical SQLite persistence for Entities and immutable EntityVersions."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from workbench.application.authorization import Action, AuthorizationService
from workbench.domain.entity import EntityRecord, EntityVersion
from workbench.repositories.sqlite_project_canvas_repository import SqliteProjectCanvasRepository


class EntityRepositoryError(RuntimeError):
    pass


class EntityNotFoundError(EntityRepositoryError):
    pass


class EntityConflictError(EntityRepositoryError):
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


class SqliteEntityRepository:
    """Project-authorized repository; version rows are append-only snapshots."""

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
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS entities (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    FOREIGN KEY(project_id) REFERENCES projects(id)
                );
                CREATE TABLE IF NOT EXISTS entity_versions (
                    id TEXT PRIMARY KEY,
                    entity_id TEXT NOT NULL,
                    project_id TEXT NOT NULL,
                    ordinal INTEGER NOT NULL,
                    payload_json TEXT NOT NULL,
                    UNIQUE(entity_id, ordinal),
                    FOREIGN KEY(entity_id) REFERENCES entities(id),
                    FOREIGN KEY(project_id) REFERENCES projects(id)
                );
                CREATE INDEX IF NOT EXISTS idx_entity_versions_entity
                    ON entity_versions(entity_id, ordinal);
                """
            )

    @staticmethod
    def _authorize(connection: sqlite3.Connection, actor_id: str, action: Action, project_id: str) -> None:
        AuthorizationService(_MembershipReader(connection)).require(actor_id, action, project_id)

    @staticmethod
    def _dump(value) -> str:
        return json.dumps(value.model_dump(mode="json"), ensure_ascii=False, sort_keys=True)

    def create(self, entity: EntityRecord, *, actor_id: str) -> EntityRecord:
        with self._connection() as connection:
            self._authorize(connection, actor_id, Action.PROJECT_EDIT, entity.project_id)
            try:
                connection.execute(
                    "INSERT INTO entities(id,project_id,payload_json) VALUES(?,?,?)",
                    (entity.id, entity.project_id, self._dump(entity)),
                )
            except sqlite3.IntegrityError as error:
                raise EntityConflictError(entity.id) from error
        return entity

    def create_with_version(
        self, entity: EntityRecord, version: EntityVersion, *, actor_id: str
    ) -> tuple[EntityRecord, EntityVersion]:
        if version.entity_id != entity.id or version.project_id != entity.project_id or version.ordinal != 1:
            raise EntityConflictError("the first entity version must belong to the new entity")
        projected = entity.model_copy(update={
            "properties": version.payload.properties,
            "state": version.payload.state,
            "metadata": version.payload.metadata,
        }).with_version(version.id)
        with self._connection() as connection:
            self._authorize(connection, actor_id, Action.PROJECT_EDIT, entity.project_id)
            try:
                connection.execute(
                    "INSERT INTO entities(id,project_id,payload_json) VALUES(?,?,?)",
                    (entity.id, entity.project_id, self._dump(projected)),
                )
                connection.execute(
                    "INSERT INTO entity_versions(id,entity_id,project_id,ordinal,payload_json) VALUES(?,?,?,?,?)",
                    (version.id, version.entity_id, version.project_id, version.ordinal, self._dump(version)),
                )
            except sqlite3.IntegrityError as error:
                raise EntityConflictError(entity.id) from error
        return projected, version

    def get(self, entity_id: str, *, actor_id: str) -> EntityRecord:
        with self._connection() as connection:
            row = connection.execute("SELECT * FROM entities WHERE id=?", (entity_id,)).fetchone()
            if row is None:
                raise EntityNotFoundError(entity_id)
            self._authorize(connection, actor_id, Action.PROJECT_READ, row["project_id"])
            return EntityRecord.model_validate(json.loads(row["payload_json"]))

    def list(self, project_id: str, *, actor_id: str) -> list[EntityRecord]:
        with self._connection() as connection:
            self._authorize(connection, actor_id, Action.PROJECT_READ, project_id)
            rows = connection.execute(
                "SELECT payload_json FROM entities WHERE project_id=? ORDER BY id", (project_id,)
            ).fetchall()
            return [EntityRecord.model_validate(json.loads(row["payload_json"])) for row in rows]

    def append_version(self, version: EntityVersion, *, actor_id: str) -> EntityVersion:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT project_id, payload_json FROM entities WHERE id=?", (version.entity_id,)
            ).fetchone()
            if row is None:
                raise EntityNotFoundError(version.entity_id)
            self._authorize(connection, actor_id, Action.PROJECT_EDIT, row["project_id"])
            if row["project_id"] != version.project_id:
                raise EntityConflictError("entity project mismatch")
            latest = connection.execute(
                "SELECT COALESCE(MAX(ordinal),0) AS ordinal FROM entity_versions WHERE entity_id=?",
                (version.entity_id,),
            ).fetchone()["ordinal"]
            if version.ordinal != latest + 1:
                raise EntityConflictError("entity version ordinal must append")
            if version.lineage.parent_version_id is not None:
                parent = connection.execute(
                    "SELECT id FROM entity_versions WHERE id=? AND entity_id=?",
                    (version.lineage.parent_version_id, version.entity_id),
                ).fetchone()
                if parent is None:
                    raise EntityConflictError("entity version lineage parent must belong to the entity")
            current = EntityRecord.model_validate(json.loads(row["payload_json"]))
            projected = EntityRecord.model_validate(
                {
                    **current.model_dump(mode="python"),
                    "properties": version.payload.properties,
                    "state": version.payload.state,
                    "metadata": version.payload.metadata,
                }
            ).with_version(version.id)
            try:
                connection.execute(
                    "INSERT INTO entity_versions(id,entity_id,project_id,ordinal,payload_json) VALUES(?,?,?,?,?)",
                    (version.id, version.entity_id, version.project_id, version.ordinal, self._dump(version)),
                )
                connection.execute(
                    "UPDATE entities SET payload_json=? WHERE id=?",
                    (self._dump(projected), version.entity_id),
                )
            except sqlite3.IntegrityError as error:
                raise EntityConflictError(version.id) from error
        return version

    def list_versions(self, entity_id: str, *, actor_id: str) -> list[EntityVersion]:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT project_id FROM entities WHERE id=?", (entity_id,)
            ).fetchone()
            if row is None:
                raise EntityNotFoundError(entity_id)
            self._authorize(connection, actor_id, Action.PROJECT_READ, row["project_id"])
            rows = connection.execute(
                "SELECT payload_json FROM entity_versions WHERE entity_id=? ORDER BY ordinal",
                (entity_id,),
            ).fetchall()
            return [EntityVersion.model_validate(json.loads(item["payload_json"])) for item in rows]

    def get_version(self, entity_id: str, version_id: str, *, actor_id: str) -> EntityVersion:
        versions = self.list_versions(entity_id, actor_id=actor_id)
        for version in versions:
            if version.id == version_id:
                return version
        raise EntityNotFoundError(version_id)

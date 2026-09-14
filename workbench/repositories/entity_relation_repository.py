"""Canonical SQLite persistence and queries for project EntityRelations."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from workbench.application.authorization import Action, AuthorizationService
from workbench.domain.entity import EntityRelation
from workbench.repositories.sqlite_project_canvas_repository import SqliteProjectCanvasRepository


class EntityRelationRepositoryError(RuntimeError):
    pass


class EntityRelationNotFoundError(EntityRelationRepositoryError):
    pass


class EntityRelationConflictError(EntityRelationRepositoryError):
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


class SqliteEntityRelationRepository:
    """Authorized relation store; relations are immutable query records."""

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
                CREATE TABLE IF NOT EXISTS entity_relations (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    relation_type TEXT NOT NULL,
                    from_type TEXT NOT NULL,
                    from_id TEXT NOT NULL,
                    from_version_id TEXT,
                    to_type TEXT NOT NULL,
                    to_id TEXT NOT NULL,
                    to_version_id TEXT,
                    revision INTEGER NOT NULL,
                    payload_json TEXT NOT NULL,
                    FOREIGN KEY(project_id) REFERENCES projects(id)
                );
                CREATE INDEX IF NOT EXISTS idx_entity_relations_project
                    ON entity_relations(project_id, relation_type, id);
                CREATE INDEX IF NOT EXISTS idx_entity_relations_from
                    ON entity_relations(project_id, from_type, from_id);
                CREATE INDEX IF NOT EXISTS idx_entity_relations_to
                    ON entity_relations(project_id, to_type, to_id);
                """
            )

    @staticmethod
    def _authorize(connection: sqlite3.Connection, actor_id: str, action: Action, project_id: str) -> None:
        AuthorizationService(_MembershipReader(connection)).require(actor_id, action, project_id)

    @staticmethod
    def _dump(relation: EntityRelation) -> str:
        return json.dumps(relation.model_dump(mode="json"), ensure_ascii=False, sort_keys=True)

    @staticmethod
    def _decode(row: sqlite3.Row) -> EntityRelation:
        return EntityRelation.model_validate(json.loads(row["payload_json"]))

    def create(self, relation: EntityRelation, *, actor_id: str) -> EntityRelation:
        with self._connection() as connection:
            self._authorize(connection, actor_id, Action.PROJECT_EDIT, relation.project_id)
            try:
                connection.execute(
                    """INSERT INTO entity_relations
                    (id,project_id,relation_type,from_type,from_id,from_version_id,
                     to_type,to_id,to_version_id,revision,payload_json)
                    VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        relation.id, relation.project_id, relation.relation_type,
                        relation.from_endpoint.resource_type, relation.from_endpoint.resource_id,
                        relation.from_endpoint.version_id, relation.to_endpoint.resource_type,
                        relation.to_endpoint.resource_id, relation.to_endpoint.version_id,
                        relation.revision, self._dump(relation),
                    ),
                )
            except sqlite3.IntegrityError as error:
                raise EntityRelationConflictError(relation.id) from error
        return relation

    def get(self, relation_id: str, *, actor_id: str) -> EntityRelation:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT * FROM entity_relations WHERE id=?", (relation_id,)
            ).fetchone()
            if row is None:
                raise EntityRelationNotFoundError(relation_id)
            self._authorize(connection, actor_id, Action.PROJECT_READ, row["project_id"])
            return self._decode(row)

    def list(self, project_id: str, *, actor_id: str) -> list[EntityRelation]:
        return self.query(project_id, actor_id=actor_id)

    def query(
        self,
        project_id: str,
        *,
        actor_id: str,
        relation_type: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
    ) -> list[EntityRelation]:
        with self._connection() as connection:
            self._authorize(connection, actor_id, Action.PROJECT_READ, project_id)
            clauses = ["project_id=?"]
            params: list[str] = [project_id]
            if relation_type is not None:
                clauses.append("relation_type=?")
                params.append(relation_type)
            if resource_type is not None and resource_id is not None:
                clauses.append("((from_type=? AND from_id=?) OR (to_type=? AND to_id=?))")
                params.extend((resource_type, resource_id, resource_type, resource_id))
            elif resource_type is not None:
                clauses.append("(from_type=? OR to_type=?)")
                params.extend((resource_type, resource_type))
            elif resource_id is not None:
                clauses.append("(from_id=? OR to_id=?)")
                params.extend((resource_id, resource_id))
            rows = connection.execute(
                f"SELECT * FROM entity_relations WHERE {' AND '.join(clauses)} ORDER BY id",
                params,
            ).fetchall()
            return [self._decode(row) for row in rows]

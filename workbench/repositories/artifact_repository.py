"""Canonical SQLite persistence for Artifact identities and immutable versions."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from workbench.application.authorization import Action, AuthorizationService
from workbench.domain.artifact import Artifact, ArtifactVersion
from workbench.repositories.sqlite_project_canvas_repository import SqliteProjectCanvasRepository


class ArtifactRepositoryError(RuntimeError): pass
class ArtifactNotFoundError(ArtifactRepositoryError): pass
class ArtifactConflictError(ArtifactRepositoryError): pass


class _MembershipReader:
    def __init__(self, connection: sqlite3.Connection): self._connection = connection
    def member_role(self, project_id: str, actor_id: str) -> str | None:
        row = self._connection.execute("SELECT role FROM project_members WHERE project_id=? AND actor_id=?", (project_id, actor_id)).fetchone()
        return row["role"] if row else None


class SqliteArtifactRepository:
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
            connection.executescript("""
            CREATE TABLE IF NOT EXISTS artifacts (
                id TEXT PRIMARY KEY, project_id TEXT NOT NULL, payload_json TEXT NOT NULL,
                FOREIGN KEY(project_id) REFERENCES projects(id)
            );
            CREATE TABLE IF NOT EXISTS artifact_versions (
                id TEXT PRIMARY KEY, artifact_id TEXT NOT NULL, project_id TEXT NOT NULL,
                ordinal INTEGER NOT NULL, payload_json TEXT NOT NULL,
                UNIQUE(artifact_id, ordinal), FOREIGN KEY(artifact_id) REFERENCES artifacts(id),
                FOREIGN KEY(project_id) REFERENCES projects(id)
            );
            CREATE INDEX IF NOT EXISTS idx_artifact_versions_artifact ON artifact_versions(artifact_id, ordinal);
            """)

    @staticmethod
    def _authorize(connection, actor_id, action, project_id):
        AuthorizationService(_MembershipReader(connection)).require(actor_id, action, project_id)

    def create_artifact(self, artifact: Artifact, *, actor_id: str) -> Artifact:
        with self._connection() as connection:
            self._authorize(connection, actor_id, Action.PROJECT_EDIT, artifact.project_id)
            try:
                connection.execute("INSERT INTO artifacts(id,project_id,payload_json) VALUES(?,?,?)", (artifact.id, artifact.project_id, json.dumps(artifact.model_dump(mode="json"), ensure_ascii=False, sort_keys=True)))
            except sqlite3.IntegrityError as error: raise ArtifactConflictError(artifact.id) from error
        return artifact

    def create_artifact_with_version(self, artifact: Artifact, version: ArtifactVersion, *, actor_id: str) -> tuple[Artifact, ArtifactVersion]:
        if version.artifact_id != artifact.id or version.project_id != artifact.project_id or version.ordinal != 1:
            raise ArtifactConflictError("the first artifact version must belong to the new artifact")
        with self._connection() as connection:
            self._authorize(connection, actor_id, Action.PROJECT_EDIT, artifact.project_id)
            try:
                connection.execute(
                    "INSERT INTO artifacts(id,project_id,payload_json) VALUES(?,?,?)",
                    (artifact.id, artifact.project_id, json.dumps(artifact.model_dump(mode="json"), ensure_ascii=False, sort_keys=True)),
                )
                connection.execute(
                    "INSERT INTO artifact_versions(id,artifact_id,project_id,ordinal,payload_json) VALUES(?,?,?,?,?)",
                    (version.id, version.artifact_id, version.project_id, version.ordinal,
                     json.dumps(version.model_dump(mode="json"), ensure_ascii=False, sort_keys=True)),
                )
                updated = artifact.with_version(version.id)
                connection.execute(
                    "UPDATE artifacts SET payload_json=? WHERE id=?",
                    (json.dumps(updated.model_dump(mode="json"), ensure_ascii=False, sort_keys=True), artifact.id),
                )
            except sqlite3.IntegrityError as error:
                raise ArtifactConflictError(artifact.id) from error
        return updated, version

    def get_artifact(self, artifact_id: str, *, actor_id: str) -> Artifact:
        with self._connection() as connection:
            row = connection.execute("SELECT * FROM artifacts WHERE id=?", (artifact_id,)).fetchone()
            if row is None: raise ArtifactNotFoundError(artifact_id)
            self._authorize(connection, actor_id, Action.PROJECT_READ, row["project_id"])
            return Artifact.model_validate(json.loads(row["payload_json"]))

    def list_artifacts(self, project_id: str, *, actor_id: str) -> list[Artifact]:
        with self._connection() as connection:
            self._authorize(connection, actor_id, Action.PROJECT_READ, project_id)
            rows = connection.execute(
                "SELECT payload_json FROM artifacts WHERE project_id=? ORDER BY id",
                (project_id,),
            ).fetchall()
            return [Artifact.model_validate(json.loads(row["payload_json"])) for row in rows]

    def append_version(self, version: ArtifactVersion, *, actor_id: str) -> ArtifactVersion:
        with self._connection() as connection:
            row = connection.execute("SELECT project_id FROM artifacts WHERE id=?", (version.artifact_id,)).fetchone()
            if row is None: raise ArtifactNotFoundError(version.artifact_id)
            self._authorize(connection, actor_id, Action.PROJECT_EDIT, row["project_id"])
            if row["project_id"] != version.project_id: raise ArtifactConflictError("artifact project mismatch")
            latest = connection.execute("SELECT COALESCE(MAX(ordinal),0) AS ordinal FROM artifact_versions WHERE artifact_id=?", (version.artifact_id,)).fetchone()["ordinal"]
            if version.ordinal != latest + 1: raise ArtifactConflictError("artifact version ordinal must append")
            try:
                connection.execute("INSERT INTO artifact_versions(id,artifact_id,project_id,ordinal,payload_json) VALUES(?,?,?,?,?)", (version.id, version.artifact_id, version.project_id, version.ordinal, json.dumps(version.model_dump(mode="json"), ensure_ascii=False, sort_keys=True)))
                artifact = Artifact.model_validate(json.loads(connection.execute("SELECT payload_json FROM artifacts WHERE id=?", (version.artifact_id,)).fetchone()[0]))
                updated = artifact.with_version(version.id)
                connection.execute("UPDATE artifacts SET payload_json=? WHERE id=?", (json.dumps(updated.model_dump(mode="json"), ensure_ascii=False, sort_keys=True), version.artifact_id))
            except sqlite3.IntegrityError as error: raise ArtifactConflictError(version.id) from error
        return version

    def list_versions(self, artifact_id: str, *, actor_id: str) -> list[ArtifactVersion]:
        with self._connection() as connection:
            row = connection.execute("SELECT project_id FROM artifacts WHERE id=?", (artifact_id,)).fetchone()
            if row is None: raise ArtifactNotFoundError(artifact_id)
            self._authorize(connection, actor_id, Action.PROJECT_READ, row["project_id"])
            rows = connection.execute("SELECT payload_json FROM artifact_versions WHERE artifact_id=? ORDER BY ordinal", (artifact_id,)).fetchall()
            return [ArtifactVersion.model_validate(json.loads(item["payload_json"])) for item in rows]

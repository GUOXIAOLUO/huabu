"""Canonical SQLite persistence for generic Catalogs and item versions."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Callable, Iterator, Protocol

from workbench.application.authorization import Action, AuthorizationService
from workbench.domain.catalog import Catalog, CatalogItem, CatalogItemVersion
from workbench.repositories.sqlite_project_canvas_repository import SqliteProjectCanvasRepository


class CatalogRepositoryError(RuntimeError): pass
class CatalogNotFoundError(CatalogRepositoryError): pass
class CatalogItemNotFoundError(CatalogRepositoryError): pass
class CatalogConflictError(CatalogRepositoryError): pass


class _MembershipReader:
    def __init__(self, connection: sqlite3.Connection): self._connection = connection
    def member_role(self, project_id: str, actor_id: str) -> str | None:
        row = self._connection.execute("SELECT role FROM project_members WHERE project_id=? AND actor_id=?", (project_id, actor_id)).fetchone()
        return row["role"] if row else None
    def workspace_member_role(self, workspace_id: str, actor_id: str) -> str | None:
        rows = self._connection.execute(
            "SELECT pm.role FROM project_members pm JOIN projects p ON p.id=pm.project_id WHERE p.workspace_id=? AND pm.actor_id=?",
            (workspace_id, actor_id),
        ).fetchall()
        roles = {row["role"] for row in rows}
        return next((role for role in ("owner", "editor", "viewer") if role in roles), None)


class CatalogRepository(Protocol):
    def create(self, catalog: Catalog, *, actor_id: str) -> Catalog: ...
    def get(self, catalog_id: str, *, actor_id: str) -> Catalog: ...
    def list(self, *, workspace_id: str, project_id: str | None, actor_id: str) -> list[Catalog]: ...
    def create_item(self, catalog: Catalog, item: CatalogItem, version: CatalogItemVersion, *, actor_id: str) -> tuple[Catalog, CatalogItem, CatalogItemVersion]: ...
    def append_version(self, catalog: Catalog, item: CatalogItem, version: CatalogItemVersion, *, actor_id: str) -> CatalogItemVersion: ...
    def get_item(self, item_id: str, *, actor_id: str) -> CatalogItem: ...
    def list_items(self, catalog_id: str, *, actor_id: str) -> list[CatalogItem]: ...
    def list_versions(self, item_id: str, *, actor_id: str) -> list[CatalogItemVersion]: ...


class SqliteCatalogRepository:
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
            CREATE TABLE IF NOT EXISTS catalogs (
                id TEXT PRIMARY KEY, workspace_id TEXT NOT NULL, project_id TEXT,
                scope TEXT NOT NULL, payload_json TEXT NOT NULL,
                FOREIGN KEY(project_id) REFERENCES projects(id)
            );
            CREATE TABLE IF NOT EXISTS catalog_items (
                id TEXT PRIMARY KEY, catalog_id TEXT NOT NULL, payload_json TEXT NOT NULL,
                FOREIGN KEY(catalog_id) REFERENCES catalogs(id)
            );
            CREATE TABLE IF NOT EXISTS catalog_item_versions (
                id TEXT PRIMARY KEY, catalog_id TEXT NOT NULL, item_id TEXT NOT NULL,
                ordinal INTEGER NOT NULL, payload_json TEXT NOT NULL,
                UNIQUE(item_id, ordinal), FOREIGN KEY(catalog_id) REFERENCES catalogs(id),
                FOREIGN KEY(item_id) REFERENCES catalog_items(id)
            );
            CREATE INDEX IF NOT EXISTS idx_catalogs_scope ON catalogs(workspace_id, project_id, id);
            CREATE INDEX IF NOT EXISTS idx_catalog_item_versions_item ON catalog_item_versions(item_id, ordinal);
            """)

    @staticmethod
    def _authorize(connection, actor_id: str, action: Action, catalog: Catalog) -> None:
        policy = AuthorizationService(_MembershipReader(connection))
        if catalog.scope == "project": policy.require(actor_id, action, catalog.project_id)
        else: policy.require_workspace(actor_id, action, catalog.workspace_id)

    @staticmethod
    def _decode_catalog(row): return Catalog.model_validate(json.loads(row["payload_json"]))
    @staticmethod
    def _decode_item(row): return CatalogItem.model_validate(json.loads(row["payload_json"]))
    @staticmethod
    def _decode_version(row): return CatalogItemVersion.model_validate(json.loads(row["payload_json"]))

    def create(self, catalog: Catalog, *, actor_id: str) -> Catalog:
        with self._connection() as connection:
            if catalog.scope == "project":
                project = connection.execute("SELECT workspace_id FROM projects WHERE id=?", (catalog.project_id,)).fetchone()
                if project is None or project["workspace_id"] != catalog.workspace_id:
                    raise CatalogConflictError("catalog project must belong to its workspace")
            self._authorize(connection, actor_id, Action.CATALOG_EDIT, catalog)
            try:
                connection.execute("INSERT INTO catalogs VALUES (?,?,?,?,?)", (catalog.id, catalog.workspace_id, catalog.project_id, catalog.scope, json.dumps(catalog.model_dump(mode="json"), ensure_ascii=False, sort_keys=True)))
            except sqlite3.IntegrityError as error: raise CatalogConflictError(catalog.id) from error
        return catalog

    def get(self, catalog_id: str, *, actor_id: str) -> Catalog:
        with self._connection() as connection:
            row = connection.execute("SELECT * FROM catalogs WHERE id=?", (catalog_id,)).fetchone()
            if row is None: raise CatalogNotFoundError(catalog_id)
            catalog = self._decode_catalog(row)
            self._authorize(connection, actor_id, Action.CATALOG_READ, catalog)
            return catalog

    def list(self, *, workspace_id: str, project_id: str | None, actor_id: str) -> list[Catalog]:
        with self._connection() as connection:
            rows = connection.execute("SELECT * FROM catalogs WHERE workspace_id=? AND (project_id IS NULL OR project_id=?) ORDER BY id", (workspace_id, project_id)).fetchall()
            catalogs = [self._decode_catalog(row) for row in rows]
            for catalog in catalogs: self._authorize(connection, actor_id, Action.CATALOG_READ, catalog)
            return catalogs

    def create_item(self, catalog: Catalog, item: CatalogItem, version: CatalogItemVersion, *, actor_id: str):
        if item.catalog_id != catalog.id or version.catalog_id != catalog.id or version.item_id != item.id or version.ordinal != 1:
            raise CatalogConflictError("first catalog item version must belong to the new item")
        with self._connection() as connection:
            self._authorize(connection, actor_id, Action.CATALOG_EDIT, catalog)
            try:
                connection.execute("INSERT INTO catalog_items VALUES (?,?,?)", (item.id, item.catalog_id, json.dumps(item.model_dump(mode="json"), ensure_ascii=False, sort_keys=True)))
                connection.execute("INSERT INTO catalog_item_versions VALUES (?,?,?,?,?)", (version.id, version.catalog_id, version.item_id, version.ordinal, json.dumps(version.model_dump(mode="json"), ensure_ascii=False, sort_keys=True)))
                updated_catalog = catalog.with_item(item.id)
                updated_item = item.with_version(version.id)
                connection.execute("UPDATE catalogs SET payload_json=? WHERE id=?", (json.dumps(updated_catalog.model_dump(mode="json"), ensure_ascii=False, sort_keys=True), catalog.id))
                connection.execute("UPDATE catalog_items SET payload_json=? WHERE id=?", (json.dumps(updated_item.model_dump(mode="json"), ensure_ascii=False, sort_keys=True), item.id))
            except sqlite3.IntegrityError as error: raise CatalogConflictError(item.id) from error
        return updated_catalog, updated_item, version

    def get_item(self, item_id: str, *, actor_id: str) -> CatalogItem:
        with self._connection() as connection:
            row = connection.execute("SELECT i.payload_json, c.payload_json AS catalog_json FROM catalog_items i JOIN catalogs c ON c.id=i.catalog_id WHERE i.id=?", (item_id,)).fetchone()
            if row is None: raise CatalogItemNotFoundError(item_id)
            catalog = Catalog.model_validate(json.loads(row["catalog_json"]))
            self._authorize(connection, actor_id, Action.CATALOG_READ, catalog)
            return CatalogItem.model_validate(json.loads(row["payload_json"]))

    def list_items(self, catalog_id: str, *, actor_id: str) -> list[CatalogItem]:
        with self._connection() as connection:
            row = connection.execute("SELECT * FROM catalogs WHERE id=?", (catalog_id,)).fetchone()
            if row is None: raise CatalogNotFoundError(catalog_id)
            catalog = self._decode_catalog(row)
            self._authorize(connection, actor_id, Action.CATALOG_READ, catalog)
            rows = connection.execute("SELECT payload_json FROM catalog_items WHERE catalog_id=? ORDER BY id", (catalog_id,)).fetchall()
            return [self._decode_item(item) for item in rows]

    def append_version(self, catalog: Catalog, item: CatalogItem, version: CatalogItemVersion, *, actor_id: str) -> CatalogItemVersion:
        if version.catalog_id != catalog.id or version.item_id != item.id:
            raise CatalogConflictError("catalog item version ownership mismatch")
        with self._connection() as connection:
            self._authorize(connection, actor_id, Action.CATALOG_EDIT, catalog)
            latest = connection.execute("SELECT COALESCE(MAX(ordinal),0) AS ordinal FROM catalog_item_versions WHERE item_id=?", (item.id,)).fetchone()["ordinal"]
            if version.ordinal != latest + 1: raise CatalogConflictError("catalog item version ordinal must append")
            updated_item = item.with_version(version.id)
            try:
                connection.execute("INSERT INTO catalog_item_versions VALUES (?,?,?,?,?)", (version.id, version.catalog_id, version.item_id, version.ordinal, json.dumps(version.model_dump(mode="json"), ensure_ascii=False, sort_keys=True)))
                connection.execute("UPDATE catalog_items SET payload_json=? WHERE id=?", (json.dumps(updated_item.model_dump(mode="json"), ensure_ascii=False, sort_keys=True), item.id))
            except sqlite3.IntegrityError as error: raise CatalogConflictError(version.id) from error
        return version

    def list_versions(self, item_id: str, *, actor_id: str) -> list[CatalogItemVersion]:
        with self._connection() as connection:
            row = connection.execute("SELECT c.payload_json FROM catalog_items i JOIN catalogs c ON c.id=i.catalog_id WHERE i.id=?", (item_id,)).fetchone()
            if row is None: raise CatalogItemNotFoundError(item_id)
            catalog = Catalog.model_validate(json.loads(row["payload_json"]))
            self._authorize(connection, actor_id, Action.CATALOG_READ, catalog)
            rows = connection.execute("SELECT payload_json FROM catalog_item_versions WHERE item_id=? ORDER BY ordinal", (item_id,)).fetchall()
            return [CatalogItemVersion.model_validate(json.loads(item["payload_json"])) for item in rows]

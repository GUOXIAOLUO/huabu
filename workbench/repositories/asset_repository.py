"""SQLite persistence for Asset identities and immutable AssetVersions."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator, Sequence

from workbench.domain.asset import (
    Asset,
    AssetVersion,
    AssetVersionContent,
    AssetVersionProvenance,
)


class AssetRepositoryError(RuntimeError):
    pass


class AssetRepositoryNotFoundError(AssetRepositoryError):
    pass


class AssetRepositoryConflictError(AssetRepositoryError):
    pass


class SqliteAssetRepository:
    """Owns Asset/AssetVersion persistence and their cross-record invariants."""

    def __init__(self, database_path: str | Path):
        self._database_path = Path(database_path)

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
        with self._connection() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS assets (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    source TEXT NOT NULL,
                    type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    metadata_json TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS asset_versions (
                    id TEXT PRIMARY KEY,
                    asset_id TEXT NOT NULL,
                    ordinal INTEGER NOT NULL,
                    location TEXT NOT NULL,
                    checksum TEXT NOT NULL,
                    mime_type TEXT NOT NULL,
                    size_bytes INTEGER NOT NULL,
                    provenance_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    UNIQUE(asset_id, ordinal),
                    FOREIGN KEY (asset_id) REFERENCES assets(id)
                );
                /* Derived index over Asset.metadata["tags"]. The canonical
                   declaration stays in metadata_json; this table exists so a
                   tag filter is an index seek instead of a JSON scan. Assets
                   are immutable and append-only through this repository, so
                   the index is written once with the record it indexes and
                   cannot drift. */
                CREATE TABLE IF NOT EXISTS asset_tags (
                    asset_id TEXT NOT NULL,
                    tag TEXT NOT NULL,
                    PRIMARY KEY (asset_id, tag),
                    FOREIGN KEY (asset_id) REFERENCES assets(id)
                );
                CREATE INDEX IF NOT EXISTS idx_assets_project_type
                    ON assets(project_id, type);
                CREATE INDEX IF NOT EXISTS idx_assets_project_source
                    ON assets(project_id, source);
                CREATE INDEX IF NOT EXISTS idx_assets_project_status
                    ON assets(project_id, status);
                CREATE INDEX IF NOT EXISTS idx_asset_tags_tag
                    ON asset_tags(tag);
                """
            )

    def create_asset(self, asset: Asset) -> Asset:
        self.migrate()
        with self._connection() as connection:
            try:
                connection.execute(
                    "INSERT INTO assets VALUES (?, ?, ?, ?, ?, ?)",
                    (asset.id, asset.project_id, asset.source, asset.type, asset.status,
                     json.dumps(asset.metadata, sort_keys=True)),
                )
                self._write_tags(connection, asset)
            except sqlite3.IntegrityError as exc:
                raise AssetRepositoryConflictError(f"asset already exists: {asset.id}") from exc
        return asset

    def create_asset_with_version(self, asset: Asset, version: AssetVersion) -> tuple[Asset, AssetVersion]:
        """Atomically persist a newly materialized Asset and its first version."""
        self.migrate()
        if version.asset_id != asset.id or version.ordinal != 1:
            raise AssetRepositoryConflictError("the first asset version must belong to the new asset and have ordinal 1")
        with self._connection() as connection:
            try:
                connection.execute(
                    "INSERT INTO assets VALUES (?, ?, ?, ?, ?, ?)",
                    (asset.id, asset.project_id, asset.source, asset.type, asset.status,
                     json.dumps(asset.metadata, sort_keys=True)),
                )
                self._write_tags(connection, asset)
                connection.execute(
                    """INSERT INTO asset_versions
                    (id, asset_id, ordinal, location, checksum, mime_type, size_bytes,
                     provenance_json, created_at, metadata_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (version.id, version.asset_id, version.ordinal, version.content.location,
                     version.content.checksum, version.content.mime_type, version.content.size_bytes,
                     json.dumps(version.provenance.model_dump(mode="json"), sort_keys=True),
                     version.created_at.isoformat(), json.dumps(version.metadata, sort_keys=True)),
                )
            except sqlite3.IntegrityError as exc:
                raise AssetRepositoryConflictError(f"asset materialization already exists: {asset.id}") from exc
        return asset, version

    @staticmethod
    def _asset_tags(asset: Asset) -> tuple[str, ...]:
        """The tags one Asset declares, normalized the way a query will look."""
        declared = asset.metadata.get("tags") if isinstance(asset.metadata, dict) else None
        values = declared if isinstance(declared, (list, tuple)) else ()
        tags: list[str] = []
        for value in values:
            tag = str(value or "").strip().casefold()
            if tag and tag not in tags:
                tags.append(tag)
        return tuple(tags)

    def _write_tags(self, connection: sqlite3.Connection, asset: Asset) -> None:
        tags = self._asset_tags(asset)
        if not tags:
            return
        connection.executemany(
            "INSERT INTO asset_tags (asset_id, tag) VALUES (?, ?)",
            [(asset.id, tag) for tag in tags],
        )

    @staticmethod
    def _hydrate(connection: sqlite3.Connection, rows: Sequence[sqlite3.Row]) -> list[Asset]:
        """Build the Asset records for `rows`, reading version ids in one query.

        One round trip per page rather than one per asset: a page is allowed to
        be 200 rows, and 200 connections to answer one query is a cost the
        caller never asked for.
        """
        if not rows:
            return []
        ids = [str(row["id"]) for row in rows]
        placeholders = ", ".join("?" for _ in ids)
        version_rows = connection.execute(
            f"SELECT asset_id, id FROM asset_versions WHERE asset_id IN ({placeholders})"
            " ORDER BY asset_id, ordinal",
            ids,
        ).fetchall()
        version_ids: dict[str, list[str]] = {asset_id: [] for asset_id in ids}
        for row in version_rows:
            version_ids[str(row["asset_id"])].append(str(row["id"]))
        return [
            Asset(
                id=row["id"], project_id=row["project_id"], source=row["source"],
                type=row["type"], status=row["status"],
                version_ids=tuple(version_ids[str(row["id"])]),
                metadata=json.loads(row["metadata_json"]),
            )
            for row in rows
        ]

    def load_asset(self, asset_id: str) -> Asset:
        self.migrate()
        with self._connection() as connection:
            row = connection.execute("SELECT * FROM assets WHERE id=?", (asset_id,)).fetchone()
            if row is None:
                raise AssetRepositoryNotFoundError(f"asset not found: {asset_id}")
            return self._hydrate(connection, [row])[0]

    def list_assets(self, *, project_id: str | None = None) -> list[Asset]:
        self.migrate()
        with self._connection() as connection:
            if project_id:
                rows = connection.execute("SELECT * FROM assets WHERE project_id=? ORDER BY id", (project_id,)).fetchall()
            else:
                rows = connection.execute("SELECT * FROM assets ORDER BY id").fetchall()
            return self._hydrate(connection, rows)

    def query_assets(self, query) -> tuple[list[Asset], int]:
        """Return one filtered, ordered page plus the unpaged total match count.

        `query` is an `AssetQuery`
        (`workbench.application.asset_query.AssetQuery`): already validated,
        already frozen, and already scoped to one project. This method is the
        repository half of `AssetQueryRepository`; the application half is
        `AssetService.query`, which owns authorization before calling here.
        """
        self.migrate()
        clauses = ["assets.project_id = ?"]
        params: list[Any] = [query.project_id]
        for column, values in (
            ("type", query.types),
            ("source", query.sources),
            ("status", query.statuses),
        ):
            if values:
                clauses.append(f"assets.{column} IN ({', '.join('?' for _ in values)})")
                params.extend(values)
        for tag in query.tags:
            clauses.append(
                "EXISTS (SELECT 1 FROM asset_tags"
                " WHERE asset_tags.asset_id = assets.id AND asset_tags.tag = ?)"
            )
            params.append(tag)
        if query.text:
            pattern = f"%{query.text.casefold()}%"
            clauses.append("(lower(assets.id) LIKE ? OR lower(assets.metadata_json) LIKE ?)")
            params.extend((pattern, pattern))
        where = " AND ".join(clauses)
        with self._connection() as connection:
            total = int(
                connection.execute(f"SELECT COUNT(*) FROM assets WHERE {where}", params).fetchone()[0]
            )
            rows = connection.execute(
                f"SELECT assets.* FROM assets WHERE {where} ORDER BY assets.id LIMIT ? OFFSET ?",
                [*params, query.limit, query.offset],
            ).fetchall()
            return self._hydrate(connection, rows), total

    def create_version(self, version: AssetVersion) -> AssetVersion:
        self.migrate()
        with self._connection() as connection:
            asset = connection.execute("SELECT id FROM assets WHERE id=?", (version.asset_id,)).fetchone()
            if asset is None:
                raise AssetRepositoryNotFoundError(f"asset not found: {version.asset_id}")
            current_count = connection.execute(
                "SELECT COUNT(*) FROM asset_versions WHERE asset_id=?", (version.asset_id,)
            ).fetchone()[0]
            if version.ordinal != current_count + 1:
                raise AssetRepositoryConflictError(
                    f"asset version ordinal must be {current_count + 1}: {version.ordinal}"
                )
            try:
                connection.execute(
                    """INSERT INTO asset_versions
                    (id, asset_id, ordinal, location, checksum, mime_type, size_bytes,
                     provenance_json, created_at, metadata_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (version.id, version.asset_id, version.ordinal, version.content.location,
                     version.content.checksum, version.content.mime_type, version.content.size_bytes,
                     json.dumps(version.provenance.model_dump(mode="json"), sort_keys=True),
                     version.created_at.isoformat(), json.dumps(version.metadata, sort_keys=True)),
                )
            except sqlite3.IntegrityError as exc:
                raise AssetRepositoryConflictError(f"asset version already exists: {version.id}") from exc
        return version

    @staticmethod
    def _version_from_row(row: sqlite3.Row) -> AssetVersion:
        """Build one AssetVersion from its stored row.

        One mapping for every version read: `load_version` and `list_versions`
        answer the same question at different widths, and two copies of this
        mapping would drift the first time a version column was added.
        """
        return AssetVersion(
            id=row["id"], asset_id=row["asset_id"], ordinal=row["ordinal"],
            content=AssetVersionContent(
                location=row["location"], checksum=row["checksum"],
                mime_type=row["mime_type"], size_bytes=row["size_bytes"],
            ),
            provenance=AssetVersionProvenance(**json.loads(row["provenance_json"])),
            created_at=row["created_at"], metadata=json.loads(row["metadata_json"]),
        )

    def load_version(self, asset_id: str, version_id: str) -> AssetVersion:
        self.migrate()
        with self._connection() as connection:
            row = connection.execute(
                "SELECT * FROM asset_versions WHERE asset_id=? AND id=?", (asset_id, version_id)
            ).fetchone()
        if row is None:
            raise AssetRepositoryNotFoundError(f"asset version not found: {asset_id}/{version_id}")
        return self._version_from_row(row)

    def list_versions(self, asset_id: str) -> list[AssetVersion]:
        """Return every version of one asset, in ordinal order.

        An asset with no versions yet is not an error: an asset is created
        before anything is stored in it, so an empty list is the honest answer
        and the caller can say "this asset has no versions" instead of being
        handed a failure it would have to read as one. A missing *asset* is
        still a failure, so a typo cannot look like an empty asset.
        """
        self.migrate()
        with self._connection() as connection:
            exists = connection.execute(
                "SELECT id FROM assets WHERE id=?", (asset_id,)
            ).fetchone()
            if exists is None:
                raise AssetRepositoryNotFoundError(f"asset not found: {asset_id}")
            rows = connection.execute(
                "SELECT * FROM asset_versions WHERE asset_id=? ORDER BY ordinal", (asset_id,)
            ).fetchall()
        return [self._version_from_row(row) for row in rows]

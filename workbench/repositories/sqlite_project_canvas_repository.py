"""SQLite Project/Canvas authority with lossless Legacy-payload compatibility."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable, Iterator

from workbench.application.authorization import Action, AuthorizationService
from workbench.domain.project.models import CanvasRecord, ProjectMember, ProjectRecord


class CanonicalRepositoryError(RuntimeError):
    pass


class CanonicalNotFoundError(CanonicalRepositoryError):
    pass


class CanonicalStaleRevisionError(CanonicalRepositoryError):
    def __init__(self, current_revision: int):
        self.current_revision = current_revision
        super().__init__("canvas revision is stale")


class LegacyIdentityError(CanonicalRepositoryError):
    pass


LOCAL_WORKSPACE_ID = "local"
LOCAL_WORKSPACE_ACTOR_ID = "local-workspace-actor"
DEFAULT_PROJECT_ID = "default"


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _iso(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _legacy_order(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _project_order(record: ProjectRecord) -> int:
    legacy = record.metadata.get("legacy") if isinstance(record.metadata, dict) else {}
    return _legacy_order(legacy.get("order")) if isinstance(legacy, dict) else 0


@dataclass(frozen=True)
class LegacyIdentityResolution:
    project_id: str
    owner_actor_id: str | None
    owner_state: str
    issues: tuple[str, ...] = ()


@dataclass(frozen=True)
class CanvasPayloadSnapshot:
    payload: dict[str, Any]
    revision: int


@dataclass(frozen=True)
class LegacyImportReport:
    imported_canvas_ids: tuple[str, ...]
    skipped_canvas_ids: tuple[str, ...]
    identity_resolutions: dict[str, LegacyIdentityResolution]


class LegacyIdentityMapper:
    """Makes Legacy project/owner interpretation inspectable and repeatable."""

    def __init__(self, known_project_ids: set[str], *, default_project_id: str = DEFAULT_PROJECT_ID):
        self._known_project_ids = set(known_project_ids)
        self._default_project_id = default_project_id

    def resolve(self, canvas: dict[str, Any]) -> LegacyIdentityResolution:
        project_id = str(canvas.get("project") or "").strip() or self._default_project_id
        owner = str(canvas.get("owner") or "").strip()
        issues: list[str] = []
        if project_id not in self._known_project_ids:
            issues.append("project_mismatch")
        if not owner:
            return LegacyIdentityResolution(project_id, None, "local_unowned", tuple(issues))
        return LegacyIdentityResolution(project_id, f"legacy-owner:{owner}", "legacy_owner", tuple(issues))


class SqliteProjectCanvasRepository:
    """Canonical R3 persistence; each Canvas payload remains lossless Legacy JSON."""

    def __init__(self, database_path: str | Path, *, clock: Callable[[], datetime] = _utcnow):
        self._database_path = Path(database_path)
        self._clock = clock

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
                CREATE TABLE IF NOT EXISTS schema_migrations (version INTEGER PRIMARY KEY);
                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY, name TEXT NOT NULL, workspace_id TEXT NOT NULL,
                    created_by TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
                    revision INTEGER NOT NULL, metadata_json TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS project_members (
                    project_id TEXT NOT NULL, actor_id TEXT NOT NULL, role TEXT NOT NULL,
                    created_at TEXT NOT NULL, PRIMARY KEY (project_id, actor_id),
                    FOREIGN KEY (project_id) REFERENCES projects(id)
                );
                CREATE TABLE IF NOT EXISTS legacy_project_exclusions (
                    project_id TEXT PRIMARY KEY
                );
                CREATE TABLE IF NOT EXISTS canvases (
                    id TEXT PRIMARY KEY, project_id TEXT NOT NULL, title TEXT NOT NULL,
                    viewport_json TEXT NOT NULL, payload_json TEXT NOT NULL,
                    revision INTEGER NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
                    deleted_at TEXT, metadata_json TEXT NOT NULL,
                    FOREIGN KEY (project_id) REFERENCES projects(id)
                );
                CREATE TABLE IF NOT EXISTS audit_outbox (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, event_type TEXT NOT NULL,
                    project_id TEXT NOT NULL, canvas_id TEXT, actor_id TEXT NOT NULL,
                    payload_json TEXT NOT NULL, occurred_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS authority_state (
                    singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
                    canvas_authority TEXT NOT NULL, updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS project_authority_state (
                    singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
                    project_authority TEXT NOT NULL, updated_at TEXT NOT NULL
                );
                INSERT OR IGNORE INTO schema_migrations(version) VALUES (1);
                INSERT OR IGNORE INTO authority_state(singleton, canvas_authority, updated_at)
                    VALUES (1, 'legacy_json', CURRENT_TIMESTAMP);
                INSERT OR IGNORE INTO project_authority_state(singleton, project_authority, updated_at)
                    VALUES (1, 'legacy_json', CURRENT_TIMESTAMP);
                """
            )

    def create_project(self, record: ProjectRecord, owner: ProjectMember | None = None) -> ProjectRecord:
        self.migrate()
        if owner is not None and (owner.project_id != record.id or owner.role != "owner"):
            raise CanonicalRepositoryError("project owner must be an owner member of the same project")
        with self._connection() as connection:
            connection.execute(
                "INSERT INTO projects VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (record.id, record.name, record.workspace_id, record.created_by, _iso(record.created_at),
                 _iso(record.updated_at), record.revision, json.dumps(record.metadata, sort_keys=True)),
            )
            member = owner or ProjectMember(project_id=record.id, actor_id=record.created_by, role="owner", created_at=record.created_at)
            connection.execute(
                "INSERT INTO project_members VALUES (?, ?, ?, ?)",
                (member.project_id, member.actor_id, member.role, _iso(member.created_at)),
            )
            self._append_audit(connection, "project.created", record.id, None, member.actor_id, {"revision": record.revision})
        return record

    def add_member(self, member: ProjectMember) -> None:
        self.migrate()
        with self._connection() as connection:
            connection.execute(
                "INSERT INTO project_members VALUES (?, ?, ?, ?) ON CONFLICT(project_id, actor_id) DO UPDATE SET role=excluded.role",
                (member.project_id, member.actor_id, member.role, _iso(member.created_at)),
            )
            self._append_audit(connection, "project.member_added", member.project_id, None, member.actor_id, {"role": member.role})

    def member_role(self, project_id: str, actor_id: str) -> str | None:
        self.migrate()
        with self._connection() as connection:
            row = connection.execute("SELECT role FROM project_members WHERE project_id=? AND actor_id=?", (project_id, actor_id)).fetchone()
        return str(row["role"]) if row else None

    def list_project_members(self, project_id: str) -> list[dict[str, str]]:
        self.migrate()
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT actor_id, role FROM project_members WHERE project_id=? ORDER BY actor_id",
                (project_id,),
            ).fetchall()
        return [{"actor_id": str(row["actor_id"]), "role": str(row["role"])} for row in rows]

    def import_legacy_projects(self, projects: list[dict[str, Any]], *, now: datetime) -> None:
        self.migrate()
        seen_ids: set[str] = set()
        for source in projects:
            if not isinstance(source, dict) or not str(source.get("id") or "").strip():
                raise CanonicalRepositoryError("legacy project must have an id")
            project_id = str(source["id"]).strip()
            if project_id in seen_ids:
                raise CanonicalRepositoryError(f"duplicate legacy project id: {project_id}")
            seen_ids.add(project_id)
            created_at = _parse_legacy_time(source.get("created_at")) or now
            updated_at = _parse_legacy_time(source.get("updated_at")) or created_at
            metadata = {"legacy": {"order": _legacy_order(source.get("order")), "source": deepcopy(source)}}
            record = ProjectRecord(
                id=project_id, name=str(source.get("name") or "未命名项目")[:500],
                workspace_id=LOCAL_WORKSPACE_ID, created_by=LOCAL_WORKSPACE_ACTOR_ID,
                created_at=created_at, updated_at=updated_at, metadata=metadata,
            )
            try:
                current = self.load_project(project_id)
            except CanonicalNotFoundError:
                self.create_project(record)
            else:
                if current.name != record.name or _project_order(current) != _project_order(record):
                    self.update_project(project_id, name=record.name, order=_legacy_order(source.get("order")))
                with self._connection() as connection:
                    connection.execute(
                        "UPDATE projects SET created_at=?, updated_at=?, metadata_json=? WHERE id=?",
                        (_iso(created_at), _iso(updated_at), json.dumps(metadata, ensure_ascii=False, sort_keys=True), project_id),
                    )
            members = source.get("members", [])
            if not isinstance(members, list):
                raise CanonicalRepositoryError(f"legacy members must be a list: {project_id}")
            for member in members:
                if not isinstance(member, dict) or not str(member.get("actor_id") or "").strip():
                    raise CanonicalRepositoryError(f"legacy member must have actor_id: {project_id}")
                self.add_member(ProjectMember(
                    project_id=project_id, actor_id=str(member["actor_id"]).strip(),
                    role=member.get("role", "viewer"), created_at=now,
                ))

    def compare_legacy_projects(self, projects: list[dict[str, Any]]) -> tuple[str, ...]:
        self.migrate()
        differences: list[str] = []
        source_ids = {str(item.get("id") or "").strip() for item in projects if isinstance(item, dict) and str(item.get("id") or "").strip()}
        canonical = {record.id: record for record in self.list_projects()}
        if source_ids != set(canonical):
            differences.append("project_ids")
        for source in projects:
            project_id = str(source.get("id") or "").strip()
            record = canonical.get(project_id)
            if record is None:
                continue
            if record.name != str(source.get("name") or "未命名项目")[:500]:
                differences.append(f"{project_id}.name")
            if _project_order(record) != _legacy_order(source.get("order")):
                differences.append(f"{project_id}.order")
            expected_members = sorted(
                (str(member.get("actor_id")).strip(), str(member.get("role", "viewer")))
                for member in source.get("members", [{"actor_id": LOCAL_WORKSPACE_ACTOR_ID, "role": "owner"}])
                if isinstance(member, dict) and member.get("actor_id")
            )
            actual_members = sorted((member["actor_id"], member["role"]) for member in self.list_project_members(project_id))
            if expected_members != actual_members:
                differences.append(f"{project_id}.members")
            if record.metadata.get("legacy", {}).get("source") != source:
                differences.append(f"{project_id}.payload")
        return tuple(sorted(set(differences)))

    def project_authority(self) -> str:
        self.migrate()
        with self._connection() as connection:
            row = connection.execute("SELECT project_authority FROM project_authority_state WHERE singleton=1").fetchone()
        return str(row["project_authority"])

    def activate_sqlite_project_authority(self, projects: list[dict[str, Any]]) -> None:
        differences = self.compare_legacy_projects(projects)
        if differences:
            raise CanonicalRepositoryError(f"Legacy project comparison failed: {', '.join(differences)}")
        with self._connection() as connection:
            connection.execute(
                "UPDATE project_authority_state SET project_authority='sqlite', updated_at=? WHERE singleton=1",
                (_iso(self._clock()),),
            )

    def authorization(self) -> AuthorizationService:
        return AuthorizationService(self)

    def load_project(self, project_id: str) -> ProjectRecord:
        self.migrate()
        with self._connection() as connection:
            row = connection.execute("SELECT * FROM projects WHERE id=?", (project_id,)).fetchone()
        if not row:
            raise CanonicalNotFoundError("project not found")
        return ProjectRecord(id=row["id"], name=row["name"], workspace_id=row["workspace_id"], created_by=row["created_by"], created_at=_parse_iso(row["created_at"]), updated_at=_parse_iso(row["updated_at"]), revision=row["revision"], metadata=json.loads(row["metadata_json"]))

    def list_projects(self) -> list[ProjectRecord]:
        self.migrate()
        with self._connection() as connection:
            rows = connection.execute("SELECT * FROM projects").fetchall()
        return [self.load_project(row["id"]) for row in rows]

    def update_project(self, project_id: str, *, name: str | None = None, order: int | None = None) -> ProjectRecord:
        current = self.load_project(project_id)
        if name is not None and not str(name).strip():
            raise CanonicalRepositoryError("project name is required")
        if name is not None and len(str(name)) > 500:
            raise CanonicalRepositoryError("project name is too long")
        metadata = dict(current.metadata)
        if order is not None:
            legacy = metadata.get("legacy")
            if not isinstance(legacy, dict):
                legacy = {}
                metadata["legacy"] = legacy
            legacy["order"] = int(order)
        with self._connection() as connection:
            updated = connection.execute(
                "UPDATE projects SET name=?, updated_at=?, revision=revision+1, metadata_json=? WHERE id=?",
                (name if name is not None else current.name, _iso(self._clock()), json.dumps(metadata, sort_keys=True), project_id),
            )
            if updated.rowcount != 1:
                raise CanonicalNotFoundError("project not found")
            self._append_audit(connection, "project.updated", project_id, None, current.created_by, {"revision": current.revision + 1})
        return self.load_project(project_id)

    def delete_project(self, project_id: str) -> None:
        self.migrate()
        with self._connection() as connection:
            row = connection.execute("SELECT created_by FROM projects WHERE id=?", (project_id,)).fetchone()
            if not row:
                raise CanonicalNotFoundError("project not found")
            self._append_audit(connection, "project.deleted", project_id, None, row["created_by"], {})
            connection.execute("INSERT OR IGNORE INTO legacy_project_exclusions(project_id) VALUES (?)", (project_id,))
            connection.execute("DELETE FROM project_members WHERE project_id=?", (project_id,))
            deleted = connection.execute("DELETE FROM projects WHERE id=?", (project_id,)).rowcount
        if deleted != 1:
            raise CanonicalNotFoundError("project not found")

    def legacy_project_excluded(self, project_id: str) -> bool:
        self.migrate()
        with self._connection() as connection:
            row = connection.execute("SELECT 1 FROM legacy_project_exclusions WHERE project_id=?", (project_id,)).fetchone()
        return row is not None

    def load_canvas_record(self, canvas_id: str) -> CanvasRecord:
        row = self._canvas_row(canvas_id)
        return self._canvas_record(row)

    def load_canvas_payload(self, canvas_id: str) -> dict[str, Any]:
        row = self._canvas_row(canvas_id)
        return json.loads(row["payload_json"])

    def load_canvas_snapshot(self, canvas_id: str) -> CanvasPayloadSnapshot:
        """Load the compatibility payload and CAS revision from one SQLite snapshot."""
        self.migrate()
        with self._connection() as connection:
            row = connection.execute("SELECT payload_json, revision FROM canvases WHERE id=?", (canvas_id,)).fetchone()
        if not row:
            raise CanonicalNotFoundError("canvas not found")
        return CanvasPayloadSnapshot(payload=json.loads(row["payload_json"]), revision=int(row["revision"]))

    def list_canvas_payloads(self, *, include_deleted: bool = False) -> list[dict[str, Any]]:
        self.migrate()
        query = "SELECT payload_json FROM canvases"
        if not include_deleted:
            query += " WHERE deleted_at IS NULL"
        query += " ORDER BY id"
        with self._connection() as connection:
            rows = connection.execute(query).fetchall()
        return [json.loads(row["payload_json"]) for row in rows]

    def import_legacy_canvases(self, canvases: list[dict[str, Any]], mapper: LegacyIdentityMapper) -> LegacyImportReport:
        self.migrate()
        resolutions: dict[str, LegacyIdentityResolution] = {}
        imported: list[str] = []
        skipped: list[str] = []
        for payload in canvases:
            canvas_id = str(payload.get("id") or "").strip()
            if not canvas_id:
                continue
            resolution = mapper.resolve(payload)
            resolutions[canvas_id] = resolution
            if resolution.issues:
                skipped.append(canvas_id)
                continue
            self._import_legacy_canvas(payload, resolution)
            imported.append(canvas_id)
        return LegacyImportReport(tuple(imported), tuple(skipped), resolutions)

    def create_canvas_payload(self, *, actor_id: str, payload: dict[str, Any]) -> tuple[CanvasRecord, dict[str, Any]]:
        """Create one lossless compatibility payload under canonical authorization."""
        self.migrate()
        canvas_id = str(payload.get("id") or "").strip()
        project_id = str(payload.get("project") or DEFAULT_PROJECT_ID).strip() or DEFAULT_PROJECT_ID
        if not canvas_id:
            raise CanonicalRepositoryError("canvas id is required")
        copy = deepcopy(payload)
        copy["id"] = canvas_id
        copy["project"] = project_id
        with self._connection() as connection:
            if connection.execute("SELECT 1 FROM canvases WHERE id=?", (canvas_id,)).fetchone():
                raise CanonicalRepositoryError("canvas already exists")
            if not connection.execute("SELECT 1 FROM projects WHERE id=?", (project_id,)).fetchone():
                raise CanonicalNotFoundError("project not found")
            AuthorizationService(_ConnectionMembershipReader(connection)).require(actor_id, Action.CANVAS_EDIT, project_id)
            now = self._clock()
            created = _parse_legacy_time(copy.get("created_at")) or now
            updated = _parse_legacy_time(copy.get("updated_at")) or created
            connection.execute(
                "INSERT INTO canvases VALUES (?, ?, ?, ?, ?, 1, ?, ?, ?, ?)",
                (canvas_id, project_id, str(copy.get("title") or "未命名画布"),
                 json.dumps(copy.get("viewport") or {}, sort_keys=True), json.dumps(copy, ensure_ascii=False, sort_keys=True),
                 _iso(created), _iso(updated), _iso(_parse_legacy_time(copy.get("deleted_at"))) if copy.get("deleted_at") else None,
                 json.dumps({"legacy": {"kind": copy.get("kind"), "owner_state": "compatibility"}}, sort_keys=True)),
            )
            self._append_audit(connection, "canvas.created", project_id, canvas_id, actor_id, {"revision": 1})
            row = connection.execute("SELECT * FROM canvases WHERE id=?", (canvas_id,)).fetchone()
        return self._canvas_record(row), copy

    def replace_canvas_payload(self, *, actor_id: str, canvas_id: str, expected_revision: int, payload: dict[str, Any]) -> tuple[CanvasRecord, dict[str, Any]]:
        """Replace a Legacy-shaped payload through the canonical mutation transaction."""
        replacement = deepcopy(payload)

        def replace(current: dict[str, Any]) -> None:
            current.clear()
            current.update(replacement)

        return self.mutate_canvas(actor_id=actor_id, canvas_id=canvas_id, expected_revision=expected_revision, mutation=replace)

    def purge_canvas_payload(self, *, actor_id: str, canvas_id: str) -> bool:
        self.migrate()
        with self._connection() as connection:
            row = connection.execute("SELECT project_id FROM canvases WHERE id=?", (canvas_id,)).fetchone()
            if not row:
                return False
            AuthorizationService(_ConnectionMembershipReader(connection)).require(actor_id, Action.CANVAS_EDIT, row["project_id"])
            self._append_audit(connection, "canvas.purged", row["project_id"], canvas_id, actor_id, {})
            connection.execute("DELETE FROM canvases WHERE id=?", (canvas_id,))
        return True

    def purge_expired_canvas_payloads(self, *, actor_id: str, before_ms: int) -> int:
        removed = 0
        for payload in self.list_canvas_payloads(include_deleted=True):
            if int(payload.get("deleted_at") or 0) and int(payload["deleted_at"]) < before_ms:
                removed += int(self.purge_canvas_payload(actor_id=actor_id, canvas_id=str(payload.get("id") or "")))
        return removed

    def reassign_canvas_projects(self, *, actor_id: str, source_project_id: str, target_project_id: str) -> int:
        self.migrate()
        with self._connection() as connection:
            authorization = AuthorizationService(_ConnectionMembershipReader(connection))
            authorization.require(actor_id, Action.CANVAS_EDIT, source_project_id)
            authorization.require(actor_id, Action.CANVAS_EDIT, target_project_id)
            rows = connection.execute("SELECT * FROM canvases WHERE project_id=?", (source_project_id,)).fetchall()
            now = self._clock()
            for row in rows:
                payload = json.loads(row["payload_json"])
                payload["project"] = target_project_id
                revision = int(row["revision"]) + 1
                connection.execute("UPDATE canvases SET project_id=?, payload_json=?, revision=?, updated_at=? WHERE id=?", (target_project_id, json.dumps(payload, ensure_ascii=False, sort_keys=True), revision, _iso(now), row["id"]))
                self._append_audit(connection, "canvas.project_reassigned", target_project_id, row["id"], actor_id, {"from_project_id": source_project_id, "revision": revision})
        return len(rows)

    def canvas_authority(self) -> str:
        self.migrate()
        with self._connection() as connection:
            row = connection.execute("SELECT canvas_authority FROM authority_state WHERE singleton=1").fetchone()
        return str(row["canvas_authority"])

    def activate_sqlite_authority(self, legacy_canvases: list[dict[str, Any]]) -> None:
        """Controlled switch: all supplied Legacy payloads must already compare."""
        for legacy in legacy_canvases:
            matched, differences = self.compare_legacy_payload(legacy)
            if not matched:
                raise CanonicalRepositoryError(f"Legacy comparison failed for {legacy.get('id')}: {', '.join(differences)}")
        with self._connection() as connection:
            connection.execute("UPDATE authority_state SET canvas_authority='sqlite', updated_at=? WHERE singleton=1", (_iso(self._clock()),))

    def rollback_to_legacy_authority(self) -> list[dict[str, Any]]:
        """Return lossless export before restoring the explicit Legacy authority state."""
        self.migrate()
        with self._connection() as connection:
            rows = connection.execute("SELECT payload_json FROM canvases ORDER BY id").fetchall()
            exports = [json.loads(row["payload_json"]) for row in rows]
            connection.execute("UPDATE authority_state SET canvas_authority='legacy_json', updated_at=? WHERE singleton=1", (_iso(self._clock()),))
        return exports

    def _import_legacy_canvas(self, payload: dict[str, Any], resolution: LegacyIdentityResolution) -> None:
        canvas_id = str(payload["id"])
        timestamp = self._clock()
        created = _parse_legacy_time(payload.get("created_at")) or timestamp
        updated = _parse_legacy_time(payload.get("updated_at")) or created
        copy = deepcopy(payload)
        copy["project"] = resolution.project_id
        with self._connection() as connection:
            connection.execute(
                """INSERT INTO canvases VALUES (?, ?, ?, ?, ?, 1, ?, ?, ?, ?)
                   ON CONFLICT(id) DO UPDATE SET project_id=excluded.project_id, title=excluded.title,
                     viewport_json=excluded.viewport_json, payload_json=excluded.payload_json,
                     updated_at=excluded.updated_at, deleted_at=excluded.deleted_at, metadata_json=excluded.metadata_json""",
                (canvas_id, resolution.project_id, str(copy.get("title") or "未命名画布"),
                 json.dumps(copy.get("viewport") or {}, sort_keys=True), json.dumps(copy, ensure_ascii=False, sort_keys=True),
                 _iso(created), _iso(updated), _iso(_parse_legacy_time(copy.get("deleted_at"))) if copy.get("deleted_at") else None,
                 json.dumps({"legacy": {"kind": copy.get("kind"), "owner_state": resolution.owner_state}}, sort_keys=True)),
            )
            if resolution.owner_actor_id:
                connection.execute(
                    "INSERT OR IGNORE INTO project_members VALUES (?, ?, 'editor', ?)",
                    (resolution.project_id, resolution.owner_actor_id, _iso(timestamp)),
                )
            self._append_audit(connection, "canvas.imported", resolution.project_id, canvas_id, LOCAL_WORKSPACE_ACTOR_ID, {"owner_state": resolution.owner_state})

    def mutate_canvas(self, *, actor_id: str, canvas_id: str, expected_revision: int, mutation: Callable[[dict[str, Any]], None]) -> tuple[CanvasRecord, dict[str, Any]]:
        if expected_revision < 1:
            raise CanonicalRepositoryError("expected_revision must be positive")
        self.migrate()
        with self._connection() as connection:
            row = connection.execute("SELECT * FROM canvases WHERE id=?", (canvas_id,)).fetchone()
            if not row:
                raise CanonicalNotFoundError("canvas not found")
            if int(row["revision"]) != expected_revision:
                raise CanonicalStaleRevisionError(int(row["revision"]))
            authorization = AuthorizationService(_ConnectionMembershipReader(connection))
            authorization.require(actor_id, Action.CANVAS_EDIT, row["project_id"])
            payload = json.loads(row["payload_json"])
            mutation(payload)
            now = self._clock()
            revision = int(row["revision"]) + 1
            payload["id"] = canvas_id
            payload["project"] = row["project_id"]
            updated_cursor = connection.execute(
                "UPDATE canvases SET title=?, viewport_json=?, payload_json=?, revision=?, updated_at=?, deleted_at=? WHERE id=? AND revision=?",
                (str(payload.get("title") or row["title"]), json.dumps(payload.get("viewport") or {}, sort_keys=True),
                 json.dumps(payload, ensure_ascii=False, sort_keys=True), revision, _iso(now),
                 _iso(_parse_legacy_time(payload.get("deleted_at"))) if payload.get("deleted_at") else None, canvas_id, expected_revision),
            )
            if updated_cursor.rowcount != 1:
                current = connection.execute("SELECT revision FROM canvases WHERE id=?", (canvas_id,)).fetchone()
                if not current:
                    raise CanonicalNotFoundError("canvas not found")
                raise CanonicalStaleRevisionError(int(current["revision"]))
            self._append_audit(connection, "canvas.mutated", row["project_id"], canvas_id, actor_id, {"revision": revision})
            updated = connection.execute("SELECT * FROM canvases WHERE id=?", (canvas_id,)).fetchone()
        return self._canvas_record(updated), payload

    def compare_legacy_payload(self, legacy: dict[str, Any]) -> tuple[bool, tuple[str, ...]]:
        canonical = self.load_canvas_payload(str(legacy.get("id") or ""))
        ignored = {"project"}
        differences = tuple(key for key in sorted(set(legacy) | set(canonical)) if key not in ignored and legacy.get(key) != canonical.get(key))
        return not differences, differences

    def export_legacy_payload(self, canvas_id: str) -> dict[str, Any]:
        return self.load_canvas_payload(canvas_id)

    def outbox_events(self) -> list[dict[str, Any]]:
        self.migrate()
        with self._connection() as connection:
            rows = connection.execute("SELECT * FROM audit_outbox ORDER BY id").fetchall()
        return [{"event_type": row["event_type"], "project_id": row["project_id"], "canvas_id": row["canvas_id"], "actor_id": row["actor_id"], "payload": json.loads(row["payload_json"]), "occurred_at": row["occurred_at"]} for row in rows]

    def _canvas_row(self, canvas_id: str) -> sqlite3.Row:
        self.migrate()
        with self._connection() as connection:
            row = connection.execute("SELECT * FROM canvases WHERE id=?", (canvas_id,)).fetchone()
        if not row:
            raise CanonicalNotFoundError("canvas not found")
        return row

    @staticmethod
    def _canvas_record(row: sqlite3.Row) -> CanvasRecord:
        return CanvasRecord(id=row["id"], project_id=row["project_id"], title=row["title"], viewport=json.loads(row["viewport_json"]), revision=row["revision"], created_at=_parse_iso(row["created_at"]), updated_at=_parse_iso(row["updated_at"]), deleted_at=_parse_iso(row["deleted_at"]), metadata=json.loads(row["metadata_json"]))

    @staticmethod
    def _append_audit(connection: sqlite3.Connection, event_type: str, project_id: str, canvas_id: str | None, actor_id: str, payload: dict[str, Any]) -> None:
        connection.execute("INSERT INTO audit_outbox(event_type, project_id, canvas_id, actor_id, payload_json, occurred_at) VALUES (?, ?, ?, ?, ?, ?)", (event_type, project_id, canvas_id, actor_id, json.dumps(payload, sort_keys=True), _iso(_utcnow())))


class _ConnectionMembershipReader:
    def __init__(self, connection: sqlite3.Connection):
        self._connection = connection

    def member_role(self, project_id: str, actor_id: str) -> str | None:
        row = self._connection.execute("SELECT role FROM project_members WHERE project_id=? AND actor_id=?", (project_id, actor_id)).fetchone()
        return str(row["role"]) if row else None


def _parse_legacy_time(value: Any) -> datetime | None:
    try:
        if isinstance(value, (int, float)) and value:
            return datetime.fromtimestamp(float(value) / 1000, tz=UTC)
        if isinstance(value, str) and value:
            return _parse_iso(value)
    except (OverflowError, OSError, ValueError) as error:
        raise CanonicalRepositoryError("invalid legacy timestamp") from error
    return None

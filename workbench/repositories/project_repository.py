"""Canonical Project persistence boundary with Legacy JSON read compatibility."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol

from workbench.domain.project.models import ProjectMember, ProjectRecord
from workbench.repositories.sqlite_project_canvas_repository import (
    CanonicalNotFoundError,
    SqliteProjectCanvasRepository,
)


class ProjectRepository(Protocol):
    """Application-facing persistence contract for projects and membership."""

    def list_projects(self) -> list[ProjectRecord]: ...

    def load_project(self, project_id: str) -> ProjectRecord: ...

    def create_project(self, record: ProjectRecord, owner: ProjectMember | None = None) -> ProjectRecord: ...

    def update_project(self, project_id: str, *, name: str | None = None, order: int | None = None) -> ProjectRecord: ...

    def delete_project(self, project_id: str) -> None: ...

    def add_member(self, member: ProjectMember) -> None: ...

    def member_role(self, project_id: str, actor_id: str) -> str | None: ...

    def list_project_members(self, project_id: str) -> list[dict[str, str]]: ...

    def list_canonical_projects(self) -> list[ProjectRecord]: ...

    def project_authority(self) -> str: ...


def _legacy_datetime(value: Any, fallback: datetime) -> datetime:
    try:
        if isinstance(value, (int, float)) and value:
            return datetime.fromtimestamp(float(value) / 1000, tz=UTC)
        if isinstance(value, str) and value:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (OverflowError, OSError, ValueError):
        return fallback
    return fallback


def _legacy_order(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


class SqliteProjectRepository:
    """ProjectRepository backed by the existing canonical SQLite authority."""

    def __init__(self, database_path: str | Path, *, legacy_projects_path: str | Path | None = None):
        self._canonical = SqliteProjectCanvasRepository(database_path)
        self._legacy_projects_path = Path(legacy_projects_path) if legacy_projects_path else None

    def _ensure_legacy_read_compatibility(self) -> None:
        if self._canonical.project_authority() == "sqlite":
            return
        if self._legacy_projects_path is None or not self._legacy_projects_path.exists():
            return
        try:
            raw = json.loads(self._legacy_projects_path.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError):
            return
        records = raw.get("projects") if isinstance(raw, dict) else raw
        if not isinstance(records, list):
            return
        now = datetime.now(UTC)
        for source in records:
            if not isinstance(source, dict) or not source.get("id"):
                continue
            project_id = str(source["id"]).strip()
            if self._canonical.legacy_project_excluded(project_id):
                continue
            try:
                self._canonical.load_project(project_id)
            except CanonicalNotFoundError:
                created_at = _legacy_datetime(source.get("created_at"), now)
                updated_at = _legacy_datetime(source.get("updated_at"), created_at)
                self._canonical.create_project(
                    ProjectRecord(
                        id=project_id,
                        name=str(source.get("name") or "未命名项目")[:500],
                        workspace_id="local",
                        created_by="local-workspace-actor",
                        created_at=created_at,
                        updated_at=updated_at,
                        metadata={"legacy": {"order": _legacy_order(source.get("order")), "source": source}},
                    )
                )

    def list_projects(self) -> list[ProjectRecord]:
        self._canonical.migrate()
        self._ensure_legacy_read_compatibility()
        records = self._canonical.list_projects()
        return sorted(records, key=lambda record: (self.project_order(record), record.created_at, record.id))

    def load_project(self, project_id: str) -> ProjectRecord:
        self._canonical.migrate()
        self._ensure_legacy_read_compatibility()
        return self._canonical.load_project(project_id)

    def create_project(self, record: ProjectRecord, owner: ProjectMember | None = None) -> ProjectRecord:
        self._canonical.migrate()
        return self._canonical.create_project(record, owner)

    def update_project(self, project_id: str, *, name: str | None = None, order: int | None = None) -> ProjectRecord:
        return self._canonical.update_project(project_id, name=name, order=order)

    def delete_project(self, project_id: str) -> None:
        self._canonical.delete_project(project_id)

    def add_member(self, member: ProjectMember) -> None:
        self._canonical.add_member(member)

    def member_role(self, project_id: str, actor_id: str) -> str | None:
        return self._canonical.member_role(project_id, actor_id)

    def project_authority(self) -> str:
        return self._canonical.project_authority()

    def list_project_members(self, project_id: str) -> list[dict[str, str]]:
        return self._canonical.list_project_members(project_id)

    def list_canonical_projects(self) -> list[ProjectRecord]:
        return self._canonical.list_projects()

    def import_legacy_projects(self, projects: list[dict[str, Any]], *, now: datetime) -> None:
        self._canonical.import_legacy_projects(projects, now=now)

    def compare_legacy_projects(self, projects: list[dict[str, Any]]) -> tuple[str, ...]:
        return self._canonical.compare_legacy_projects(projects)

    def activate_sqlite_project_authority(self, projects: list[dict[str, Any]]) -> None:
        self._canonical.activate_sqlite_project_authority(projects)

    @staticmethod
    def project_order(record: ProjectRecord) -> int:
        legacy = record.metadata.get("legacy") if isinstance(record.metadata, dict) else {}
        try:
            return int(legacy.get("order") or 0) if isinstance(legacy, dict) else 0
        except (TypeError, ValueError):
            return 0

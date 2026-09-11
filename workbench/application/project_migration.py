"""Explicit Project JSON migration and authority cutover orchestration."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from workbench.repositories.project_repository import SqliteProjectRepository


@dataclass(frozen=True)
class ProjectMigrationReport:
    source_project_count: int
    sqlite_project_count: int
    source_member_count: int
    sqlite_member_count: int
    differences: tuple[str, ...]
    activated: bool


class ProjectMigrationService:
    """Import, compare, and explicitly switch project authority."""

    def __init__(self, repository: SqliteProjectRepository):
        self._repository = repository

    def migrate_and_compare(self, projects: list[dict[str, Any]], *, now: datetime) -> ProjectMigrationReport:
        self._repository.import_legacy_projects(projects, now=now)
        differences = self._repository.compare_legacy_projects(projects)
        source_members = sum(
            len(project.get("members", [{"actor_id": "local-workspace-actor", "role": "owner"}]))
            for project in projects
        )
        canonical_projects = self._repository.list_canonical_projects()
        sqlite_members = sum(len(self._repository.list_project_members(project.id)) for project in canonical_projects)
        return ProjectMigrationReport(
            source_project_count=len(projects),
            sqlite_project_count=len(canonical_projects),
            source_member_count=source_members,
            sqlite_member_count=sqlite_members,
            differences=differences,
            activated=False,
        )

    def activate_after_compare(self, projects: list[dict[str, Any]], report: ProjectMigrationReport) -> ProjectMigrationReport:
        current_differences = self._repository.compare_legacy_projects(projects)
        if report.differences or current_differences:
            raise ValueError("cannot activate project authority while comparisons differ")
        self._repository.activate_sqlite_project_authority(projects)
        return ProjectMigrationReport(**{**report.__dict__, "activated": True})

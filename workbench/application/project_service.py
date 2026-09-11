"""Application boundary for Project lifecycle operations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Callable, Protocol

from workbench.domain.project.models import ProjectRecord
from workbench.repositories.project_repository import ProjectRepository
from workbench.repositories.sqlite_project_canvas_repository import CanonicalNotFoundError, LOCAL_WORKSPACE_ACTOR_ID


class ProjectServiceError(ValueError):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)


class ProjectNotFoundError(ProjectServiceError):
    def __init__(self, project_id: str):
        super().__init__("not_found", f"project not found: {project_id}")


class ProjectCanvasReassigner(Protocol):
    def __call__(self, *, source_project_id: str, target_project_id: str) -> int: ...


@dataclass(frozen=True)
class ProjectArchiveResult:
    project_id: str
    moved_canvas_count: int


class ProjectService:
    """Validate Project commands and coordinate repository-owned persistence."""

    def __init__(
        self,
        repository: ProjectRepository,
        *,
        canvas_reassigner: ProjectCanvasReassigner | None = None,
        clock: Callable[[], datetime] | None = None,
        actor_id: str = LOCAL_WORKSPACE_ACTOR_ID,
    ):
        self._repository = repository
        self._canvas_reassigner = canvas_reassigner
        self._clock = clock or (lambda: datetime.now(UTC))
        self._actor_id = actor_id

    def list(self) -> list[ProjectRecord]:
        return self._repository.list_projects()

    def get(self, project_id: str) -> ProjectRecord:
        return self._require(project_id)

    def list_after_ensuring_default(self) -> list[ProjectRecord]:
        self.ensure_default()
        return self.list()

    def ensure_default(self) -> ProjectRecord:
        try:
            return self._repository.load_project("default")
        except CanonicalNotFoundError:
            now = self._clock()
            return self._repository.create_project(ProjectRecord(
                id="default",
                name="默认项目",
                workspace_id="local",
                created_by=self._actor_id,
                created_at=now,
                updated_at=now,
            ))

    def create(self, name: str | None = None) -> ProjectRecord:
        self.ensure_default()
        projects = self._repository.list_projects()
        clean_name = self._clean_name(name, fallback="新项目")
        order = max((self._project_order(project) for project in projects), default=0) + 1
        now = self._clock()
        return self._repository.create_project(ProjectRecord(
            id=self._new_id(),
            name=clean_name,
            workspace_id="local",
            created_by=self._actor_id,
            created_at=now,
            updated_at=now,
            metadata={"legacy": {"order": order}},
        ))

    def update(self, project_id: str, *, name: str | None = None, order: int | None = None) -> ProjectRecord:
        self._require(project_id)
        clean_name = self._clean_name(name, fallback=None) if name is not None else None
        try:
            return self._repository.update_project(project_id, name=clean_name, order=order)
        except CanonicalNotFoundError as error:
            raise ProjectNotFoundError(project_id) from error

    def archive(self, project_id: str) -> ProjectArchiveResult:
        if project_id == "default":
            raise ProjectServiceError("invalid_request", "默认项目不可删除")
        self._require(project_id)
        self.ensure_default()
        if self._canvas_reassigner is None:
            raise ProjectServiceError("configuration", "canvas reassigner is required to archive a project")
        moved = self._canvas_reassigner(source_project_id=project_id, target_project_id="default")
        try:
            self._repository.delete_project(project_id)
        except CanonicalNotFoundError as error:
            raise ProjectNotFoundError(project_id) from error
        return ProjectArchiveResult(project_id=project_id, moved_canvas_count=moved)

    def _require(self, project_id: str) -> ProjectRecord:
        try:
            return self._repository.load_project(project_id)
        except CanonicalNotFoundError as error:
            raise ProjectNotFoundError(project_id) from error

    @staticmethod
    def _clean_name(name: str | None, *, fallback: str | None) -> str:
        clean = str(name).strip() if name is not None else ""
        if not clean:
            if fallback is None:
                raise ProjectServiceError("invalid_request", "project name is required")
            clean = fallback
        if len(clean) > 60:
            clean = clean[:60]
        return clean

    @staticmethod
    def _project_order(project: ProjectRecord) -> int:
        legacy = project.metadata.get("legacy") if isinstance(project.metadata, dict) else None
        try:
            return int(legacy.get("order") or 0) if isinstance(legacy, dict) else 0
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def _new_id() -> str:
        import uuid
        return uuid.uuid4().hex

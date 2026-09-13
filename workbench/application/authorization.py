"""Action/resource authorization for canonical Project and Canvas operations."""

from enum import StrEnum
from typing import Protocol


class Action(StrEnum):
    PROJECT_READ = "project.read"
    CANVAS_EDIT = "canvas.edit"
    COLLECTION_READ = "collection.read"
    COLLECTION_EDIT = "collection.edit"
    PROMPT_READ = "prompt.read"
    PROMPT_EDIT = "prompt.edit"
    EXECUTION_READ = "execution.read"
    EXECUTION_EDIT = "execution.edit"


class AuthorizationError(PermissionError):
    pass


class ProjectMembershipReader(Protocol):
    def member_role(self, project_id: str, actor_id: str) -> str | None: ...


class AuthorizationService:
    """Small R3 action policy; authentication remains outside this local mapping."""

    def __init__(self, memberships: ProjectMembershipReader):
        self._memberships = memberships

    def allows(self, actor_id: str, action: Action, project_id: str) -> bool:
        role = self._memberships.member_role(project_id, actor_id)
        if action in {Action.PROJECT_READ, Action.COLLECTION_READ, Action.PROMPT_READ, Action.EXECUTION_READ}:
            return role in {"owner", "editor", "viewer"}
        if action in {Action.CANVAS_EDIT, Action.COLLECTION_EDIT, Action.PROMPT_EDIT, Action.EXECUTION_EDIT}:
            return role in {"owner", "editor"}
        return False

    def require(self, actor_id: str, action: Action, project_id: str) -> None:
        if not self.allows(actor_id, action, project_id):
            raise AuthorizationError(f"actor is not permitted to perform {action.value}")

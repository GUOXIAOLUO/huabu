"""Atomic, industry-neutral group-membership mutations for migrated Canvas actions.

Group membership (the legacy ``items`` list of member node ids on a ``group`` /
``smart-group`` node) is a Classic/Smart visual-organization concern. The
application boundary owns request validity, authorization, and optimistic
concurrency; the repository port persists the legacy ``items`` shape under one
canvas lock so no page-side raw save performs the durable write.

This module deliberately has no notion of geometry, connection hand-off, or
``group.images`` grid absorption — those stay page-side compatibility.
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Callable, Protocol

from workbench.application.node_creation import ProjectAuthorizer
from workbench.domain.canvas.models import NodeRecord


class GroupMutationError(ValueError):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)


@dataclass(frozen=True)
class GroupMembershipCommand:
    """Add or remove one member node from a group's legacy ``items`` list."""

    actor_id: str
    project_id: str
    canvas_id: str
    expected_revision: int
    group_id: str
    member_id: str
    operation: str = "add"  # "add" | "remove"


@dataclass(frozen=True)
class GroupMembershipPersistence:
    canvas_revision: int
    group: NodeRecord


@dataclass(frozen=True)
class GroupMembershipChangedAuditEvent:
    actor_id: str
    project_id: str
    canvas_id: str
    group_id: str
    member_id: str
    operation: str
    occurred_at: datetime


class AtomicGroupMembershipRepository(Protocol):
    def set_group_membership(self, command: GroupMembershipCommand) -> GroupMembershipPersistence: ...


class AuditSink(Protocol):
    def append(self, event: GroupMembershipChangedAuditEvent) -> None: ...


class GroupMembershipService:
    """Authorize and audit a group-membership change before persistence mutates."""

    def __init__(
        self,
        *,
        authorizer: ProjectAuthorizer,
        repository: AtomicGroupMembershipRepository,
        audit_sink: AuditSink,
        clock: Callable[[], datetime] | None = None,
    ):
        self._authorizer = authorizer
        self._repository = repository
        self._audit_sink = audit_sink
        self._clock = clock or (lambda: datetime.now(UTC))

    def set_membership(self, command: GroupMembershipCommand) -> GroupMembershipPersistence:
        for name in ("actor_id", "project_id", "canvas_id", "group_id", "member_id"):
            if not str(getattr(command, name) or "").strip():
                raise GroupMutationError("invalid_request", f"{name} is required")
        if command.expected_revision < 1:
            raise GroupMutationError("invalid_request", "expected_revision must be positive")
        if command.operation not in {"add", "remove"}:
            raise GroupMutationError("invalid_request", "operation must be add or remove")
        if command.group_id == command.member_id:
            raise GroupMutationError("invalid_graph", "a group cannot contain itself")
        if not self._authorizer.can_edit(command.actor_id, command.project_id, command.canvas_id):
            raise GroupMutationError("forbidden", "actor is not permitted to edit this Canvas")
        persisted = self._repository.set_group_membership(command)
        self._audit_sink.append(GroupMembershipChangedAuditEvent(
            actor_id=command.actor_id, project_id=command.project_id, canvas_id=command.canvas_id,
            group_id=command.group_id, member_id=command.member_id, operation=command.operation,
            occurred_at=self._clock(),
        ))
        return persisted

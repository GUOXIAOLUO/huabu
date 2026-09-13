"""Explicit discovery boundary for system, package, user, and project Prompts."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from workbench.domain.prompt import PromptDefinition, PromptRef
from workbench.repositories.prompt_repository import PromptRepository

PromptSource = Literal["system", "package", "project", "user"]


class PromptRegistration(BaseModel):
    """Discoverability metadata; it never embeds PromptVersion content."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    prompt: PromptRef
    name: str = Field(min_length=1, max_length=500)
    description: str = Field(default="", max_length=5_000)
    source: PromptSource
    source_id: str = Field(default="", max_length=255)
    tags: tuple[str, ...] = ()
    metadata: dict[str, Any] = Field(default_factory=dict)


class PromptRegistry:
    """Combine explicit registrations with authorized project-owned Prompts."""

    def __init__(self, repository: PromptRepository, *, actor_id: str, registrations: Iterable[PromptRegistration] = ()):
        self._repository = repository
        self._actor_id = actor_id
        self._registrations: dict[tuple[str, int], PromptRegistration] = {}
        for registration in registrations:
            self.register(registration)

    def register(self, registration: PromptRegistration) -> None:
        key = (registration.prompt.prompt_id, registration.prompt.version)
        if key in self._registrations:
            raise ValueError(f"prompt is already registered: {registration.prompt.prompt_id}@{registration.prompt.version}")
        self._registrations[key] = registration

    def discover(self, project_id: str, *, query: str = "", source: PromptSource | None = None) -> list[PromptRegistration]:
        # Calling the repository first both supplies project records and enforces project read authorization.
        definitions = self._repository.list(project_id, actor_id=self._actor_id)
        entries = [self._from_definition(definition) for definition in definitions]
        entries.extend(
            entry for entry in self._registrations.values()
            if entry.source != "user" or entry.source_id == self._actor_id
        )
        normalized_query = query.strip().casefold()
        return sorted(
            [entry for entry in entries if self._matches(entry, normalized_query, source)],
            key=lambda entry: (entry.name.casefold(), entry.prompt.prompt_id, entry.prompt.version),
        )

    @staticmethod
    def _from_definition(definition: PromptDefinition) -> PromptRegistration:
        return PromptRegistration(
            prompt=PromptRef(prompt_id=definition.id, version=definition.current_version),
            name=definition.name,
            description=definition.description,
            source="project",
            source_id=definition.project_id,
            tags=tuple(definition.metadata.get("tags", ())) if isinstance(definition.metadata.get("tags", ()), (list, tuple)) else (),
            metadata=definition.metadata,
        )

    @staticmethod
    def _matches(entry: PromptRegistration, query: str, source: PromptSource | None) -> bool:
        if source is not None and entry.source != source:
            return False
        if not query:
            return True
        haystack = " ".join((entry.name, entry.description, entry.source_id, *entry.tags)).casefold()
        return query in haystack

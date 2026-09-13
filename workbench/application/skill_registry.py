"""Explicit discovery boundary for installed Workbench Skills."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from workbench.domain.skill import SkillDefinition, SkillPack, SkillRef


SkillSource = Literal["system", "package", "project", "user"]


class SkillRegistration(BaseModel):
    """Discoverability metadata kept separate from the Skill contract itself."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    skill: SkillDefinition
    source: SkillSource
    source_id: str = Field(default="", max_length=255)
    tags: tuple[str, ...] = ()
    metadata: dict[str, Any] = Field(default_factory=dict)


class SkillPackRegistration(BaseModel):
    """Discoverability metadata for one installed SkillPack."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    pack: SkillPack
    source: SkillSource
    source_id: str = Field(default="", max_length=255)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SkillRegistryError(ValueError):
    """Raised when registration or exact-version resolution violates the contract."""


class SkillRegistry:
    """Register and discover installed Skills without executing or fetching them."""

    def __init__(
        self,
        registrations: Iterable[SkillRegistration] = (),
        packs: Iterable[SkillPackRegistration] = (),
    ):
        self._registrations: dict[tuple[str, str], SkillRegistration] = {}
        self._packs: dict[tuple[str, str], SkillPackRegistration] = {}
        self._pack_enabled: dict[tuple[str, str], bool] = {}
        for registration in registrations:
            self.register(registration)
        for registration in packs:
            self.register_pack(registration)

    def register(self, registration: SkillRegistration) -> SkillRegistration:
        if not isinstance(registration, SkillRegistration):
            raise TypeError("SkillRegistry accepts SkillRegistration values")
        key = self._key(registration.skill.id, registration.skill.version)
        if key in self._registrations:
            raise SkillRegistryError(f"skill is already registered: {registration.skill.id}@{registration.skill.version}")
        self._registrations[key] = registration
        return registration

    def unregister(self, skill_id: str, version: str) -> SkillRegistration | None:
        return self._registrations.pop(self._key(skill_id, version), None)

    def register_pack(self, registration: SkillPackRegistration) -> SkillPackRegistration:
        if not isinstance(registration, SkillPackRegistration):
            raise TypeError("SkillRegistry accepts SkillPackRegistration values")
        key = self._key(registration.pack.id, registration.pack.version)
        if key in self._packs:
            raise SkillRegistryError(f"skill pack is already registered: {registration.pack.id}@{registration.pack.version}")
        self._packs[key] = registration
        self._pack_enabled[key] = registration.pack.enabled
        return registration

    def unregister_pack(self, pack_id: str, version: str) -> SkillPackRegistration | None:
        key = self._key(pack_id, version)
        self._pack_enabled.pop(key, None)
        return self._packs.pop(key, None)

    def list_packs(self, *, enabled: bool | None = None, source: SkillSource | None = None) -> list[SkillPackRegistration]:
        return sorted(
            (self._pack_registration(key) for key, registration in self._packs.items()
             if (enabled is None or self._pack_enabled[key] == enabled)
             and (source is None or registration.source == source)),
            key=lambda item: (item.pack.title.casefold(), item.pack.id, item.pack.version),
        )

    def resolve_pack(self, pack_id: str, version: str) -> SkillPackRegistration | None:
        key = self._key(pack_id, version)
        return self._pack_registration(key) if key in self._packs else None

    def set_pack_enabled(self, pack_id: str, version: str, enabled: bool) -> SkillPackRegistration:
        key = self._key(pack_id, version)
        if key not in self._packs:
            raise SkillRegistryError(f"skill pack is not registered: {pack_id}@{version}")
        self._pack_enabled[key] = bool(enabled)
        return self._pack_registration(key)

    def list(
        self,
        *,
        source: SkillSource | None = None,
        package_id: str | None = None,
        include_disabled: bool = False,
    ) -> list[SkillRegistration]:
        return self._sorted(
            registration
            for registration in self._registrations.values()
            if (source is None or registration.source == source)
            and (package_id is None or (registration.skill.package is not None and registration.skill.package.package_id == package_id))
            and (include_disabled or self._skill_is_enabled(registration.skill.id, registration.skill.version))
        )

    def search(
        self,
        query: str = "",
        *,
        source: SkillSource | None = None,
        package_id: str | None = None,
        include_disabled: bool = False,
    ) -> list[SkillRegistration]:
        normalized_query = query.strip().casefold()
        return self._sorted(
            registration
            for registration in self.list(source=source, package_id=package_id, include_disabled=include_disabled)
            if not normalized_query or normalized_query in self._search_text(registration)
        )

    def discover(
        self,
        *,
        query: str = "",
        source: SkillSource | None = None,
        package_id: str | None = None,
        include_disabled: bool = False,
    ) -> list[SkillRegistration]:
        """Provide one future-facing discovery verb for Task and Agent callers."""
        return self.search(query, source=source, package_id=package_id, include_disabled=include_disabled)

    def resolve(self, skill_id: str, version: str) -> SkillRegistration | None:
        """Resolve one exact installed Skill version; never selects a fallback."""
        return self._registrations.get(self._key(skill_id, version))

    def require(self, skill_id: str, version: str) -> SkillRegistration:
        registration = self.resolve(skill_id, version)
        if registration is None:
            raise SkillRegistryError(f"skill is not registered: {skill_id}@{version}")
        return registration

    @staticmethod
    def _key(skill_id: str, version: str) -> tuple[str, str]:
        return str(skill_id), str(version)

    def _skill_is_enabled(self, skill_id: str, version: str) -> bool:
        memberships = [key for key, registration in self._packs.items() if SkillRef(skill_id=skill_id, version=version) in registration.pack.skills]
        return not memberships or any(self._pack_enabled[key] for key in memberships)

    def _pack_registration(self, key: tuple[str, str]) -> SkillPackRegistration:
        registration = self._packs[key]
        if registration.pack.enabled == self._pack_enabled[key]:
            return registration
        return registration.model_copy(update={"pack": registration.pack.model_copy(update={"enabled": self._pack_enabled[key]})})

    @staticmethod
    def _search_text(registration: SkillRegistration) -> str:
        package_id = registration.skill.package.package_id if registration.skill.package else ""
        return " ".join((
            registration.skill.id,
            registration.skill.title,
            registration.skill.description,
            registration.source,
            registration.source_id,
            package_id,
            *registration.tags,
        )).casefold()

    @staticmethod
    def _sorted(registrations: Iterable[SkillRegistration]) -> list[SkillRegistration]:
        return sorted(registrations, key=lambda item: (item.skill.title.casefold(), item.skill.id, item.skill.version))

"""Repository seam for versioned execution profiles."""

from __future__ import annotations

from typing import Protocol

from workbench.domain.execution import ExecutionProfile, ExecutionProfileRef


class ExecutionProfileRepository(Protocol):
    def save(self, profile: ExecutionProfile) -> ExecutionProfile: ...
    def get(self, profile_ref: ExecutionProfileRef) -> ExecutionProfile | None: ...
    def list(self, profile_id: str | None = None) -> list[ExecutionProfile]: ...


class InMemoryExecutionProfileRepository:
    """Deterministic profile persistence until durable storage is authorized."""

    def __init__(self):
        self._profiles: dict[tuple[str, int], ExecutionProfile] = {}

    def save(self, profile: ExecutionProfile) -> ExecutionProfile:
        if not isinstance(profile, ExecutionProfile):
            raise TypeError("execution profile repository accepts ExecutionProfile values")
        key = (profile.id, profile.version)
        if key in self._profiles:
            raise ValueError(f"execution profile version is already stored: {profile.id}@{profile.version}")
        self._profiles[key] = profile
        return profile

    def get(self, profile_ref: ExecutionProfileRef) -> ExecutionProfile | None:
        if not isinstance(profile_ref, ExecutionProfileRef):
            raise TypeError("execution profile repository accepts ExecutionProfileRef values")
        return self._profiles.get((profile_ref.profile_id, profile_ref.version))

    def list(self, profile_id: str | None = None) -> list[ExecutionProfile]:
        return sorted(
            (profile for profile in self._profiles.values() if profile_id is None or profile.id == profile_id),
            key=lambda profile: (profile.id, profile.version),
        )

"""Explicit discovery and resolution boundary for Workbench executors."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from workbench.domain.execution import Executor


ExecutorResolutionReason = Literal[
    "no_executors_registered",
    "no_selector",
    "runtime_route_unavailable",
    "execution_profile_unavailable",
    "capabilities_unavailable",
    "no_compatible_executor",
]


@dataclass(frozen=True)
class ExecutorRegistration:
    """Discoverability metadata for one executor implementation.

    Route and profile values are opaque references.  Their definitions and
    selection policy belong to later boundaries; the registry only matches
    exact references and declared capabilities.
    """

    executor: Executor
    capabilities: tuple[str, ...] = ()
    runtime_routes: tuple[str, ...] = ()
    execution_profiles: tuple[str, ...] = ()

    def __post_init__(self):
        if not isinstance(self.executor, Executor):
            raise TypeError("ExecutorRegistration requires an Executor")
        if not self.executor_ref:
            raise ValueError("executor_ref must be a non-empty string")
        for name, values in (
            ("capabilities", self.capabilities),
            ("runtime_routes", self.runtime_routes),
            ("execution_profiles", self.execution_profiles),
        ):
            if any(not isinstance(value, str) or not value for value in values):
                raise ValueError(f"executor {name} must contain non-empty strings")
            if len(values) != len(set(values)):
                raise ValueError(f"executor {name} must be unique")

    @property
    def executor_ref(self) -> str:
        return str(self.executor.executor_ref)


@dataclass(frozen=True)
class ExecutorResolution:
    """Deterministic result of an executor lookup, including no-match reasons."""

    executor: Executor | None
    candidate_executor_refs: tuple[str, ...] = ()
    reason: ExecutorResolutionReason | None = None

    @property
    def resolved(self) -> bool:
        return self.executor is not None


class ExecutorRegistryError(ValueError):
    """Raised when registration or required resolution violates the contract."""


class ExecutorRegistry:
    """Register and resolve executors without fallback or execution side effects."""

    def __init__(self, registrations: tuple[ExecutorRegistration, ...] = ()):
        self._registrations: dict[str, ExecutorRegistration] = {}
        for registration in registrations:
            self.register(registration)

    def register(self, registration: ExecutorRegistration) -> ExecutorRegistration:
        if not isinstance(registration, ExecutorRegistration):
            raise TypeError("ExecutorRegistry accepts ExecutorRegistration values")
        if registration.executor_ref in self._registrations:
            raise ExecutorRegistryError(f"executor is already registered: {registration.executor_ref}")
        self._registrations[registration.executor_ref] = registration
        return registration

    def unregister(self, executor_ref: str) -> ExecutorRegistration | None:
        return self._registrations.pop(str(executor_ref), None)

    def list(self) -> tuple[ExecutorRegistration, ...]:
        return tuple(self._registrations[key] for key in sorted(self._registrations))

    def resolve(
        self,
        *,
        runtime_route_ref: str | None = None,
        execution_profile_ref: str | None = None,
        required_capabilities: tuple[str, ...] = (),
    ) -> ExecutorResolution:
        """Resolve exact route/profile/capability constraints deterministically.

        A missing requested route/profile is never replaced by another
        registered route.  When several registrations match, the stable
        executor reference is the tie-breaker.
        """

        required = tuple(required_capabilities)
        if any(not isinstance(value, str) or not value for value in required):
            raise ValueError("required executor capabilities must be non-empty strings")
        if len(required) != len(set(required)):
            raise ValueError("required executor capabilities must be unique non-empty strings")
        for name, value in (("runtime_route_ref", runtime_route_ref), ("execution_profile_ref", execution_profile_ref)):
            if value is not None and (not isinstance(value, str) or not value):
                raise ValueError(f"{name} must be a non-empty string")
        if not self._registrations:
            return ExecutorResolution(None, reason="no_executors_registered")
        if runtime_route_ref is None and execution_profile_ref is None and not required:
            return ExecutorResolution(None, reason="no_selector")

        registrations = self.list()
        candidates = tuple(
            item for item in registrations
            if (runtime_route_ref is None or runtime_route_ref in item.runtime_routes)
            and (execution_profile_ref is None or execution_profile_ref in item.execution_profiles)
            and set(required).issubset(item.capabilities)
        )
        if candidates:
            return ExecutorResolution(
                executor=candidates[0].executor,
                candidate_executor_refs=tuple(item.executor_ref for item in candidates),
            )

        if runtime_route_ref is not None and not any(runtime_route_ref in item.runtime_routes for item in registrations):
            reason: ExecutorResolutionReason = "runtime_route_unavailable"
        elif execution_profile_ref is not None and not any(execution_profile_ref in item.execution_profiles for item in registrations):
            reason = "execution_profile_unavailable"
        elif required and not any(set(required).issubset(item.capabilities) for item in registrations):
            reason = "capabilities_unavailable"
        else:
            reason = "no_compatible_executor"
        return ExecutorResolution(None, reason=reason)

    def require(self, **kwargs) -> Executor:
        resolution = self.resolve(**kwargs)
        if not resolution.resolved:
            raise ExecutorRegistryError(f"executor resolution unavailable: {resolution.reason}")
        return resolution.executor

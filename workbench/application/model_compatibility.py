"""Deterministic Skill-capability matching against available model routes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from workbench.domain.availability import ModelAvailability


class CapabilityMatchError(ValueError):
    """Raised when capability requirements cannot be normalized safely."""


@dataclass(frozen=True)
class CompatibilityCandidate:
    availability: ModelAvailability
    compatible: bool
    score: int
    reasons: tuple[str, ...] = ()


@dataclass(frozen=True)
class CompatibilityResult:
    requirements: tuple[str, ...]
    selected: ModelAvailability | None
    candidates: tuple[CompatibilityCandidate, ...]
    reasons: tuple[str, ...] = ()

    @property
    def compatible(self) -> bool:
        return self.selected is not None


class ModelCompatibilityResolver:
    """Rank explicit routes without silently changing a requested route."""

    def resolve(
        self,
        requirements: Iterable[object],
        availabilities: Iterable[ModelAvailability],
        *,
        model_ref: str | None = None,
    ) -> CompatibilityResult:
        normalized = self.normalize_requirements(requirements)
        records = tuple(availabilities)
        candidates = tuple(
            self._candidate(item, normalized, model_ref=model_ref)
            for item in records
        )
        ranked = tuple(sorted(candidates, key=lambda item: (-item.score, item.availability.id)))
        compatible = tuple(item for item in ranked if item.compatible)
        if compatible:
            return CompatibilityResult(normalized, compatible[0].availability, ranked)
        reasons = tuple(dict.fromkeys(reason for item in ranked for reason in item.reasons))
        if not reasons:
            reasons = ("no_availability_routes",)
        return CompatibilityResult(normalized, None, ranked, reasons)

    @staticmethod
    def normalize_requirements(requirements: Iterable[object]) -> tuple[str, ...]:
        normalized: list[str] = []
        for requirement in requirements:
            raw = requirement if isinstance(requirement, str) else getattr(requirement, "id", "")
            value = str(raw).strip().casefold().replace("-", "_")
            if value and value not in normalized:
                normalized.append(value)
        if not normalized:
            raise CapabilityMatchError("capability requirements must not be empty")
        return tuple(sorted(normalized))

    @classmethod
    def _candidate(
        cls,
        availability: ModelAvailability,
        requirements: tuple[str, ...],
        *,
        model_ref: str | None,
    ) -> CompatibilityCandidate:
        reasons: list[str] = []
        if model_ref is not None and availability.model_ref != model_ref:
            reasons.append("model_ref_mismatch")
        if not availability.enabled:
            reasons.append("route_disabled")
        if availability.status != "available":
            reasons.append(f"route_status:{availability.status}")
        available = {cls._normalize(item) for item in availability.normalized_capabilities}
        missing = sorted(set(requirements) - available)
        reasons.extend(f"missing_capability:{item}" for item in missing)
        compatible = not reasons
        score = len(available.intersection(requirements)) if compatible else -len(missing)
        return CompatibilityCandidate(availability, compatible, score, tuple(reasons))

    @staticmethod
    def _normalize(value: object) -> str:
        return str(value).strip().casefold().replace("-", "_")

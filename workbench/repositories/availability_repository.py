"""Repository boundary for model availability route records."""

from __future__ import annotations

from typing import Protocol

from workbench.domain.availability import ModelAvailability


class AvailabilityRepository(Protocol):
    def save(self, availability: ModelAvailability) -> ModelAvailability: ...
    def get(self, availability_id: str) -> ModelAvailability | None: ...
    def list(self, *, model_ref: str | None = None) -> list[ModelAvailability]: ...


class InMemoryAvailabilityRepository:
    """Deterministic repository seam until durable availability storage is authorized."""

    def __init__(self):
        self._records: dict[str, ModelAvailability] = {}

    def save(self, availability: ModelAvailability) -> ModelAvailability:
        if not isinstance(availability, ModelAvailability):
            raise TypeError("availability repository accepts ModelAvailability values")
        self._records[availability.id] = availability
        return availability

    def get(self, availability_id: str) -> ModelAvailability | None:
        return self._records.get(availability_id)

    def list(self, *, model_ref: str | None = None) -> list[ModelAvailability]:
        records = self._records.values()
        if model_ref is not None:
            records = (item for item in records if item.model_ref == model_ref)
        return sorted(records, key=lambda item: item.id)

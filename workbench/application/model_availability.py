"""Application boundary for ModelAvailability route records."""

from __future__ import annotations

from workbench.domain.availability import ModelAvailability
from workbench.repositories.availability_repository import AvailabilityRepository


class ModelAvailabilityService:
    """Register and query explicit routes without selecting or executing them."""

    def __init__(self, repository: AvailabilityRepository):
        self._repository = repository

    def register(self, availability: ModelAvailability) -> ModelAvailability:
        return self._repository.save(availability)

    def get(self, availability_id: str) -> ModelAvailability | None:
        return self._repository.get(availability_id)

    def list_for_model(self, model_ref: str) -> list[ModelAvailability]:
        return self._repository.list(model_ref=model_ref)

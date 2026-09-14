"""Application validation for Canvas references to canonical AssetVersions."""

from typing import Protocol

from workbench.domain.asset import AssetVersionRef
from workbench.repositories.asset_repository import AssetRepositoryNotFoundError


class AssetVersionReader(Protocol):
    def get(self, asset_id: str, *, actor_id: str): ...
    def get_version(self, asset_id: str, version_id: str, *, actor_id: str): ...


class AssetVersionReferenceValidator:
    """Validates identity and project scope without owning Canvas persistence."""

    def __init__(self, assets: AssetVersionReader):
        self._assets = assets

    def validate(self, *, actor_id: str, project_id: str, reference: AssetVersionRef) -> None:
        try:
            asset = self._assets.get(reference.asset_id, actor_id=actor_id)
        except AssetRepositoryNotFoundError as error:
            raise LookupError("asset not found") from error
        if asset.project_id != project_id:
            raise PermissionError("asset belongs to another project")
        try:
            version = self._assets.get_version(reference.asset_id, reference.version_id, actor_id=actor_id)
        except AssetRepositoryNotFoundError as error:
            raise LookupError("asset version not found") from error
        if version.asset_id != reference.asset_id:
            raise LookupError("asset version belongs to another asset")

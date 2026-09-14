"""Application boundary for reading canonical assets and their versions."""

from __future__ import annotations

from typing import Protocol

from workbench.application.asset_query import AssetQuery, AssetQueryPage
from workbench.application.asset_versions import AssetVersionHistory
from workbench.application.authorization import Action
from workbench.repositories.asset_repository import SqliteAssetRepository
from workbench.domain.asset import Asset, AssetVersion


class AssetAuthorization(Protocol):
    def require(self, actor_id: str, action: Action, project_id: str) -> None: ...


class AssetService:
    def __init__(self, repository: SqliteAssetRepository, authorization: AssetAuthorization):
        self._repository = repository
        self._authorization = authorization

    def list(self, *, project_id: str, actor_id: str):
        self._authorization.require(actor_id, Action.PROJECT_READ, project_id)
        return self._repository.list_assets(project_id=project_id)

    def query(self, query: AssetQuery, *, actor_id: str) -> AssetQueryPage:
        """Search/filter/paginate one project's Asset identities.

        The query is the service's own input contract and already carries the
        project it is scoped to, so authorization is checked against
        `query.project_id` and nothing else: a caller cannot widen a query to a
        project it may not read by passing a second project id.
        """
        if not isinstance(query, AssetQuery):
            raise TypeError("AssetService.query requires an AssetQuery")
        self._authorization.require(actor_id, Action.PROJECT_READ, query.project_id)
        assets, total = self._repository.query_assets(query)
        return AssetQueryPage(
            items=tuple(assets), total=total, limit=query.limit, offset=query.offset
        )

    def get(self, asset_id: str, *, actor_id: str):
        asset = self._repository.load_asset(asset_id)
        self._authorization.require(actor_id, Action.PROJECT_READ, asset.project_id)
        return asset

    def get_version(self, asset_id: str, version_id: str, *, actor_id: str):
        version = self._repository.load_version(asset_id, version_id)
        asset = self._repository.load_asset(version.asset_id)
        self._authorization.require(actor_id, Action.PROJECT_READ, asset.project_id)
        return version

    def history(self, asset_id: str, *, actor_id: str) -> AssetVersionHistory:
        """One asset's version history, after the asset's own authorization.

        The identity is loaded first because the authorization decision belongs
        to the *asset*: a version read cannot authorize itself, and taking the
        project from the caller instead would make the caller a second owner of
        the scope. A missing asset is a `AssetRepositoryNotFoundError` from the
        load, so an unknown id can never be answered as an empty history.
        """
        asset = self._repository.load_asset(asset_id)
        self._authorization.require(actor_id, Action.PROJECT_READ, asset.project_id)
        return AssetVersionHistory(
            asset_id=asset.id, versions=tuple(self._repository.list_versions(asset.id))
        )

    def create(self, asset: Asset, *, actor_id: str) -> Asset:
        self._authorization.require(actor_id, Action.PROJECT_EDIT, asset.project_id)
        return self._repository.create_asset(asset)

    def create_version(self, version: AssetVersion, *, actor_id: str) -> AssetVersion:
        asset = self._repository.load_asset(version.asset_id)
        self._authorization.require(actor_id, Action.PROJECT_EDIT, asset.project_id)
        return self._repository.create_version(version)

    def create_with_version(self, asset: Asset, version: AssetVersion, *, actor_id: str) -> tuple[Asset, AssetVersion]:
        if version.asset_id != asset.id:
            raise ValueError("asset and version identities do not match")
        self._authorization.require(actor_id, Action.PROJECT_EDIT, asset.project_id)
        return self._repository.create_asset_with_version(asset, version)

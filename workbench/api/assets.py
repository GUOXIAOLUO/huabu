"""Canonical Asset/AssetVersion read transport."""

from datetime import datetime
from typing import Any, Protocol

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel

from workbench.application.asset_query import (
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    AssetQuery,
    AssetQueryError,
)
from workbench.repositories.asset_repository import AssetRepositoryNotFoundError


class AssetResponse(BaseModel):
    id: str
    project_id: str
    source: str
    type: str
    status: str
    version_ids: list[str]
    metadata: dict[str, Any]


class AssetQueryPageResponse(BaseModel):
    """One page of matches plus the count the caller pages against.

    `total` is the unpaged match count, so a client can render "1-50 of 213"
    without issuing a second request.
    """

    items: list[AssetResponse]
    total: int
    limit: int
    offset: int
    has_more: bool


class AssetVersionResponse(BaseModel):
    id: str
    asset_id: str
    ordinal: int
    content: dict[str, Any]
    provenance: dict[str, Any]
    created_at: datetime
    metadata: dict[str, Any]


class AssetVersionHistoryResponse(BaseModel):
    """One asset's versions in sequence, plus the id of the current one.

    `current_version_id` is the end of the sequence as the *service* resolved
    it. A client could re-derive it from the ordinals, but then "current means
    the highest ordinal" would have a second owner, free to disagree with the
    history it was derived from.
    """

    asset_id: str
    current_version_id: str | None
    versions: list[AssetVersionResponse]


class _AssetServiceFactory(Protocol):
    def __call__(self, actor_id: str): ...


def _actor(value: str) -> str:
    actor = value.strip()
    if not actor or len(actor) > 255:
        raise HTTPException(status_code=401, detail="X-User-ID is required")
    return actor


def _asset_response(asset) -> AssetResponse:
    return AssetResponse(
        id=asset.id, project_id=asset.project_id, source=asset.source, type=asset.type,
        status=asset.status, version_ids=list(asset.version_ids), metadata=asset.metadata,
    )


def _version_response(version) -> AssetVersionResponse:
    """One projection for both version reads: the single version and the history.

    `get_asset_version` and `list_asset_versions` answer the same record at
    different widths, and two copies of this projection would drift the first
    time a version field was added.
    """
    return AssetVersionResponse(
        id=version.id, asset_id=version.asset_id, ordinal=version.ordinal,
        content=version.content.model_dump(), provenance=version.provenance.model_dump(),
        created_at=version.created_at, metadata=version.metadata,
    )


def create_canonical_assets_router(*, service_factory: _AssetServiceFactory) -> APIRouter:
    router = APIRouter(prefix="/api/v1/assets", tags=["assets"])

    @router.get("", response_model=list[AssetResponse])
    async def list_assets(
        project_id: str = Query(min_length=1, max_length=255),
        x_user_id: str = Header(default=""),
    ):
        try:
            actor_id = _actor(x_user_id)
            return [_asset_response(asset) for asset in service_factory(actor_id).list(
                project_id=project_id, actor_id=actor_id
            )]
        except PermissionError as error:
            raise HTTPException(status_code=403, detail=str(error)) from error

    @router.get("/query", response_model=AssetQueryPageResponse)
    async def query_assets(
        project_id: str = Query(min_length=1, max_length=255),
        q: str = Query(default="", max_length=200),
        asset_type: list[str] = Query(default=[], alias="type"),
        source: list[str] = Query(default=[]),
        status: list[str] = Query(default=[]),
        tag: list[str] = Query(default=[]),
        limit: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
        offset: int = Query(default=0, ge=0),
        x_user_id: str = Header(default=""),
    ):
        """Filter/search one project's assets by type, source, status, tag and text."""
        try:
            actor_id = _actor(x_user_id)
            page = service_factory(actor_id).query(
                AssetQuery(
                    project_id=project_id, text=q, types=tuple(asset_type),
                    sources=tuple(source), statuses=tuple(status), tags=tuple(tag),
                    limit=limit, offset=offset,
                ),
                actor_id=actor_id,
            )
        except AssetQueryError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
        except PermissionError as error:
            raise HTTPException(status_code=403, detail=str(error)) from error
        return AssetQueryPageResponse(
            items=[_asset_response(asset) for asset in page.items],
            total=page.total, limit=page.limit, offset=page.offset, has_more=page.has_more,
        )

    @router.get("/{asset_id}", response_model=AssetResponse)
    async def get_asset(asset_id: str, x_user_id: str = Header(default="")):
        try:
            return _asset_response(service_factory(_actor(x_user_id)).get(asset_id, actor_id=_actor(x_user_id)))
        except AssetRepositoryNotFoundError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error
        except PermissionError as error:
            raise HTTPException(status_code=403, detail=str(error)) from error

    # Both version routes address more than one path segment, so neither can be
    # swallowed by the single-segment `/{asset_id}` read declared above: the
    # ordering hazard that matters for `/query` is not load-bearing here.
    @router.get("/{asset_id}/versions", response_model=AssetVersionHistoryResponse)
    async def list_asset_versions(asset_id: str, x_user_id: str = Header(default="")):
        """One asset's version history, oldest first, with the current one named."""
        try:
            actor_id = _actor(x_user_id)
            history = service_factory(actor_id).history(asset_id, actor_id=actor_id)
        except AssetRepositoryNotFoundError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error
        except PermissionError as error:
            raise HTTPException(status_code=403, detail=str(error)) from error
        return AssetVersionHistoryResponse(
            asset_id=history.asset_id,
            current_version_id=history.current_version_id,
            versions=[_version_response(version) for version in history.versions],
        )

    @router.get("/{asset_id}/versions/{version_id}", response_model=AssetVersionResponse)
    async def get_asset_version(asset_id: str, version_id: str, x_user_id: str = Header(default="")):
        try:
            actor_id = _actor(x_user_id)
            version = service_factory(actor_id).get_version(asset_id, version_id, actor_id=actor_id)
        except AssetRepositoryNotFoundError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error
        except PermissionError as error:
            raise HTTPException(status_code=403, detail=str(error)) from error
        return _version_response(version)

    return router

"""Explicit migration from the legacy asset-library JSON store."""

from __future__ import annotations

import hashlib
import json
import mimetypes
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from workbench.domain.asset import Asset, AssetVersion, AssetVersionContent, AssetVersionProvenance
from workbench.repositories.asset_repository import (
    AssetRepositoryConflictError,
    SqliteAssetRepository,
)


@dataclass(frozen=True)
class AssetLibraryMigrationReport:
    imported_items: tuple[str, ...]
    skipped_items: tuple[str, ...]


class AssetLibraryMigrationService:
    def __init__(self, repository: SqliteAssetRepository, *, library_root: str | Path):
        self._repository = repository
        self._library_root = Path(library_root).resolve()

    def migrate(self, legacy_path: str | Path, *, project_id: str) -> AssetLibraryMigrationReport:
        payload = json.loads(Path(legacy_path).read_text(encoding="utf-8"))
        imported: list[str] = []
        skipped: list[str] = []
        libraries = payload.get("libraries", []) if isinstance(payload, dict) else []
        for library in libraries if isinstance(libraries, list) else []:
            categories = library.get("categories", []) if isinstance(library, dict) else []
            for category in categories if isinstance(categories, list) else []:
                items = category.get("items", []) if isinstance(category, dict) else []
                for item in items if isinstance(items, list) else []:
                    item_id = str(item.get("id") or "").strip() if isinstance(item, dict) else ""
                    if not item_id:
                        skipped.append(item_id)
                        continue
                    relative = self._safe_relative_path(item.get("url", ""))
                    source = self._library_root / relative if relative else None
                    if source is None or not source.is_file():
                        skipped.append(item_id)
                        continue
                    data = source.read_bytes()
                    asset = Asset(
                        id=item_id, project_id=project_id, source="import",
                        type=self._asset_type(item), metadata={"legacy": {"item": item}},
                    )
                    try:
                        self._repository.create_asset(asset)
                    except AssetRepositoryConflictError:
                        existing_asset = self._repository.load_asset(item_id)
                        if (
                            existing_asset.project_id != asset.project_id
                            or existing_asset.source != asset.source
                            or existing_asset.type != asset.type
                        ):
                            raise AssetRepositoryConflictError(
                                f"asset identity conflict during migration: {item_id}"
                            )
                        # Reruns remain safe: an identical identity is reused.
                        asset = self._repository.load_asset(item_id)
                    version = AssetVersion(
                        id=f"{item_id}-v1", asset_id=item_id, ordinal=1,
                        content=AssetVersionContent(
                            location=relative, checksum="sha256:" + hashlib.sha256(data).hexdigest(),
                            mime_type=mimetypes.guess_type(source.name)[0] or "application/octet-stream",
                            size_bytes=len(data),
                        ),
                        provenance=AssetVersionProvenance(source="import", source_ref=str(legacy_path)),
                        created_at=datetime.now(UTC), metadata={"legacy_item_id": item_id},
                    )
                    try:
                        self._repository.create_version(version)
                    except AssetRepositoryConflictError:
                        existing_version = self._repository.load_version(item_id, version.id)
                        if (
                            existing_version.asset_id != version.asset_id
                            or existing_version.ordinal != version.ordinal
                            or existing_version.content != version.content
                            or existing_version.provenance != version.provenance
                            or existing_version.metadata != version.metadata
                        ):
                            raise AssetRepositoryConflictError(
                                f"asset version conflict during migration: {version.id}"
                            )
                    imported.append(item_id)
        return AssetLibraryMigrationReport(tuple(imported), tuple(skipped))

    def _safe_relative_path(self, url: object) -> str | None:
        raw = str(url or "").split("?", 1)[0]
        prefix = "/assets/library/"
        if not raw.startswith(prefix):
            return None
        candidate = (self._library_root / raw[len(prefix):]).resolve()
        try:
            return candidate.relative_to(self._library_root).as_posix()
        except ValueError:
            return None

    @staticmethod
    def _asset_type(item: dict) -> str:
        kind = str(item.get("kind") or item.get("type") or "other").lower()
        return kind if kind in {"image", "video", "audio", "document", "model", "workflow", "other"} else "other"

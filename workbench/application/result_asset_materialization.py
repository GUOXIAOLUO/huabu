"""Explicit conversion of one selected execution result into a reusable Asset."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Callable

from workbench.domain.asset import Asset, AssetType, AssetVersion, AssetVersionContent, AssetVersionProvenance


class ResultAssetMaterializationError(ValueError):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)


class ResultAssetMaterializationService:
    def __init__(self, assets, selections, runs, attempts, *, actor_id: str,
                 id_factory: Callable[[], str] | None = None,
                 clock: Callable[[], datetime] | None = None):
        self._assets, self._selections, self._runs, self._attempts = assets, selections, runs, attempts
        self._actor_id = actor_id
        self._id_factory = id_factory or (lambda: uuid.uuid4().hex)
        self._clock = clock or (lambda: datetime.now(UTC))

    def materialize(self, *, project_id: str, run_id: str, attempt_id: str,
                    output_name: str, ordinal: int, title: str, type: AssetType,
                    content: AssetVersionContent, metadata: dict | None = None) -> tuple[Asset, AssetVersion]:
        if not all(str(value or '').strip() for value in (project_id, run_id, attempt_id, output_name, title)):
            raise ResultAssetMaterializationError('invalid_request', 'project, result address, and title are required')
        if not isinstance(ordinal, int) or isinstance(ordinal, bool) or ordinal < 0:
            raise ResultAssetMaterializationError('invalid_request', 'ordinal must be a non-negative integer')
        try:
            run = self._runs.get(run_id)
            attempt = self._attempts.get(attempt_id)
            selections = self._selections.list_for_run(run_id)
        except Exception as error:
            if getattr(error, 'code', '') == 'not_found':
                raise ResultAssetMaterializationError('not_found', str(error)) from error
            raise
        if run.project_id != project_id or attempt.run_id != run_id:
            raise ResultAssetMaterializationError('cross_project', 'result does not belong to the target project/run')
        selected = next((item for item in selections if item.attempt_id == attempt_id and item.output_name == output_name and item.ordinal == ordinal and item.selected), None)
        if selected is None:
            raise ResultAssetMaterializationError('result_not_selected', f'result is not selected: {output_name}#{ordinal}')
        asset_metadata = dict(metadata or {})
        asset_metadata.setdefault('title', title)
        asset = Asset(id=self._id_factory(), project_id=project_id, source='execution', type=type, metadata=asset_metadata)
        version = AssetVersion(
            id=self._id_factory(), asset_id=asset.id, ordinal=1, content=content,
            provenance=AssetVersionProvenance(source='execution', source_ref=f'{run_id}/{attempt_id}/{output_name}#{ordinal}', actor_id=self._actor_id),
            created_at=self._clock(), metadata={'result': {'run_id': run_id, 'attempt_id': attempt_id, 'output_name': output_name, 'ordinal': ordinal}},
        )
        created_asset, created_version = self._assets.create_with_version(asset, version, actor_id=self._actor_id)
        return self._assets.get(created_asset.id, actor_id=self._actor_id), created_version

"""Explicit promotion of one selected execution result into an ArtifactVersion."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Callable

from workbench.domain.artifact import (
    Artifact,
    ArtifactType,
    ArtifactVersion,
    ArtifactVersionContentRef,
    ArtifactVersionLineage,
)


class ResultArtifactMaterializationError(ValueError):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)


class ResultArtifactMaterializationService:
    def __init__(self, artifacts, selections, runs, attempts, *, actor_id: str,
                 id_factory: Callable[[], str] | None = None,
                 clock: Callable[[], datetime] | None = None):
        self._artifacts, self._selections = artifacts, selections
        self._runs, self._attempts = runs, attempts
        self._actor_id = actor_id
        self._id_factory = id_factory or (lambda: uuid.uuid4().hex)
        self._clock = clock or (lambda: datetime.now(UTC))

    def materialize(self, *, project_id: str, run_id: str, attempt_id: str,
                    output_name: str, ordinal: int, title: str, type: ArtifactType,
                    content_ref: ArtifactVersionContentRef,
                    input_refs: tuple[str, ...] = (),
                    prompt_version_ref: str | None = None,
                    model_ref: str | None = None,
                    skill_version_ref: str | None = None,
                    metadata: dict | None = None) -> tuple[Artifact, ArtifactVersion]:
        values = (project_id, run_id, attempt_id, output_name, title)
        if not all(str(value or '').strip() for value in values):
            raise ResultArtifactMaterializationError('invalid_request', 'project, result address, and title are required')
        if not isinstance(ordinal, int) or isinstance(ordinal, bool) or ordinal < 0:
            raise ResultArtifactMaterializationError('invalid_request', 'ordinal must be a non-negative integer')
        try:
            run = self._runs.get(run_id)
            attempt = self._attempts.get(attempt_id)
            selections = self._selections.list_for_run(run_id)
        except Exception as error:
            if getattr(error, 'code', '') == 'not_found':
                raise ResultArtifactMaterializationError('not_found', str(error)) from error
            raise
        if run.project_id != project_id or attempt.run_id != run_id:
            raise ResultArtifactMaterializationError('cross_project', 'result does not belong to the target project/run')
        selected = next((item for item in selections if item.attempt_id == attempt_id
                         and item.output_name == output_name and item.ordinal == ordinal
                         and item.selected), None)
        if selected is None:
            raise ResultArtifactMaterializationError('result_not_selected', f'result is not selected: {output_name}#{ordinal}')
        result_metadata = dict(metadata or {})
        result_metadata.setdefault('result', {
            'task_id': run.task_id, 'run_id': run_id, 'attempt_id': attempt_id,
            'output_name': output_name, 'ordinal': ordinal,
        })
        lineage = ArtifactVersionLineage(
            task_id=run.task_id, run_id=run_id, attempt_id=attempt_id,
            input_refs=tuple(input_refs),
            prompt_version_ref=prompt_version_ref, model_ref=model_ref,
            skill_version_ref=skill_version_ref,
        )
        return self._artifacts.create_with_version(
            project_id=project_id, type=type, title=title,
            content_ref=content_ref, lineage=lineage,
            metadata=result_metadata, version_metadata={'result': result_metadata['result']},
        )

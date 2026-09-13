"""Freeze resolved Task inputs into a reproducible, non-executable snapshot."""

from __future__ import annotations

from copy import deepcopy
from collections.abc import Callable, Iterable, Mapping
from typing import Any

from workbench.application.binding_resolver import BindingResolutionError, BindingResolver
from workbench.domain.canvas.input_bindings import InputBinding
from workbench.domain.collection import Collection
from workbench.domain.execution.input_projection import (
    EXECUTION_INPUT_PROJECTION_SCHEMA_VERSION,
    ExecutionInputProjection,
    ProjectedExecutionInput,
    ProjectionError,
)
from workbench.domain.canvas.models import DefinitionRef
from workbench.domain.prompt import PromptRef


SourceResolver = Callable[[str], Any | None]


class ExecutionInputProjectionService:
    """Resolve and freeze inputs without invoking an Executor."""

    def __init__(self, source_resolvers: Mapping[str, SourceResolver] | None = None):
        self._source_resolvers = dict(source_resolvers or {})

    def project(
        self,
        bindings: Iterable[InputBinding],
        *,
        parameters: Mapping[str, Any] | None = None,
        skill_ref: DefinitionRef | None = None,
        prompt_ref: PromptRef | None = None,
        model_availability_ref: str | None = None,
        execution_profile_ref: str | None = None,
    ) -> ExecutionInputProjection:
        """Return a complete snapshot or explicit pre-execution errors."""

        try:
            resolved = BindingResolver(self._source_resolvers).resolve(bindings)
        except BindingResolutionError as error:
            return self._invalid(
                parameters=parameters,
                skill_ref=skill_ref,
                prompt_ref=prompt_ref,
                model_availability_ref=model_availability_ref,
                execution_profile_ref=execution_profile_ref,
                error=ProjectionError(code=error.code, message=str(error), binding_id=error.binding_id),
            )

        errors: list[ProjectionError] = []
        inputs: list[ProjectedExecutionInput] = []
        for item in resolved:
            if item.status == "disabled":
                errors.append(ProjectionError(code="binding_disabled", message="input binding is disabled", binding_id=item.binding_id))
                continue
            if item.status != "resolved":
                errors.append(ProjectionError(code=item.reason or "input_unresolved", message=f"input binding is {item.reason or item.status}", binding_id=item.binding_id))
                continue
            if item.source_type == "collection":
                self._append_collection_rows(inputs, errors, item)
                continue
            snapshot = deepcopy(item.value)
            inputs.append(ProjectedExecutionInput(
                input_id=item.binding_id,
                binding_id=item.binding_id,
                target=item.target,
                role=item.role,
                order=item.order,
                source_type=item.source_type,
                source_ref=item.source_ref,
                value=deepcopy(snapshot),
                source_snapshot=snapshot,
            ))

        if errors:
            return self._invalid(
                parameters=parameters,
                skill_ref=skill_ref,
                prompt_ref=prompt_ref,
                model_availability_ref=model_availability_ref,
                execution_profile_ref=execution_profile_ref,
                errors=errors,
            )
        return ExecutionInputProjection(
            inputs=tuple(inputs),
            parameters=deepcopy(dict(parameters or {})),
            skill_ref=skill_ref,
            prompt_ref=prompt_ref,
            model_availability_ref=model_availability_ref,
            execution_profile_ref=execution_profile_ref,
        )

    @staticmethod
    def _append_collection_rows(inputs: list[ProjectedExecutionInput], errors: list[ProjectionError], item: Any) -> None:
        if not isinstance(item.value, Collection):
            errors.append(ProjectionError(code="collection_invalid", message="collection binding did not resolve to a Collection", binding_id=item.binding_id))
            return
        collection = item.value
        collection_snapshot = collection.model_dump(mode="json")
        for row in sorted(collection.items, key=lambda row: (row.order, row.id)):
            row_snapshot = {
                "collection_id": collection.id,
                "collection_revision": collection.revision,
                "collection_schema_version": collection_snapshot["schema_version"],
                "row_id": row.id,
                "row_order": row.order,
                "values": row.model_dump(mode="json"),
            }
            inputs.append(ProjectedExecutionInput(
                input_id=f"{item.binding_id}:{row.id}",
                binding_id=item.binding_id,
                target=item.target,
                role=item.role,
                order=item.order,
                source_type=item.source_type,
                source_ref=item.source_ref,
                value=deepcopy(row_snapshot),
                source_snapshot=deepcopy(row_snapshot),
            ))

    @staticmethod
    def _invalid(*, parameters: Mapping[str, Any] | None, skill_ref: DefinitionRef | None, prompt_ref: PromptRef | None, model_availability_ref: str | None, execution_profile_ref: str | None, error: ProjectionError | None = None, errors: Iterable[ProjectionError] = ()) -> ExecutionInputProjection:
        all_errors = tuple(errors) + ((error,) if error is not None else ())
        return ExecutionInputProjection(
            parameters=deepcopy(dict(parameters or {})),
            skill_ref=skill_ref,
            prompt_ref=prompt_ref,
            model_availability_ref=model_availability_ref,
            execution_profile_ref=execution_profile_ref,
            errors=all_errors,
        )

"""Application boundary for putting produced results into a Collection.

A result reaches a Collection directly: this reads what the user selected and
materialises it as typed Collection items. No Canvas node is created, and no
result is converted into an Asset or an Artifact — the item names the result it
came from, which is all the lineage this card is allowed to keep.
"""

from __future__ import annotations

import uuid
from typing import Callable

from workbench.application.collection_service import CollectionNotFoundServiceError, CollectionService, CollectionServiceError
from workbench.application.execution_run_service import ExecutionRunService, ExecutionRunServiceError
from workbench.application.result_selection_service import ResultSelectionService, ResultSelectionServiceError
from workbench.domain.collection import Collection, CollectionColumn, CollectionExecutionResultCell, CollectionItem, CollectionSchema


class ResultCollectionServiceError(ValueError):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)


class ResultCollectionNotFoundServiceError(ResultCollectionServiceError):
    def __init__(self, target: str):
        super().__init__("not_found", f"result collection target not found: {target}")


class ResultCollectionService:
    def __init__(self, collection_service: CollectionService, selection_service: ResultSelectionService, run_service: ExecutionRunService, *, actor_id: str, id_factory: Callable[[], str] | None = None):
        self._collections = collection_service
        self._selections = selection_service
        self._runs = run_service
        self._actor_id = actor_id
        self._id_factory = id_factory or (lambda: uuid.uuid4().hex)

    def add_selected(self, *, collection_id: str, run_id: str, expected_revision: int, column_key: str = "result") -> Collection:
        """Append one item per selected result of a run to a Collection."""
        collection = self._read_collection(collection_id)
        # The run has to exist and to belong to the same project: an item whose
        # lineage points into another project would not be readable by the
        # people who can read the Collection.
        try:
            run = self._runs.get(run_id)
        except ExecutionRunServiceError as error:
            if error.code == "not_found":
                raise ResultCollectionNotFoundServiceError(run_id) from error
            raise ResultCollectionServiceError(error.code, str(error)) from error
        if run.project_id != collection.project_id:
            raise ResultCollectionServiceError("cross_project", "a result may not be collected into another project")

        try:
            selections = self._selections.list_for_run(run_id)
        except ResultSelectionServiceError as error:
            if error.code == "not_found":
                raise ResultCollectionNotFoundServiceError(run_id) from error
            raise ResultCollectionServiceError(error.code, str(error)) from error
        chosen = [selection for selection in selections if selection.selected]
        if not chosen:
            raise ResultCollectionServiceError("nothing_selected", f"run has no selected results: {run_id}")

        schema = self._ensure_column(collection.collection_schema, column_key)
        order = max((item.order for item in collection.items), default=-1) + 1
        items = list(collection.items) + [
            CollectionItem(
                id=self._id_factory(),
                order=order + offset,
                values={column_key: CollectionExecutionResultCell(
                    run_id=selection.run_id, attempt_id=selection.attempt_id,
                    output_name=selection.output_name, ordinal=selection.ordinal,
                )},
            )
            for offset, selection in enumerate(chosen)
        ]
        self._validate(collection, schema, items)
        try:
            return self._collections.update(collection_id, expected_revision=expected_revision, schema=schema, items=items)
        except CollectionNotFoundServiceError as error:
            raise ResultCollectionNotFoundServiceError(collection_id) from error
        except CollectionServiceError as error:
            raise ResultCollectionServiceError(error.code, str(error)) from error

    def _read_collection(self, collection_id: str) -> Collection:
        try:
            return self._collections.get(collection_id)
        except CollectionNotFoundServiceError as error:
            raise ResultCollectionNotFoundServiceError(collection_id) from error
        except CollectionServiceError as error:
            raise ResultCollectionServiceError(error.code, str(error)) from error

    @staticmethod
    def _validate(collection: Collection, schema: CollectionSchema, items: list[CollectionItem]) -> None:
        """`CollectionService.update` copies the aggregate without re-running
        validators, so the result is validated here before it is handed over —
        and reported as a service error rather than escaping as a raw pydantic
        exception the API would answer with a 500."""
        try:
            Collection(
                id=collection.id, project_id=collection.project_id, name=collection.name,
                schema=schema, items=items, default_view=collection.default_view,
                revision=collection.revision, metadata=collection.metadata,
            )
        except ValueError as error:
            raise ResultCollectionServiceError("invalid_collection", str(error)) from error

    @staticmethod
    def _ensure_column(schema: CollectionSchema, column_key: str) -> CollectionSchema:
        """Make sure the schema can hold execution results under this key.

        Materialising is the point of the card, so a missing column is created
        rather than demanded up front — but an existing column is never
        retyped, because that would silently reinterpret the rows already in it.
        """
        existing = next((column for column in schema.columns if column.key == column_key), None)
        if existing is not None:
            if existing.value_type != "execution_result":
                raise ResultCollectionServiceError(
                    "column_type_mismatch",
                    f"column {column_key} holds {existing.value_type}, not execution results",
                )
            return schema
        if any(column.id == column_key for column in schema.columns):
            raise ResultCollectionServiceError("column_conflict", f"column id is already taken: {column_key}")
        return schema.model_copy(update={"columns": list(schema.columns) + [
            CollectionColumn(id=column_key, key=column_key, label=column_key, value_type="execution_result"),
        ]})

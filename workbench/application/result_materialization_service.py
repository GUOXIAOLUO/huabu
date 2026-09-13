"""Application boundary for putting a produced result onto a Canvas as a node.

Nothing here runs on its own. A node appears only because a caller named one
result and asked for it, and the card's whole point is that no output is ever
turned into a node by running something.

Two boundaries are deliberate. The result must already be *selected*: selection
(R8-19) is where a user says which results matter, and materializing is not
allowed to invent a second opinion about that. And the node keeps its lineage on
itself — the four-part address in ``config`` and the producing run in
``provenance_ref`` — rather than in a second table, so there is exactly one
place that knows where the node came from.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Callable

from workbench.application.execution_run_service import ExecutionRunService, ExecutionRunServiceError
from workbench.application.node_creation import (
    NodeCreateCommand,
    NodeCreationError,
    NodeCreationPersistence,
    NodeCreationService,
    NodeCreationSource,
)
from workbench.application.result_node_definitions import ResultNodeDefinitionRegistry
from workbench.application.result_selection_service import ResultSelectionService, ResultSelectionServiceError
from workbench.domain.canvas.models import Position
from workbench.domain.execution import ExecutionResultIdentity


RESULT_MATERIALIZATION_CONFIG_KEY = "result"


class ResultMaterializationServiceError(ValueError):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)


class ResultMaterializationNotFoundServiceError(ResultMaterializationServiceError):
    def __init__(self, target: str):
        super().__init__("not_found", f"result materialization target not found: {target}")


class ResultMaterializationService:
    def __init__(
        self,
        node_creation: NodeCreationService,
        selections: ResultSelectionService,
        runs: ExecutionRunService,
        *,
        actor_id: str,
        id_factory: Callable[[], str] | None = None,
        clock: Callable[[], datetime] | None = None,
    ):
        self._node_creation = node_creation
        self._selections = selections
        self._runs = runs
        self._actor_id = actor_id
        self._id_factory = id_factory or (lambda: uuid.uuid4().hex)
        self._clock = clock or (lambda: datetime.now(UTC))

    def materialize(
        self,
        *,
        request_id: str,
        project_id: str,
        canvas_id: str,
        run_id: str,
        attempt_id: str,
        output_name: str,
        ordinal: int,
        position: Position,
        expected_revision: int | None = None,
        title: str | None = None,
    ) -> NodeCreationPersistence:
        """Create one Canvas node for one named, already-selected result."""
        self._validate(request_id, project_id, canvas_id, run_id, attempt_id, output_name, ordinal, expected_revision)

        try:
            run = self._runs.get(run_id)
        except ExecutionRunServiceError as error:
            if error.code == "not_found":
                raise ResultMaterializationNotFoundServiceError(run_id) from error
            raise ResultMaterializationServiceError(error.code, str(error)) from error
        # A node whose provenance points into another project would be a node its
        # readers cannot follow.
        if run.project_id != project_id:
            raise ResultMaterializationServiceError("cross_project", "a result may not be materialized into another project")

        identity = self._require_selected(run_id, attempt_id, output_name, ordinal)
        try:
            return self._node_creation.create(NodeCreateCommand(
                request_id=request_id,
                actor_id=self._actor_id,
                project_id=project_id,
                canvas_id=canvas_id,
                source=NodeCreationSource.RESULT_MATERIALIZATION,
                definition_ref=ResultNodeDefinitionRegistry.EXECUTION_RESULT,
                position=position,
                expected_revision=expected_revision,
                title=title or identity.label(),
                initial_config={RESULT_MATERIALIZATION_CONFIG_KEY: identity.model_dump(mode="json")},
                provenance_ref=run_id,
            ))
        except NodeCreationError as error:
            raise ResultMaterializationServiceError(error.code, str(error)) from error

    def _require_selected(self, run_id: str, attempt_id: str, output_name: str, ordinal: int) -> ExecutionResultIdentity:
        """Return the address of the result, but only if the user selected it."""
        try:
            selections = self._selections.list_for_run(run_id)
        except ResultSelectionServiceError as error:
            if error.code == "not_found":
                raise ResultMaterializationNotFoundServiceError(run_id) from error
            raise ResultMaterializationServiceError(error.code, str(error)) from error
        matches = [
            selection for selection in selections
            if selection.attempt_id == attempt_id and selection.output_name == output_name and selection.ordinal == ordinal
        ]
        if not matches:
            raise ResultMaterializationNotFoundServiceError(f"{attempt_id}/{output_name}#{ordinal}")
        chosen = next((selection for selection in matches if selection.selected), None)
        if chosen is None:
            raise ResultMaterializationServiceError("result_not_selected", f"result is not selected: {output_name}#{ordinal}")
        return ExecutionResultIdentity(
            run_id=chosen.run_id, attempt_id=chosen.attempt_id,
            output_name=chosen.output_name, ordinal=chosen.ordinal,
        )

    @staticmethod
    def _validate(request_id, project_id, canvas_id, run_id, attempt_id, output_name, ordinal, expected_revision) -> None:
        for name, value in (
            ("request_id", request_id), ("project_id", project_id), ("canvas_id", canvas_id),
            ("run_id", run_id), ("attempt_id", attempt_id), ("output_name", output_name),
        ):
            if not str(value or "").strip():
                raise ResultMaterializationServiceError("invalid_request", f"{name} is required")
        if not isinstance(ordinal, int) or isinstance(ordinal, bool) or ordinal < 0:
            raise ResultMaterializationServiceError("invalid_request", "ordinal must be a non-negative integer")
        if expected_revision is not None and expected_revision < 1:
            raise ResultMaterializationServiceError("invalid_request", "expected_revision must be positive when supplied")

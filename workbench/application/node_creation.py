"""Industry-neutral, UI-free node creation application service."""

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Callable, Protocol

from workbench.domain.asset import AssetVersionRef
from workbench.domain.canvas.models import ArtifactOrAssetVersionRef, DefinitionRef, ModelBinding, NodeRecord, Position, RendererRef, Size
from workbench.domain.canvas.input_bindings import InputBindingAdapter, InputBindingValue
from workbench.domain.canvas.port_type_registry import PortTypeRegistry, create_core_port_type_registry
from workbench.domain.canvas.ports import PortSet
from workbench.domain.canvas.states import NodeState


class NodeCreationSource(StrEnum):
    CONTEXT_MENU = "context_menu"
    COMMAND_PALETTE = "command_palette"
    SKILL_LIBRARY_DRAG = "skill_library_drag"
    FILE_DROP = "file_drop"
    CLIPBOARD = "clipboard"
    QUICK_COLLECTION = "quick_collection"
    WORKFLOW_IMPORT = "workflow_import"
    AGENT_PROPOSAL = "agent_proposal"
    RESULT_MATERIALIZATION = "result_materialization"
    ASSET_REFERENCE_DRAG = "asset_reference_drag"
    LEGACY = "legacy"


class NodeCreationError(ValueError):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)


@dataclass(frozen=True)
class NodeCreateCommand:
    request_id: str
    actor_id: str
    project_id: str
    canvas_id: str
    source: NodeCreationSource
    definition_ref: DefinitionRef
    position: Position
    expected_revision: int | None = None
    title: str | None = None
    initial_bindings: tuple[InputBindingValue | dict[str, Any], ...] = ()
    initial_output_refs: tuple[ArtifactOrAssetVersionRef | dict[str, Any], ...] = ()
    initial_config: dict[str, Any] | None = None
    requested_model_binding: ModelBinding | None = None
    approval_id: str | None = None
    provenance_ref: str | None = None


@dataclass(frozen=True)
class ResolvedNodeDefinition:
    definition_ref: DefinitionRef
    kind: str
    renderer: RendererRef
    title: str
    ports: PortSet
    default_size: Size
    initial_state: NodeState = NodeState.READY
    enabled: bool = True
    requires_model: bool = False


@dataclass(frozen=True)
class NodeCreationPersistence:
    node: NodeRecord
    canvas_revision: int
    created: bool


@dataclass(frozen=True)
class NodeCreatedAuditEvent:
    request_id: str
    actor_id: str
    project_id: str
    canvas_id: str
    node_id: str
    definition_ref: DefinitionRef
    source: NodeCreationSource
    occurred_at: datetime


class ProjectAuthorizer(Protocol):
    def can_edit(self, actor_id: str, project_id: str, canvas_id: str) -> bool: ...


class NodeDefinitionRegistry(Protocol):
    def resolve(self, definition_ref: DefinitionRef) -> ResolvedNodeDefinition | None: ...


class ModelCompatibilityPolicy(Protocol):
    def is_compatible(self, definition: ResolvedNodeDefinition, binding: ModelBinding) -> bool: ...


class AtomicNodeCreationRepository(Protocol):
    def create_node(self, node: NodeRecord, *, expected_revision: int | None, request_id: str) -> NodeCreationPersistence: ...


class AuditSink(Protocol):
    def append(self, event: NodeCreatedAuditEvent) -> None: ...


class AssetVersionReferenceValidator(Protocol):
    def validate(self, *, actor_id: str, project_id: str, reference: AssetVersionRef) -> None: ...


class ArtifactVersionReferenceValidator(Protocol):
    def validate(self, *, actor_id: str, project_id: str, reference: dict[str, Any]) -> None: ...


class NodeCreationService:
    """Single creation pipeline for migrated entry paths.

    This service deliberately knows no Legacy node shape, provider SDK, HTTP route,
    DOM element, or Industry Pack identifier. Those concerns live behind interfaces.
    """

    def __init__(
        self,
        *,
        authorizer: ProjectAuthorizer,
        definitions: NodeDefinitionRegistry,
        model_policy: ModelCompatibilityPolicy,
        repository: AtomicNodeCreationRepository,
        audit_sink: AuditSink,
        node_id_factory: Callable[[], str],
        port_types: PortTypeRegistry | None = None,
        asset_reference_validator: AssetVersionReferenceValidator | None = None,
        artifact_version_reference_validator: ArtifactVersionReferenceValidator | None = None,
        clock: Callable[[], datetime] | None = None,
    ):
        self._authorizer = authorizer
        self._definitions = definitions
        self._model_policy = model_policy
        self._repository = repository
        self._audit_sink = audit_sink
        self._node_id_factory = node_id_factory
        self._port_types = port_types or create_core_port_type_registry()
        self._asset_reference_validator = asset_reference_validator
        self._artifact_version_reference_validator = artifact_version_reference_validator
        self._clock = clock or (lambda: datetime.now(UTC))

    def create(self, command: NodeCreateCommand) -> NodeCreationPersistence:
        node, definition, timestamp = self.prepare(command)
        persisted = self._repository.create_node(node, expected_revision=command.expected_revision, request_id=command.request_id)
        if persisted.created:
            self._audit_sink.append(NodeCreatedAuditEvent(
                request_id=command.request_id, actor_id=command.actor_id, project_id=command.project_id,
                canvas_id=command.canvas_id, node_id=persisted.node.id, definition_ref=definition.definition_ref,
                source=command.source, occurred_at=timestamp,
            ))
        return persisted

    def prepare(self, command: NodeCreateCommand) -> tuple[NodeRecord, ResolvedNodeDefinition, datetime]:
        """Validate and construct a node without persistence or audit side effects."""
        self._validate_command(command)
        if not self._authorizer.can_edit(command.actor_id, command.project_id, command.canvas_id):
            raise NodeCreationError("forbidden", "actor is not permitted to edit this Canvas")

        definition = self._definitions.resolve(command.definition_ref)
        if definition is None:
            raise NodeCreationError("definition_not_found", "node definition is unavailable")
        if not definition.enabled:
            raise NodeCreationError("definition_disabled", "node definition is disabled")
        if definition.definition_ref != command.definition_ref:
            raise NodeCreationError("definition_mismatch", "resolved definition does not match the requested version")
        try:
            self._port_types.resolve_port_set(definition.ports)
        except (LookupError, TypeError, ValueError) as error:
            raise NodeCreationError("invalid_port_types", "node definition contains unknown port types") from error

        binding = command.requested_model_binding
        if definition.requires_model and binding is None:
            raise NodeCreationError("model_required", "this definition requires an explicit compatible model")
        if binding is not None and not self._model_policy.is_compatible(definition, binding):
            raise NodeCreationError("model_incompatible", "the selected model is not compatible with this definition")

        if command.source is NodeCreationSource.ASSET_REFERENCE_DRAG:
            try:
                reference = AssetVersionRef.model_validate((command.initial_config or {}).get("asset_version_ref"))
            except ValueError as error:
                raise NodeCreationError("invalid_asset_reference", "a valid AssetVersionRef is required") from error
            if self._asset_reference_validator is None:
                raise NodeCreationError("asset_reference_unavailable", "asset reference validation is not configured")
            try:
                self._asset_reference_validator.validate(
                    actor_id=command.actor_id, project_id=command.project_id, reference=reference
                )
            except PermissionError as error:
                raise NodeCreationError("forbidden", "actor cannot reference this asset version") from error
            except LookupError as error:
                raise NodeCreationError("asset_reference_not_found", "asset version reference is unavailable") from error

        artifact_reference = (command.initial_config or {}).get("artifact_version_ref")
        if artifact_reference is not None:
            if self._artifact_version_reference_validator is None:
                raise NodeCreationError("artifact_reference_unavailable", "artifact version validation is not configured")
            try:
                self._artifact_version_reference_validator.validate(
                    actor_id=command.actor_id, project_id=command.project_id, reference=artifact_reference
                )
            except PermissionError as error:
                raise NodeCreationError("forbidden", "actor cannot reference this artifact version") from error
            except (LookupError, ValueError, TypeError) as error:
                raise NodeCreationError("artifact_reference_not_found", "artifact version reference is unavailable") from error

        timestamp = self._clock()
        node = NodeRecord(
            id=self._node_id_factory(),
            project_id=command.project_id,
            canvas_id=command.canvas_id,
            kind=definition.kind,
            definition_ref=definition.definition_ref,
            renderer=definition.renderer,
            state=definition.initial_state,
            title=command.title or definition.title,
            position=command.position,
            size=definition.default_size,
            ports=definition.ports,
            input_bindings=InputBindingAdapter.from_payloads(command.initial_bindings),
            output_refs=[ArtifactOrAssetVersionRef.model_validate(ref) for ref in command.initial_output_refs],
            model_binding=binding,
            config=dict(command.initial_config or {}),
            provenance_ref=command.provenance_ref,
            created_by=command.actor_id,
            created_at=timestamp,
            updated_at=timestamp,
            metadata={
                "creation": {
                    "request_id": command.request_id,
                    "source": command.source.value,
                    "approval_id": command.approval_id,
                }
            },
        )
        return node, definition, timestamp

    @staticmethod
    def _validate_command(command: NodeCreateCommand) -> None:
        for name in ("request_id", "actor_id", "project_id", "canvas_id"):
            if not str(getattr(command, name) or "").strip():
                raise NodeCreationError("invalid_request", f"{name} is required")
        if command.expected_revision is not None and command.expected_revision < 1:
            raise NodeCreationError("invalid_request", "expected_revision must be positive when supplied")

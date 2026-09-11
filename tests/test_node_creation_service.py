import unittest
from datetime import UTC, datetime

from workbench.application.node_creation import (
    NodeCreateCommand,
    NodeCreatedAuditEvent,
    NodeCreationError,
    NodeCreationPersistence,
    NodeCreationService,
    NodeCreationSource,
    ResolvedNodeDefinition,
)
from workbench.domain.canvas.models import DefinitionRef, ModelBinding, Position, RendererRef, Size
from workbench.domain.canvas.ports import InputPort, OutputPort, PortSet
from workbench.domain.canvas.port_type_registry import PortTypeDefinition, PortTypeRegistry
from workbench.domain.canvas.states import NodeState
from workbench.repositories.canvas_repository import StaleCanvasRevisionError


DEFINITION_REF = DefinitionRef(type="skill", id="common.example", version="1.0.0")
DEFINITION = ResolvedNodeDefinition(
    definition_ref=DEFINITION_REF,
    kind="skill",
    renderer=RendererRef(id="form", version="1"),
    title="Example",
    ports=PortSet(inputs=[InputPort(id="source", accepts=["asset.image"])], outputs=[OutputPort(id="result", produces=["artifact.example"])]),
    default_size=Size(width=320, height=220),
    initial_state=NodeState.READY,
    requires_model=True,
)


class AllowAuthorizer:
    def __init__(self, allowed=True):
        self.allowed = allowed

    def can_edit(self, actor_id, project_id, canvas_id):
        return self.allowed


class DefinitionRegistry:
    def __init__(self, definition=DEFINITION):
        self.definition = definition

    def resolve(self, definition_ref):
        return self.definition


class CompatibilityPolicy:
    def __init__(self, compatible=True):
        self.compatible = compatible
        self.seen = []

    def is_compatible(self, definition, binding):
        self.seen.append(binding)
        return self.compatible


class AtomicRepository:
    def __init__(self, revision=1):
        self.revision = revision
        self.by_request = {}
        self.nodes = []

    def create_node(self, node, *, expected_revision, request_id):
        if request_id in self.by_request:
            existing = self.by_request[request_id]
            return NodeCreationPersistence(
                node=existing.node,
                canvas_revision=existing.canvas_revision,
                created=False,
            )
        if expected_revision is not None and expected_revision != self.revision:
            raise StaleCanvasRevisionError({"id": node.canvas_id, "updated_at": self.revision})
        self.nodes.append(node)
        self.revision += 1
        result = NodeCreationPersistence(node=node, canvas_revision=self.revision, created=True)
        self.by_request[request_id] = result
        return result


class AuditEvents:
    def __init__(self):
        self.events: list[NodeCreatedAuditEvent] = []

    def append(self, event):
        self.events.append(event)


class NodeCreationServiceTests(unittest.TestCase):
    def setUp(self):
        self.authorizer = AllowAuthorizer()
        self.registry = DefinitionRegistry()
        self.compatibility = CompatibilityPolicy()
        self.repository = AtomicRepository()
        self.audit = AuditEvents()
        self.port_types = PortTypeRegistry([
            PortTypeDefinition("asset.image", "Image asset"),
            PortTypeDefinition("artifact.example", "Example artifact"),
            PortTypeDefinition("legacy.any", "Legacy compatible value"),
        ])
        self.service = NodeCreationService(
            authorizer=self.authorizer,
            definitions=self.registry,
            model_policy=self.compatibility,
            repository=self.repository,
            audit_sink=self.audit,
            node_id_factory=lambda: "node-created-1",
            port_types=self.port_types,
            clock=lambda: datetime(2026, 9, 2, tzinfo=UTC),
        )

    def command(self, **overrides):
        values = {
            "request_id": "request-1",
            "actor_id": "user-1",
            "project_id": "project-1",
            "canvas_id": "canvas-1",
            "source": NodeCreationSource.CONTEXT_MENU,
            "definition_ref": DEFINITION_REF,
            "position": Position(x=12, y=24),
            "expected_revision": 1,
            "requested_model_binding": ModelBinding(selection_mode="user", provider_id="provider-1", model_id="model-1"),
        }
        values.update(overrides)
        return NodeCreateCommand(**values)

    def test_creates_valid_node_and_audits_once(self):
        result = self.service.create(self.command())
        self.assertTrue(result.created)
        self.assertEqual(result.node.kind, "skill")
        self.assertEqual(result.node.ports.outputs[0].id, "result")
        self.assertEqual(result.node.metadata["creation"]["source"], "context_menu")
        self.assertEqual(len(self.audit.events), 1)

    def test_prepare_has_no_persistence_or_audit_side_effect(self):
        node, definition, _ = self.service.prepare(self.command())
        self.assertEqual(node.definition_ref, definition.definition_ref)
        self.assertEqual(self.repository.nodes, [])
        self.assertEqual(self.audit.events, [])

    def test_duplicate_request_is_idempotent(self):
        first = self.service.create(self.command())
        second = self.service.create(self.command())
        self.assertEqual(first.node.id, second.node.id)
        self.assertEqual(len(self.repository.nodes), 1)
        self.assertEqual(len(self.audit.events), 1)

    def test_disabled_or_missing_definition_fails_safely(self):
        self.registry.definition = None
        with self.assertRaisesRegex(NodeCreationError, "unavailable"):
            self.service.create(self.command())

        self.registry.definition = ResolvedNodeDefinition(**{**DEFINITION.__dict__, "enabled": False})
        with self.assertRaisesRegex(NodeCreationError, "disabled"):
            self.service.create(self.command(request_id="request-2"))

    def test_user_selected_incompatible_model_is_not_replaced(self):
        self.compatibility.compatible = False
        selected = ModelBinding(selection_mode="user", provider_id="provider-x", model_id="model-x")
        with self.assertRaisesRegex(NodeCreationError, "not compatible"):
            self.service.create(self.command(requested_model_binding=selected))
        self.assertEqual(self.compatibility.seen, [selected])
        self.assertFalse(self.repository.nodes)

    def test_requires_authorization_and_current_revision(self):
        self.authorizer.allowed = False
        with self.assertRaisesRegex(NodeCreationError, "not permitted"):
            self.service.create(self.command())

        self.authorizer.allowed = True
        with self.assertRaises(StaleCanvasRevisionError):
            self.service.create(self.command(expected_revision=99))
        self.assertFalse(self.audit.events)

    def test_requires_explicit_model_when_definition_requires_one(self):
        with self.assertRaisesRegex(NodeCreationError, "requires an explicit"):
            self.service.create(self.command(requested_model_binding=None))

    def test_definition_ports_are_resolved_by_the_injected_registry(self):
        self.registry.definition = ResolvedNodeDefinition(**{
            **DEFINITION.__dict__,
            "ports": PortSet(outputs=[OutputPort(id="result", produces=["unknown.type"])])
        })
        with self.assertRaisesRegex(NodeCreationError, "unknown port types"):
            self.service.create(self.command(request_id="request-ports"))
        self.assertFalse(self.repository.nodes)

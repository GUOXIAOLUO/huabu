"""Canonical Canvas definitions for produced results.

Only one definition lives here, because only one canonical node shape is
authorized: a node that stands for a result the user chose. It is deliberately
not an ``asset`` or an ``artifact`` node — turning a result into one of those is
a different conversion with its own card — so it declares no ports: it cannot
claim to accept or produce typed values it has not been given.
"""

from workbench.application.node_creation import ResolvedNodeDefinition
from workbench.domain.canvas.models import DefinitionRef, RendererRef, Size
from workbench.domain.canvas.ports import PortSet


class ResultNodeDefinitionRegistry:
    """Resolve the canonical execution-result node definition."""

    EXECUTION_RESULT = DefinitionRef(type="workbench", id="execution-result", version="1")

    def resolve(self, definition_ref: DefinitionRef) -> ResolvedNodeDefinition | None:
        if definition_ref != self.EXECUTION_RESULT:
            return None
        return ResolvedNodeDefinition(
            definition_ref=self.EXECUTION_RESULT,
            kind="result",
            renderer=RendererRef(id="result", version="1"),
            title="Result",
            ports=PortSet(inputs=[], outputs=[]),
            default_size=Size(width=320, height=240),
        )


class ResultNodeModelCompatibilityPolicy:
    """A node that stands for a produced result is never bound to a model."""

    def is_compatible(self, definition: ResolvedNodeDefinition, binding: object) -> bool:
        return False

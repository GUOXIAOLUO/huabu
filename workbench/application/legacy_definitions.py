"""Temporary registry for explicitly approved Legacy node definitions."""

from workbench.application.node_creation import ResolvedNodeDefinition
from workbench.domain.canvas.models import DefinitionRef, RendererRef, Size
from workbench.domain.canvas.ports import InputPort, OutputPort, PortSet


class LegacyDefinitionRegistry:
    """Expose only low-risk definitions until the dynamic Skill registry exists."""

    IMAGE = DefinitionRef(type="legacy", id="image", version="0")
    PROMPT = DefinitionRef(type="legacy", id="prompt", version="0")
    LOOP = DefinitionRef(type="legacy", id="loop", version="0")
    GROUP = DefinitionRef(type="legacy", id="group", version="0")
    OUTPUT = DefinitionRef(type="legacy", id="output", version="0")
    COLLECTION = DefinitionRef(type="legacy", id="collection", version="0")
    SMART_PROMPT = DefinitionRef(type="legacy", id="smart-prompt", version="0")
    SMART_LOOP = DefinitionRef(type="legacy", id="smart-loop", version="0")
    SMART_GROUP = DefinitionRef(type="legacy", id="smart-group", version="0")
    SMART_MINIMAX = DefinitionRef(type="legacy", id="smart-minimax", version="0")

    def resolve(self, definition_ref: DefinitionRef) -> ResolvedNodeDefinition | None:
        if definition_ref == self.IMAGE:
            return ResolvedNodeDefinition(
                definition_ref=self.IMAGE,
                kind="asset",
                renderer=RendererRef(id="legacy", version="1"),
                title="Image",
                ports=PortSet(
                    inputs=[InputPort(id="legacy.in", accepts=["legacy.any"], multiple=True)],
                    outputs=[OutputPort(id="legacy.out", produces=["legacy.any"], multiple=True)],
                ),
                default_size=Size(width=280, height=180),
            )
        if definition_ref == self.COLLECTION:
            return ResolvedNodeDefinition(
                definition_ref=self.COLLECTION, kind="collection", renderer=RendererRef(id="legacy", version="1"), title="Collection",
                ports=PortSet(inputs=[], outputs=[]), default_size=Size(width=420, height=300),
            )
        if definition_ref not in {self.PROMPT, self.LOOP, self.GROUP, self.OUTPUT, self.SMART_PROMPT, self.SMART_LOOP, self.SMART_GROUP, self.SMART_MINIMAX}:
            return None
        return ResolvedNodeDefinition(
            definition_ref=definition_ref,
            kind="group" if definition_ref in {self.GROUP, self.SMART_GROUP} else "legacy",
            renderer=RendererRef(id="legacy", version="1"),
            title="Prompt" if definition_ref in {self.PROMPT, self.SMART_PROMPT} else "Loop" if definition_ref in {self.LOOP, self.SMART_LOOP} else "Output" if definition_ref == self.OUTPUT else "MiniMax H3" if definition_ref == self.SMART_MINIMAX else "智能分组" if definition_ref == self.SMART_GROUP else "Group",
            ports=PortSet(
                inputs=[InputPort(id="legacy.in", accepts=["legacy.any"], multiple=True)],
                outputs=[OutputPort(id="legacy.out", produces=["legacy.any"], multiple=True)],
            ),
            default_size=Size(width=1040 if definition_ref == self.SMART_MINIMAX else 460 if definition_ref == self.OUTPUT else 340 if definition_ref == self.SMART_GROUP else 300 if definition_ref == self.GROUP else 340 if definition_ref == self.SMART_PROMPT else 340 if definition_ref == self.SMART_LOOP else 280, height=640 if definition_ref == self.SMART_MINIMAX else 286 if definition_ref == self.SMART_GROUP else 220 if definition_ref == self.GROUP else 286 if definition_ref == self.SMART_PROMPT else 168 if definition_ref == self.SMART_LOOP else 180),
        )


class LegacyImageModelCompatibilityPolicy:
    """The approved blank Legacy Image node accepts no provider/model binding."""

    def is_compatible(self, definition: ResolvedNodeDefinition, binding: object) -> bool:
        return False

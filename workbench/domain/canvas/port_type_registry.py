"""Industry-neutral registry for typed Canvas port semantics."""

from dataclasses import dataclass
from typing import Iterable

from .ports import PortSet


@dataclass(frozen=True, slots=True)
class PortTypeDefinition:
    """A named port type; package extensions use the same registry seam."""

    id: str
    label: str
    parents: tuple[str, ...] = ()


class PortTypeRegistry:
    """Resolve and compare port types without embedding industry semantics."""

    def __init__(self, definitions: Iterable[PortTypeDefinition] = ()):
        self._definitions: dict[str, PortTypeDefinition] = {}
        for definition in definitions:
            self.register(definition)

    def register(self, definition: PortTypeDefinition) -> PortTypeDefinition:
        if not isinstance(definition, PortTypeDefinition):
            raise TypeError("PortTypeRegistry accepts PortTypeDefinition values")
        if not definition.id.strip() or "." not in definition.id:
            raise ValueError("port type ids must be non-empty namespaced values")
        if definition.id in self._definitions:
            raise ValueError(f"port type already registered: {definition.id}")
        if any(parent == definition.id for parent in definition.parents):
            raise ValueError(f"port type cannot parent itself: {definition.id}")
        missing = [parent for parent in definition.parents if parent not in self._definitions]
        if missing:
            raise ValueError(f"port type parents are not registered: {', '.join(missing)}")
        self._definitions[definition.id] = definition
        return definition

    def resolve(self, type_id: str) -> PortTypeDefinition | None:
        return self._definitions.get(type_id)

    def require(self, type_id: str) -> PortTypeDefinition:
        definition = self.resolve(type_id)
        if definition is None:
            raise LookupError(f"unknown port type: {type_id}")
        return definition

    def all(self) -> tuple[PortTypeDefinition, ...]:
        return tuple(self._definitions.values())

    def accepts(self, produced: str, accepted: str) -> bool:
        """Return whether one resolved output type can feed an input type."""
        if self.resolve(produced) is None or self.resolve(accepted) is None:
            return False
        if produced == accepted or accepted == "legacy.any":
            return True
        pending = [produced]
        visited: set[str] = set()
        while pending:
            current = pending.pop()
            if current in visited:
                continue
            visited.add(current)
            definition = self.require(current)
            if accepted in definition.parents:
                return True
            pending.extend(definition.parents)
        return False

    def resolve_port_set(self, ports: PortSet) -> dict[str, tuple[PortTypeDefinition, ...]]:
        """Resolve every accepted/produced string through this one registry."""
        return {
            "inputs": tuple(self.require(type_id) for port in ports.inputs for type_id in port.accepts),
            "outputs": tuple(self.require(type_id) for port in ports.outputs for type_id in port.produces),
        }


def create_core_port_type_registry() -> PortTypeRegistry:
    """Build the generic core vocabulary and the characterized Legacy catch-all."""
    registry = PortTypeRegistry()
    for definition in (
        PortTypeDefinition("asset.image", "Image asset"),
        PortTypeDefinition("asset.video", "Video asset"),
        PortTypeDefinition("asset.audio", "Audio asset"),
        PortTypeDefinition("asset.file", "File asset"),
        PortTypeDefinition("asset.cad", "CAD-compatible asset", ("asset.file",)),
        PortTypeDefinition("artifact.file", "File artifact"),
        PortTypeDefinition("artifact.image", "Image artifact", ("artifact.file",)),
        PortTypeDefinition("artifact.video", "Video artifact", ("artifact.file",)),
        PortTypeDefinition("text.plain", "Plain text"),
        PortTypeDefinition("legacy.any", "Legacy compatible value"),
    ):
        registry.register(definition)
    return registry

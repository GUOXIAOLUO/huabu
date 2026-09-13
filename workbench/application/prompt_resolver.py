"""Deterministic, provider-neutral Prompt layer resolution."""

from __future__ import annotations

from collections.abc import Iterable

from workbench.domain.prompt import PromptLayer, PromptLayerName, ResolvedPrompt


class PromptResolverError(ValueError):
    """Raised when prompt layers cannot produce one deterministic result."""


class PromptResolver:
    """Select one complete layer without concatenating or calling a model."""

    PRECEDENCE: tuple[PromptLayerName, ...] = ("default", "project", "task", "runtime")

    def resolve(self, layers: Iterable[PromptLayer]) -> ResolvedPrompt:
        by_layer: dict[PromptLayerName, PromptLayer] = {}
        for layer in layers:
            if layer.layer in by_layer:
                raise PromptResolverError(f"duplicate prompt layer: {layer.layer}")
            by_layer[layer.layer] = layer
        for layer_name in reversed(self.PRECEDENCE):
            selected = by_layer.get(layer_name)
            if selected is not None:
                return ResolvedPrompt(
                    prompt=selected.prompt,
                    content=selected.content,
                    source=selected.layer,
                    metadata=dict(selected.metadata),
                )
        raise PromptResolverError("at least one prompt layer is required")

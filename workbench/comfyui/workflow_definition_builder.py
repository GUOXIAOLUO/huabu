"""Build version-pinned, simplified Workbench definitions from Comfy graphs.

This module is deliberately limited to ComfyUI workflow mapping.  It does not
own Canvas nodes, provider connections, or execution; :class:`ComfyUIExecutor`
continues to own runtime submission and input injection.
"""

from __future__ import annotations

from typing import Any, Mapping

from .executor import (
    ComfyUIInputBinding,
    ComfyUIInputCandidate,
    ComfyUIOutputMapping,
    ComfyUIWorkflow,
    ComfyUIWorkflowRef,
)


class ComfyUIWorkflowDefinitionBuilder:
    """Discover safe slots and build one immutable simplified definition."""

    _ROLE_NAMES = {
        "text": "prompt",
        "prompt": "prompt",
        "positive": "prompt",
        "negative": "negative_prompt",
        "seed": "seed",
        "width": "width",
        "height": "height",
        "strength": "strength",
        "duration": "duration",
        "audio": "audio",
        "image": "image",
        "mask": "mask",
        "reference": "reference",
    }

    @classmethod
    def discover_inputs(cls, graph: Mapping[str, Any]) -> tuple[ComfyUIInputCandidate, ...]:
        """Return deterministic candidates for scalar, user-editable slots."""
        if not isinstance(graph, Mapping):
            raise ValueError("ComfyUI workflow graph must be a mapping")
        candidates: list[ComfyUIInputCandidate] = []
        for node_id in sorted(graph, key=str):
            node = graph[node_id]
            if not isinstance(node, Mapping) or not isinstance(node.get("inputs"), Mapping):
                continue
            for input_name, value in sorted(node["inputs"].items(), key=lambda item: str(item[0])):
                if isinstance(value, list) and len(value) == 2:
                    continue
                normalized = str(input_name).strip().lower()
                role = cls._ROLE_NAMES.get(normalized)
                if role is None:
                    continue
                candidates.append(ComfyUIInputCandidate(
                    role=role,
                    node_id=str(node_id),
                    input_name=str(input_name),
                    required=role in {"prompt", "image"},
                ))
        return tuple(candidates)

    @classmethod
    def build(cls, stored: Mapping[str, Any]) -> ComfyUIWorkflow:
        """Build a simplified definition from a stored versioned record.

        ``workflow_ref`` or the pair ``workflow_id``/``version`` is required;
        the builder never infers a latest version.  Mappings are explicit and
        validated against the stored graph before the definition is returned.
        """
        if not isinstance(stored, Mapping):
            raise TypeError("stored ComfyUI workflow must be a mapping")
        raw_ref = stored.get("workflow_ref")
        if raw_ref is None:
            raw_ref = {"workflow_id": stored.get("workflow_id") or stored.get("id"), "version": stored.get("version")}
        reference = ComfyUIWorkflowRef.parse(raw_ref)
        graph = stored.get("graph")
        if not isinstance(graph, Mapping):
            raise ValueError("stored ComfyUI workflow graph must be a mapping")
        input_bindings = tuple(ComfyUIInputBinding(**item) for item in stored.get("input_bindings", ()))
        output_mappings = tuple(ComfyUIOutputMapping(**item) for item in stored.get("output_mappings", ()))
        cls._validate_nodes(graph, input_bindings, output_mappings)
        return ComfyUIWorkflow(
            id=reference.workflow_id,
            version=reference.version,
            title=str(stored.get("title") or reference.ref),
            graph=dict(graph),
            input_bindings=input_bindings,
            output_mappings=output_mappings,
        )

    @staticmethod
    def _validate_nodes(graph: Mapping[str, Any], inputs: tuple[ComfyUIInputBinding, ...], outputs: tuple[ComfyUIOutputMapping, ...]) -> None:
        for binding in inputs:
            node = graph.get(binding.node_id)
            if not isinstance(node, Mapping) or not isinstance(node.get("inputs"), Mapping):
                raise ValueError(f"ComfyUI input binding references an unknown node: {binding.node_id}")
            if binding.input_name not in node["inputs"]:
                raise ValueError(f"ComfyUI input binding references an unknown input: {binding.node_id}.{binding.input_name}")
        for mapping in outputs:
            if mapping.node_id not in graph or not isinstance(graph[mapping.node_id], Mapping):
                raise ValueError(f"ComfyUI output mapping references an unknown node: {mapping.node_id}")
            if mapping.output_name.strip() == "":
                raise ValueError("ComfyUI output mapping requires an output name")

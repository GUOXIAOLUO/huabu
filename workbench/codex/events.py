"""Workbench-neutral runtime events projected from Codex protocol messages."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Mapping


RuntimeEventKind = Literal["lifecycle", "progress", "output", "error", "approval"]
RuntimeEventStatus = Literal["started", "running", "completed", "failed", "cancelled", "waiting"]


@dataclass(frozen=True)
class RuntimeDiagnosticRef:
    """Optional raw-protocol pointer retained for diagnostics and support."""

    protocol_method: str
    code: str


@dataclass(frozen=True)
class RuntimeEvent:
    """Stable event contract exposed by the Codex bridge to upper layers."""

    kind: RuntimeEventKind
    status: RuntimeEventStatus
    operation: str
    payload: Mapping[str, Any] = field(default_factory=dict)
    diagnostic_ref: RuntimeDiagnosticRef | None = None


class CodexEventNormalizer:
    """Translate Codex method names into Workbench-neutral event semantics."""

    @classmethod
    def normalize(cls, method: str, payload: Mapping[str, Any]) -> RuntimeEvent:
        normalized_method = method.lower()
        if "approval" in normalized_method:
            return RuntimeEvent("approval", "waiting", "approval", cls._neutral_payload(payload))
        if normalized_method == "turn/started":
            return RuntimeEvent("lifecycle", "started", "turn", cls._neutral_payload(payload))
        if normalized_method == "turn/completed":
            return RuntimeEvent("lifecycle", "completed", "turn", cls._neutral_payload(payload))
        if normalized_method in {"turn/failed", "turn/error"}:
            return RuntimeEvent(
                "error", "failed", "turn", cls._neutral_payload(payload), RuntimeDiagnosticRef(method, "turn-failed")
            )
        if normalized_method in {"turn/cancelled", "turn/canceled"}:
            return RuntimeEvent("lifecycle", "cancelled", "turn", cls._neutral_payload(payload))
        if normalized_method.startswith("item/"):
            status: RuntimeEventStatus = "completed" if normalized_method.endswith("/completed") else "running"
            kind: RuntimeEventKind = "output" if status == "completed" else "progress"
            return RuntimeEvent(kind, status, "item", cls._neutral_payload(payload))
        return RuntimeEvent("progress", "running", "runtime", {}, RuntimeDiagnosticRef(method, "notification"))

    @staticmethod
    def error(code: str, payload: Mapping[str, Any], *, protocol_method: str) -> RuntimeEvent:
        return RuntimeEvent(
            "error",
            "failed",
            "transport",
            CodexEventNormalizer._neutral_payload(payload),
            RuntimeDiagnosticRef(protocol_method, code),
        )

    @staticmethod
    def _neutral_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
        """Project common values without exposing the Codex params shape."""
        neutral: dict[str, Any] = {}
        for container, identifier, output_key in (("turn", "id", "runtime_id"), ("item", "id", "item_id")):
            value = payload.get(container)
            if isinstance(value, Mapping) and isinstance(value.get(identifier), str):
                neutral[output_key] = value[identifier]
                if container == "item" and isinstance(value.get("type"), str):
                    neutral["item_type"] = value["type"]
                if container == "item" and isinstance(value.get("text"), str):
                    neutral["text"] = value["text"]
        for key in ("reason", "message", "text", "progress", "error", "attempts", "timeout_seconds"):
            if key in payload and isinstance(payload[key], (bool, int, float, str)):
                neutral[key] = payload[key]
        return neutral

"""Typed compatibility models for the Codex App Server JSONL subset."""

from __future__ import annotations

import json
from typing import Any, Literal, TypeAlias

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CodexProtocolError(ValueError):
    """An invalid or unsupported Codex wire message."""


class ProtocolModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class ForwardCompatibleProtocolModel(ProtocolModel):
    """Validate the known fields while retaining newer server fields."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class ClientInfo(ProtocolModel):
    name: str = Field(min_length=1)
    version: str = Field(min_length=1)


class InitializeParams(ProtocolModel):
    client_info: ClientInfo = Field(alias="clientInfo")
    capabilities: dict[str, Any] = Field(default_factory=dict)


class TextInput(ProtocolModel):
    type: Literal["text"]
    text: str


class ThreadStartParams(ProtocolModel):
    cwd: str
    approval_policy: Literal["never"] = Field(alias="approvalPolicy")
    sandbox: Literal["read-only"]


class TurnStartParams(ProtocolModel):
    thread_id: str = Field(alias="threadId", min_length=1)
    input: tuple[TextInput, ...] = Field(min_length=1)
    cwd: str
    approval_policy: Literal["never"] = Field(alias="approvalPolicy")
    sandbox_policy: dict[str, Any] = Field(alias="sandboxPolicy")


class ThreadResumeParams(ThreadStartParams):
    thread_id: str = Field(alias="threadId", min_length=1)


class TurnInterruptParams(ProtocolModel):
    thread_id: str = Field(alias="threadId", min_length=1)
    turn_id: str = Field(alias="turnId", min_length=1)


class ConfigReadParams(ProtocolModel):
    cwd: str
    include_layers: Literal[True] = Field(alias="includeLayers")


class EmptyParams(ProtocolModel):
    pass


class ProtocolRequest(ProtocolModel):
    id: int = Field(gt=0)
    method: str = Field(min_length=1)
    params: dict[str, Any] = Field(default_factory=dict)


class ProtocolNotification(ProtocolModel):
    method: str = Field(min_length=1)
    params: dict[str, Any] = Field(default_factory=dict)


class ProtocolServerRequest(ProtocolNotification):
    id: int = Field(gt=0)


class ProtocolResponse(ProtocolModel):
    id: int = Field(gt=0)
    result: dict[str, Any] | None = None
    error: dict[str, Any] | None = None

    @model_validator(mode="after")
    def require_one_outcome(self) -> "ProtocolResponse":
        if (self.result is None) == (self.error is None):
            raise ValueError("Codex response must contain exactly one of result or error")
        return self


class InitializeResult(ForwardCompatibleProtocolModel):
    protocol_version: str = Field(alias="protocolVersion", min_length=1)


class ThreadReference(ForwardCompatibleProtocolModel):
    id: str = Field(min_length=1)


class ThreadStartResult(ForwardCompatibleProtocolModel):
    thread: ThreadReference


class TurnReference(ForwardCompatibleProtocolModel):
    id: str = Field(min_length=1)


class TurnStartResult(ForwardCompatibleProtocolModel):
    turn: TurnReference


class EmptyResult(ProtocolModel):
    pass


class CodexModel(ForwardCompatibleProtocolModel):
    id: str | None = None
    name: str | None = None


class ModelListResult(ProtocolModel):
    data: tuple[CodexModel, ...]


class ConfigReadResult(ProtocolModel):
    config: dict[str, Any]


ServerMessage: TypeAlias = ProtocolResponse | ProtocolNotification | ProtocolServerRequest


def parse_server_message(raw: bytes | str) -> ServerMessage:
    try:
        payload = json.loads(raw)
    except (TypeError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CodexProtocolError("Codex message is not valid JSON") from exc
    if not isinstance(payload, dict):
        raise CodexProtocolError("Codex message must be a JSON object")
    try:
        if "method" in payload:
            if "id" in payload:
                return ProtocolServerRequest.model_validate(payload)
            return ProtocolNotification.model_validate(payload)
        return ProtocolResponse.model_validate(payload)
    except ValueError as exc:
        raise CodexProtocolError(f"invalid Codex message: {exc}") from exc


class CodexProtocolCompatibility:
    """Version policy isolated from transport and Workbench application code."""

    supported_protocol_versions = frozenset({"2"})

    @classmethod
    def validate_initialize(cls, result: InitializeResult) -> InitializeResult:
        if result.protocol_version not in cls.supported_protocol_versions:
            raise CodexProtocolError(f"unsupported Codex protocol version: {result.protocol_version}")
        return result

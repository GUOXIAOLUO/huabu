"""MCP capability execution boundary.

`MCPExecutor` owns the Workbench side of one MCP capability invocation:
connection and capability reference resolution, the deterministic
capability-kind to MCP-action mapping, input role to argument mapping, and
normalization of MCP results, progress and errors.  MCP transport stays behind
the injected `MCPTransport` port, and Integration references are carried as
opaque values only.
"""

from .executor import (
    CAPABILITY_ACTIONS,
    DEFAULT_MCP_CANCEL_TIMEOUT_SECONDS,
    DEFAULT_MCP_TIMEOUT_SECONDS,
    MCP_EXECUTOR_REF,
    MCP_RUNTIME_ROUTE,
    CapabilityResolver,
    MCPActionKind,
    MCPCall,
    MCPCapability,
    MCPCapabilityKind,
    MCPCapabilityRef,
    MCPExecutor,
    MCPExecutorError,
    MCPInputBinding,
    MCPOutputItem,
    MCPOutputKind,
    MCPRawEvent,
    MCPRawEventKind,
    MCPSubmission,
    MCPTransport,
    MCPTransportError,
)

__all__ = [
    "CAPABILITY_ACTIONS",
    "DEFAULT_MCP_CANCEL_TIMEOUT_SECONDS",
    "DEFAULT_MCP_TIMEOUT_SECONDS",
    "MCP_EXECUTOR_REF",
    "MCP_RUNTIME_ROUTE",
    "CapabilityResolver",
    "MCPActionKind",
    "MCPCall",
    "MCPCapability",
    "MCPCapabilityKind",
    "MCPCapabilityRef",
    "MCPExecutor",
    "MCPExecutorError",
    "MCPInputBinding",
    "MCPOutputItem",
    "MCPOutputKind",
    "MCPRawEvent",
    "MCPRawEventKind",
    "MCPSubmission",
    "MCPTransport",
    "MCPTransportError",
]

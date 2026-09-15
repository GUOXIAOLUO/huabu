"""ComfyUI workflow execution boundary.

`ComfyUIExecutor` owns the Workbench side of one ComfyUI run: versioned
workflow reference resolution, input role to workflow input mapping, and
normalization of ComfyUI progress/output events.  ComfyUI transport stays
behind the injected `ComfyUITransport` port, and no Canvas graph is recreated
or required.
"""

from .executor import (
    COMFYUI_EXECUTOR_REF,
    COMFYUI_RUNTIME_ROUTE,
    DEFAULT_COMFYUI_CANCEL_TIMEOUT_SECONDS,
    DEFAULT_COMFYUI_TIMEOUT_SECONDS,
    ComfyUICall,
    ComfyUIExecutor,
    ComfyUIExecutorError,
    ComfyUIInputBinding,
    ComfyUIInputCandidate,
    ComfyUIOutputMapping,
    ComfyUIOutputItem,
    ComfyUIRawEvent,
    ComfyUISubmission,
    ComfyUITransport,
    ComfyUITransportError,
    ComfyUIWorkflow,
    ComfyUIWorkflowRef,
    WorkflowResolver,
)
from .workflow_definition_builder import ComfyUIWorkflowDefinitionBuilder

__all__ = [
    "COMFYUI_EXECUTOR_REF",
    "COMFYUI_RUNTIME_ROUTE",
    "DEFAULT_COMFYUI_CANCEL_TIMEOUT_SECONDS",
    "DEFAULT_COMFYUI_TIMEOUT_SECONDS",
    "ComfyUICall",
    "ComfyUIExecutor",
    "ComfyUIExecutorError",
    "ComfyUIInputBinding",
    "ComfyUIInputCandidate",
    "ComfyUIOutputMapping",
    "ComfyUIOutputItem",
    "ComfyUIRawEvent",
    "ComfyUISubmission",
    "ComfyUITransport",
    "ComfyUITransportError",
    "ComfyUIWorkflow",
    "ComfyUIWorkflowRef",
    "WorkflowResolver",
    "ComfyUIWorkflowDefinitionBuilder",
]

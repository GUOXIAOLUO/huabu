"""Generic direct model/API execution route boundary.

The executor adapts one direct provider call into the provider-neutral
Executor lifecycle.  HTTP/SDK details, authentication and credential
resolution stay behind the injected ``DirectModelTransport`` port, so no
provider SDK or secret material reaches the domain.
"""

from .executor import (
    DEFAULT_DIRECT_MODEL_CANCEL_TIMEOUT_SECONDS,
    DEFAULT_DIRECT_MODEL_TIMEOUT_SECONDS,
    DIRECT_MODEL_EXECUTOR_REF,
    DIRECT_MODEL_OUTPUT_NAME,
    DIRECT_MODEL_ROUTE_TYPE,
    AvailabilityResolver,
    ConnectionResolver,
    DirectModelCall,
    DirectModelExecutor,
    DirectModelExecutorError,
    DirectModelRawEvent,
    DirectModelSubmission,
    DirectModelTransport,
    DirectModelTransportError,
)

__all__ = [
    "DEFAULT_DIRECT_MODEL_CANCEL_TIMEOUT_SECONDS",
    "DEFAULT_DIRECT_MODEL_TIMEOUT_SECONDS",
    "DIRECT_MODEL_EXECUTOR_REF",
    "DIRECT_MODEL_OUTPUT_NAME",
    "DIRECT_MODEL_ROUTE_TYPE",
    "AvailabilityResolver",
    "ConnectionResolver",
    "DirectModelCall",
    "DirectModelExecutor",
    "DirectModelExecutorError",
    "DirectModelRawEvent",
    "DirectModelSubmission",
    "DirectModelTransport",
    "DirectModelTransportError",
]

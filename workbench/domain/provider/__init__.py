"""Generic provider definition and connection records."""

from .models import (
    CREDENTIAL_REF_SCHEMA_VERSION,
    MODEL_DEFINITION_SCHEMA_VERSION,
    PROVIDER_CONNECTION_SCHEMA_VERSION,
    PROVIDER_DEFINITION_SCHEMA_VERSION,
    CredentialRef,
    ProviderConnection,
    ProviderDefinition,
    ModelDefinition,
)

__all__ = [
    "CREDENTIAL_REF_SCHEMA_VERSION",
    "MODEL_DEFINITION_SCHEMA_VERSION",
    "PROVIDER_CONNECTION_SCHEMA_VERSION",
    "PROVIDER_DEFINITION_SCHEMA_VERSION",
    "CredentialRef",
    "ModelDefinition",
    "ProviderConnection",
    "ProviderDefinition",
]

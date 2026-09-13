"""Business-neutral ProviderDefinition metadata, separate from connections."""

from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator
from workbench.domain.value_types import OpaqueId, assert_safe_metadata


PROVIDER_DEFINITION_SCHEMA_VERSION = "workbench.provider-definition/1"
PROVIDER_CONNECTION_SCHEMA_VERSION = "workbench.provider-connection/1"
CREDENTIAL_REF_SCHEMA_VERSION = "workbench.credential-ref/1"
MODEL_DEFINITION_SCHEMA_VERSION = "workbench.model-definition/1"
class ProviderDefinition(BaseModel):
    """Stable adapter/protocol-family metadata with no configured endpoint."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal[PROVIDER_DEFINITION_SCHEMA_VERSION] = PROVIDER_DEFINITION_SCHEMA_VERSION
    id: OpaqueId
    title: Annotated[str, Field(min_length=1, max_length=500)]
    protocol: OpaqueId
    capabilities: tuple[OpaqueId, ...] = ()
    config_schema: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def require_unique_capabilities(self):
        if len(self.capabilities) != len(set(self.capabilities)):
            raise ValueError("provider definition capabilities must be unique")
        assert_safe_metadata(self.metadata)
        return self


class CredentialRef(BaseModel):
    """Opaque reference to secret material owned by a credential store."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal[CREDENTIAL_REF_SCHEMA_VERSION] = CREDENTIAL_REF_SCHEMA_VERSION
    id: OpaqueId


ConnectionStatus = Literal["active", "disabled", "error", "unknown"]


class ProviderConnection(BaseModel):
    """Configured endpoint/account metadata without the endpoint secret."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal[PROVIDER_CONNECTION_SCHEMA_VERSION] = PROVIDER_CONNECTION_SCHEMA_VERSION
    id: OpaqueId
    provider_id: OpaqueId
    ref: OpaqueId
    config: dict[str, Any] = Field(default_factory=dict)
    credential_ref: CredentialRef | None = None
    status: ConnectionStatus = "unknown"
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def require_secret_free_serializable_fields(self):
        assert_safe_metadata(self.config, path="config")
        assert_safe_metadata(self.metadata)
        return self


class ModelDefinition(BaseModel):
    """Provider-neutral model identity and capability metadata."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal[MODEL_DEFINITION_SCHEMA_VERSION] = MODEL_DEFINITION_SCHEMA_VERSION
    id: OpaqueId
    family: OpaqueId
    display_name: Annotated[str, Field(min_length=1, max_length=500)]
    normalized_capabilities: tuple[OpaqueId, ...] = ()
    input_modalities: tuple[OpaqueId, ...] = ()
    output_modalities: tuple[OpaqueId, ...] = ()
    context_window: Annotated[int, Field(ge=1)] | None = None
    parameter_schema: dict[str, Any] = Field(default_factory=dict)
    native_metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def require_unique_metadata_values(self):
        for field_name in ("normalized_capabilities", "input_modalities", "output_modalities"):
            values = getattr(self, field_name)
            if len(values) != len(set(values)):
                raise ValueError(f"model definition {field_name} must be unique")
        assert_safe_metadata(self.native_metadata)
        return self

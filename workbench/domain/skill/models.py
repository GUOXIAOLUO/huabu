"""Business-neutral, versioned Workbench Skill definition records."""

from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from workbench.domain.canvas.models import DefinitionRef, RendererRef
from workbench.domain.canvas.ports import PortSet
from workbench.domain.prompt import PromptRef


SKILL_SCHEMA_VERSION = "workbench.skill/1"
SKILL_PACK_SCHEMA_VERSION = "workbench.skill-pack/1"
SKILL_BINDING_SCHEMA_VERSION = "workbench.skill-binding/1"
OpaqueId = Annotated[str, Field(min_length=1, max_length=255)]


class SkillPackageRef(BaseModel):
    """Optional package provenance; it does not imply a package runtime."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    package_id: OpaqueId
    version: Annotated[str, Field(min_length=1, max_length=120)]


class SkillRef(BaseModel):
    """Exact reference used to associate one Skill version with a Pack."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    skill_id: OpaqueId
    version: Annotated[str, Field(min_length=1, max_length=120)]


class SkillBinding(BaseModel):
    """An exact Skill version and its task-local configuration."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal[SKILL_BINDING_SCHEMA_VERSION] = SKILL_BINDING_SCHEMA_VERSION
    skill_id: OpaqueId
    version: Annotated[str, Field(min_length=1, max_length=120)]
    enabled: bool = True
    parameters: dict[str, Any] = Field(default_factory=dict)
    prompt_override: PromptRef | None = None
    execution_profile_ref: OpaqueId | None = None

    def validate_against(self, definition: "SkillDefinition") -> "SkillBinding":
        """Validate exact identity and task parameters against a Skill schema."""
        if not isinstance(definition, SkillDefinition):
            raise TypeError("SkillBinding requires a SkillDefinition")
        if (self.skill_id, self.version) != (definition.id, definition.version):
            raise ValueError("skill binding must reference the exact SkillDefinition version")
        _validate_json_schema(self.parameters, definition.parameter_schema, path="parameters")
        return self


class SkillPack(BaseModel):
    """Generic installable/discoverable grouping of exact Skill references."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal[SKILL_PACK_SCHEMA_VERSION] = SKILL_PACK_SCHEMA_VERSION
    id: OpaqueId
    version: Annotated[str, Field(min_length=1, max_length=120)]
    title: Annotated[str, Field(min_length=1, max_length=500)]
    description: str = ""
    package: SkillPackageRef | None = None
    skills: tuple[SkillRef, ...] = ()
    enabled: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def require_unique_skills(self):
        keys = [(item.skill_id, item.version) for item in self.skills]
        if len(keys) != len(set(keys)):
            raise ValueError("skill pack references must be unique")
        return self


class SkillCapabilityRequirement(BaseModel):
    """Declarative capability requirement with no provider or industry vocabulary."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: OpaqueId
    version: Annotated[str, Field(min_length=1, max_length=120)] | None = None
    parameters: dict[str, Any] = Field(default_factory=dict)


class SkillExecutionRoute(BaseModel):
    """Declarative route metadata; selection/execution belongs to later services."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    route_type: OpaqueId
    route_ref: OpaqueId
    executor_type: OpaqueId
    execution_profile: OpaqueId | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class SkillPresentation(BaseModel):
    """Presentation hints consumed by a renderer/NodeShell boundary."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    renderer: RendererRef | None = None
    view: Annotated[str, Field(min_length=1, max_length=120)] | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class SkillWorkspace(BaseModel):
    """Workspace projection metadata without owning workspace lifecycle."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    workspace_type: OpaqueId
    entrypoint: Annotated[str, Field(min_length=1, max_length=255)] | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class SkillDefinition(BaseModel):
    """Stable, generic Skill contract; execution is intentionally out of scope."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal[SKILL_SCHEMA_VERSION] = SKILL_SCHEMA_VERSION
    id: OpaqueId
    version: Annotated[str, Field(min_length=1, max_length=120)]
    package: SkillPackageRef | None = None
    title: Annotated[str, Field(min_length=1, max_length=500)]
    description: str = ""
    input_schema: dict[str, Any] = Field(default_factory=dict)
    output_schema: dict[str, Any] = Field(default_factory=dict)
    parameter_schema: dict[str, Any] = Field(default_factory=dict)
    ports: PortSet = Field(default_factory=PortSet)
    capability_requirements: tuple[SkillCapabilityRequirement, ...] = ()
    prompt: PromptRef | None = None
    presentation: SkillPresentation = Field(default_factory=SkillPresentation)
    workspace: SkillWorkspace | None = None
    execution_routes: tuple[SkillExecutionRoute, ...] = ()
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def definition_ref(self) -> DefinitionRef:
        """Expose the generic resolver key without making Skill a Canvas node."""
        return DefinitionRef(type="skill", id=self.id, version=self.version)

    @model_validator(mode="after")
    def require_unique_capabilities_and_routes(self):
        capability_ids = [item.id for item in self.capability_requirements]
        if len(capability_ids) != len(set(capability_ids)):
            raise ValueError("skill capability requirement ids must be unique")
        route_keys = [(item.route_type, item.route_ref) for item in self.execution_routes]
        if len(route_keys) != len(set(route_keys)):
            raise ValueError("skill execution routes must be unique")
        return self


def _validate_json_schema(value: Any, schema: dict[str, Any], *, path: str) -> None:
    """Validate the JSON-schema subset needed by task Skill parameters."""
    if not schema:
        return
    expected_type = schema.get("type")
    type_matches = {
        "object": isinstance(value, dict),
        "array": isinstance(value, list),
        "string": isinstance(value, str),
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "number": isinstance(value, (int, float)) and not isinstance(value, bool),
        "boolean": isinstance(value, bool),
        "null": value is None,
    }
    if expected_type in type_matches and not type_matches[expected_type]:
        raise ValueError(f"{path} must be {expected_type}")
    if "enum" in schema and value not in schema["enum"]:
        raise ValueError(f"{path} is not an allowed value")
    if isinstance(value, dict):
        properties = schema.get("properties") or {}
        missing = [name for name in schema.get("required") or [] if name not in value]
        if missing:
            raise ValueError(f"{path} is missing required parameter(s): {', '.join(missing)}")
        if schema.get("additionalProperties") is False:
            unknown = sorted(set(value) - set(properties))
            if unknown:
                raise ValueError(f"{path} contains unknown parameter(s): {', '.join(unknown)}")
        for name, child_schema in properties.items():
            if name in value and isinstance(child_schema, dict):
                _validate_json_schema(value[name], child_schema, path=f"{path}.{name}")
    if isinstance(value, list) and isinstance(schema.get("items"), dict):
        for index, item in enumerate(value):
            _validate_json_schema(item, schema["items"], path=f"{path}[{index}]")

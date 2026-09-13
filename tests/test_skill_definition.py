"""Behavioral contract tests for the generic SkillDefinition domain record."""

import unittest

from pydantic import ValidationError

from workbench.domain.canvas.models import RendererRef
from workbench.domain.prompt import PromptRef
from workbench.domain.skill import (
    SKILL_SCHEMA_VERSION,
    SkillCapabilityRequirement,
    SkillBinding,
    SkillDefinition,
    SkillExecutionRoute,
    SkillPackageRef,
    SkillPresentation,
    SkillWorkspace,
)


class SkillDefinitionTests(unittest.TestCase):
    def make_definition(self, **changes):
        payload = {
            "id": "common.image-analysis",
            "version": "1.0.0",
            "package": {"package_id": "workbench.common", "version": "1.0.0"},
            "title": "Image analysis",
            "description": "Analyze an image and return structured observations.",
            "input_schema": {"type": "object", "properties": {"image": {"type": "string"}}},
            "output_schema": {"type": "object", "properties": {"observations": {"type": "array"}}},
            "parameter_schema": {"type": "object", "properties": {"detail": {"type": "string"}}},
            "ports": {
                "inputs": [{"id": "image", "accepts": ["asset.image"], "required": True}],
                "outputs": [{"id": "observations", "produces": ["artifact.file"]}],
            },
            "capability_requirements": [{"id": "vision.analysis", "version": "1"}],
            "prompt": {"prompt_id": "common.image-analysis.prompt", "version": 1},
            "presentation": {"renderer": {"id": "skill", "version": "1"}, "view": "task"},
            "workspace": {"workspace_type": "generic", "entrypoint": "analysis"},
            "execution_routes": [{
                "route_type": "runtime", "route_ref": "local.default", "executor_type": "script",
                "execution_profile": "default",
            }],
            "metadata": {"tags": ["image", "analysis"]},
        }
        payload.update(changes)
        return payload

    def test_definition_keeps_generic_versioned_contract_and_resolver_key(self):
        definition = SkillDefinition.model_validate(self.make_definition())

        self.assertEqual(definition.schema_version, SKILL_SCHEMA_VERSION)
        self.assertEqual(definition.definition_ref.model_dump(), {"type": "skill", "id": definition.id, "version": definition.version})
        self.assertEqual(definition.package, SkillPackageRef(package_id="workbench.common", version="1.0.0"))
        self.assertEqual(definition.prompt, PromptRef(prompt_id="common.image-analysis.prompt", version=1))
        self.assertEqual(definition.ports.inputs[0].accepts, ["asset.image"])
        self.assertEqual(definition.execution_routes[0].executor_type, "script")
        self.assertIsInstance(definition.presentation.renderer, RendererRef)
        self.assertIsInstance(definition.workspace, SkillWorkspace)

    def test_definition_is_immutable_and_rejects_unknown_fields(self):
        definition = SkillDefinition.model_validate(self.make_definition())

        with self.assertRaises(ValidationError):
            definition.title = "changed"
        with self.assertRaises(ValidationError):
            SkillDefinition.model_validate(self.make_definition(provider_sdk="vendor.client"))

    def test_definition_rejects_duplicate_capabilities_and_routes(self):
        duplicate_capabilities = [
            {"id": "vision.analysis"},
            {"id": "vision.analysis", "version": "2"},
        ]
        with self.assertRaises(ValidationError):
            SkillDefinition.model_validate(self.make_definition(capability_requirements=duplicate_capabilities))

        duplicate_routes = [
            {"route_type": "runtime", "route_ref": "local.default", "executor_type": "script"},
            {"route_type": "runtime", "route_ref": "local.default", "executor_type": "other"},
        ]
        with self.assertRaises(ValidationError):
            SkillDefinition.model_validate(self.make_definition(execution_routes=duplicate_routes))

    def test_skill_binding_keeps_exact_version_and_validates_parameters(self):
        definition = SkillDefinition.model_validate(self.make_definition(parameter_schema={
            "type": "object", "required": ["detail"],
            "properties": {"detail": {"type": "string"}},
            "additionalProperties": False,
        }))
        binding = SkillBinding(skill_id=definition.id, version=definition.version, parameters={"detail": "high"})
        self.assertIs(binding.validate_against(definition), binding)
        restored = SkillBinding.model_validate(binding.model_dump(mode="json"))
        self.assertEqual(restored.parameters, {"detail": "high"})
        with self.assertRaisesRegex(ValueError, "missing required"):
            SkillBinding(skill_id=definition.id, version=definition.version).validate_against(definition)
        with self.assertRaisesRegex(ValueError, "exact SkillDefinition version"):
            SkillBinding(skill_id=definition.id, version="2.0.0", parameters={"detail": "high"}).validate_against(definition)


if __name__ == "__main__":
    unittest.main()

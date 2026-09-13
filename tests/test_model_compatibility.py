import unittest

from workbench.application.model_compatibility import CapabilityMatchError, ModelCompatibilityResolver
from workbench.domain.availability import ModelAvailability
from workbench.domain.skill import SkillCapabilityRequirement


def availability(identifier, capabilities, *, route_type="provider", enabled=True, status="available"):
    return ModelAvailability(
        id=identifier,
        model_ref="model-x",
        route_type=route_type,
        route_ref=identifier,
        executor_type="executor",
        normalized_capabilities=tuple(capabilities),
        enabled=enabled,
        status=status,
    )


class ModelCompatibilityTests(unittest.TestCase):
    def test_requirements_select_the_best_route_deterministically(self):
        resolver = ModelCompatibilityResolver()
        result = resolver.resolve(
            [SkillCapabilityRequirement(id="Vision"), "text-generation"],
            [
                availability("runtime-route", ["vision", "text_generation", "reasoning"], route_type="runtime"),
                availability("provider-route", ["vision", "text_generation"]),
            ],
            model_ref="model-x",
        )

        self.assertTrue(result.compatible)
        self.assertEqual(result.requirements, ("text_generation", "vision"))
        self.assertEqual(result.selected.id, "provider-route")
        self.assertEqual([item.availability.id for item in result.candidates], ["provider-route", "runtime-route"])

    def test_incompatibility_explains_disabled_and_missing_routes_without_fallback(self):
        result = ModelCompatibilityResolver().resolve(
            ["vision", "reasoning"],
            [
                availability("disabled", ["vision", "reasoning"], enabled=False),
                availability("partial", ["vision"]),
            ],
            model_ref="model-x",
        )

        self.assertFalse(result.compatible)
        self.assertIsNone(result.selected)
        self.assertIn("route_disabled", result.reasons)
        self.assertIn("missing_capability:reasoning", result.reasons)

    def test_empty_requirements_fail_explicitly(self):
        with self.assertRaises(CapabilityMatchError):
            ModelCompatibilityResolver().resolve([], [])


if __name__ == "__main__":
    unittest.main()

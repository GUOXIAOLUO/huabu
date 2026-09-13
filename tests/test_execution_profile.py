import unittest

from pydantic import ValidationError

from workbench.domain.execution import (
    EXECUTION_PROFILE_SCHEMA_VERSION,
    ExecutionProfile,
    ExecutionProfileRef,
)
from workbench.domain.skill import SkillBinding
from workbench.repositories.execution_profile_repository import InMemoryExecutionProfileRepository


class ExecutionProfileTests(unittest.TestCase):
    def profile(self, version=1, **kwargs):
        values = dict(
            id="profile-local",
            version=version,
            name="Local fast",
            executor_ref="model-api",
            runtime_connection_ref="runtime-local",
            model_availability_ref="model-local",
            default_params={"temperature": 0.2},
            safety_policy_ref="safe-default",
            timeout_seconds=45,
        )
        values.update(kwargs)
        return ExecutionProfile(**values)

    def test_profile_is_versioned_and_round_trips_through_repository(self):
        repository = InMemoryExecutionProfileRepository()
        first = self.profile()
        second = self.profile(version=2, default_params={"temperature": 0.4})
        repository.save(first)
        repository.save(second)

        self.assertEqual(first.schema_version, EXECUTION_PROFILE_SCHEMA_VERSION)
        self.assertEqual(repository.get(first.ref), first)
        self.assertEqual([item.version for item in repository.list("profile-local")], [1, 2])
        self.assertEqual(ExecutionProfileRef.model_validate(first.ref.model_dump()), first.ref)

    def test_skill_can_hold_an_opaque_profile_ref_without_executor_internals(self):
        profile = self.profile()
        binding = SkillBinding(skill_id="skill", version="1", execution_profile_ref=profile.id)

        self.assertEqual(binding.execution_profile_ref, profile.id)
        self.assertNotIn("executor_ref", binding.model_dump())
        self.assertEqual(profile.ref, ExecutionProfileRef(profile_id=profile.id, version=profile.version))

    def test_profiles_reject_secret_like_defaults_and_invalid_timeouts(self):
        with self.assertRaises(ValueError):
            self.profile(default_params={"api_key": "secret"})
        with self.assertRaises(ValidationError):
            self.profile(timeout_seconds=0)
        repository = InMemoryExecutionProfileRepository()
        repository.save(self.profile())
        with self.assertRaises(ValueError):
            repository.save(self.profile())


if __name__ == "__main__":
    unittest.main()

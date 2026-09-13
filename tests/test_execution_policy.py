import unittest

from pydantic import ValidationError

from workbench.domain.collection import Collection
from workbench.domain.execution import EXECUTION_POLICY_SCHEMA_VERSION, ExecutionPolicy


class ExecutionPolicyTests(unittest.TestCase):
    def test_policy_round_trips_with_all_scheduling_controls(self):
        policy = ExecutionPolicy(
            mode="batch",
            concurrency=4,
            start_index=2,
            limit=20,
            retry=2,
            timeout=45.5,
            order="input",
            continue_on_error=True,
        )

        restored = ExecutionPolicy.model_validate(policy.model_dump())

        self.assertEqual(restored, policy)
        self.assertEqual(policy.schema_version, EXECUTION_POLICY_SCHEMA_VERSION)

    def test_defaults_are_single_and_bounded(self):
        policy = ExecutionPolicy()

        self.assertEqual(
            (policy.mode, policy.concurrency, policy.start_index, policy.limit, policy.retry, policy.timeout, policy.order, policy.continue_on_error),
            ("single", 1, 0, None, 0, 300.0, "input", False),
        )

    def test_invalid_ranges_and_single_concurrency_are_rejected(self):
        for field, value in (("concurrency", 0), ("start_index", -1), ("limit", 0), ("retry", -1), ("timeout", 0)):
            with self.subTest(field=field):
                with self.assertRaises(ValidationError):
                    ExecutionPolicy(**{field: value})
        with self.assertRaises(ValueError):
            ExecutionPolicy(mode="single", concurrency=2)

    def test_policy_is_not_collection_semantics(self):
        self.assertNotIn("collection", ExecutionPolicy.model_fields)
        self.assertNotIn("rows", ExecutionPolicy.model_fields)
        self.assertNotIn("items", ExecutionPolicy.model_fields)
        self.assertNotIn("policy", Collection.model_fields)


if __name__ == "__main__":
    unittest.main()

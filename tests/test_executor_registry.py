import unittest

from workbench.application.executor_registry import (
    ExecutorRegistry,
    ExecutorRegistryError,
    ExecutorRegistration,
)
from workbench.domain.execution import (
    CancelResult,
    ExecutionHandle,
    ExecutionRequest,
    ExecutionResult,
    ExecutionStatusSnapshot,
    ExecutorHealth,
    PreparedExecution,
)


class FakeExecutor:
    def __init__(self, executor_ref):
        self.executor_ref = executor_ref

    async def prepare(self, request: ExecutionRequest) -> PreparedExecution:
        return PreparedExecution(execution_id=request.execution_id, executor_ref=self.executor_ref)

    async def start(self, prepared: PreparedExecution) -> ExecutionHandle:
        return ExecutionHandle(execution_id=prepared.execution_id, executor_ref=self.executor_ref)

    async def stream(self, handle):
        if False:
            yield handle

    async def cancel(self, handle):
        return CancelResult(execution_id=handle.execution_id, accepted=False, status="unknown")

    async def status(self, handle):
        return ExecutionStatusSnapshot(execution_id=handle.execution_id, status="queued")

    async def result(self, handle):
        return ExecutionResult(execution_id=handle.execution_id, status="succeeded")

    async def cleanup(self, handle):
        return None

    async def health(self):
        return ExecutorHealth(executor_ref=self.executor_ref, status="healthy")


class ExecutorRegistryTests(unittest.TestCase):
    def registration(self, executor_ref, **kwargs):
        return ExecutorRegistration(executor=FakeExecutor(executor_ref), **kwargs)

    def test_resolves_exact_route_profile_and_capabilities_deterministically(self):
        registry = ExecutorRegistry((
            self.registration("z-executor", capabilities=("text",), runtime_routes=("local",), execution_profiles=("fast",)),
            self.registration("a-executor", capabilities=("text", "vision"), runtime_routes=("local",), execution_profiles=("fast",)),
        ))

        result = registry.resolve(
            runtime_route_ref="local",
            execution_profile_ref="fast",
            required_capabilities=("vision",),
        )

        self.assertTrue(result.resolved)
        self.assertEqual(result.executor.executor_ref, "a-executor")
        self.assertEqual(result.candidate_executor_refs, ("a-executor",))

    def test_returns_explicit_unavailable_reason_without_fallback(self):
        registry = ExecutorRegistry((
            self.registration("local", runtime_routes=("local",), execution_profiles=("fast",)),
        ))

        route_result = registry.resolve(runtime_route_ref="cloud")
        profile_result = registry.resolve(execution_profile_ref="deep")
        capability_result = registry.resolve(required_capabilities=("vision",))

        self.assertEqual(route_result.reason, "runtime_route_unavailable")
        self.assertEqual(profile_result.reason, "execution_profile_unavailable")
        self.assertEqual(capability_result.reason, "capabilities_unavailable")
        self.assertIsNone(route_result.executor)

    def test_combined_constraints_do_not_cross_select_another_executor(self):
        registry = ExecutorRegistry((
            self.registration("profile-only", runtime_routes=("local",), execution_profiles=("deep",)),
            self.registration("route-only", runtime_routes=("cloud",), execution_profiles=("fast",)),
        ))

        result = registry.resolve(runtime_route_ref="cloud", execution_profile_ref="deep")

        self.assertFalse(result.resolved)
        self.assertEqual(result.reason, "no_compatible_executor")

    def test_duplicate_registration_and_invalid_selector_are_rejected(self):
        first = self.registration("same", runtime_routes=("local",))
        registry = ExecutorRegistry((first,))
        with self.assertRaisesRegex(ExecutorRegistryError, "already registered"):
            registry.register(first)
        with self.assertRaises(ValueError):
            registry.resolve(required_capabilities=("text", "text"))
        with self.assertRaises(ValueError):
            registry.resolve(required_capabilities=(1,))
        with self.assertRaises(ValueError):
            registry.resolve(runtime_route_ref="")


if __name__ == "__main__":
    unittest.main()

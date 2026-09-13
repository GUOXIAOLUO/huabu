import unittest

from workbench.domain.execution import (
    CancelResult,
    ExecutionEvent,
    ExecutionHandle,
    ExecutionInput,
    ExecutionOutput,
    ExecutionRequest,
    ExecutionResult,
    ExecutionStatusSnapshot,
    Executor,
    ExecutorHealth,
    PreparedExecution,
)


class FakeExecutor:
    executor_ref = "fake-executor"

    def __init__(self):
        self.cancel_calls = 0
        self.cleaned = False

    async def prepare(self, request):
        return PreparedExecution(execution_id=request.execution_id, executor_ref=self.executor_ref)

    async def start(self, prepared):
        return ExecutionHandle(execution_id=prepared.execution_id, executor_ref=self.executor_ref)

    async def stream(self, handle):
        yield ExecutionEvent(execution_id=handle.execution_id, sequence=0, kind="started", status="running")
        yield ExecutionEvent(
            execution_id=handle.execution_id,
            sequence=1,
            kind="partial_result",
            status="running",
            outputs=(ExecutionOutput(name="draft", value="partial"),),
        )

    async def cancel(self, handle):
        self.cancel_calls += 1
        return CancelResult(execution_id=handle.execution_id, accepted=True, status="cancelled")

    async def status(self, handle):
        return ExecutionStatusSnapshot(execution_id=handle.execution_id, status="running")

    async def result(self, handle):
        return ExecutionResult(
            execution_id=handle.execution_id,
            status="succeeded",
            outputs=(ExecutionOutput(name="answer", value=42),),
        )

    async def cleanup(self, handle):
        self.cleaned = True

    async def health(self):
        return ExecutorHealth(executor_ref=self.executor_ref, status="healthy")


class ExecutorContractTests(unittest.IsolatedAsyncioTestCase):
    async def test_fake_executor_completes_typed_lifecycle(self):
        executor = FakeExecutor()
        self.assertIsInstance(executor, Executor)
        request = ExecutionRequest(
            execution_id="execution-1",
            idempotency_key="retry-key-1",
            inputs=(ExecutionInput(name="prompt", value="hello"),),
        )

        prepared = await executor.prepare(request)
        handle = await executor.start(prepared)
        events = [event async for event in executor.stream(handle)]
        status = await executor.status(handle)
        result = await executor.result(handle)
        health = await executor.health()
        await executor.cleanup(handle)

        self.assertEqual(handle.execution_id, request.execution_id)
        self.assertEqual([event.kind for event in events], ["started", "partial_result"])
        self.assertEqual(events[1].outputs[0].value, "partial")
        self.assertEqual(status.status, "running")
        self.assertEqual(result.outputs[0].value, 42)
        self.assertEqual(health.status, "healthy")
        self.assertTrue(executor.cleaned)

    async def test_cancellation_is_repeatable_and_explicit(self):
        executor = FakeExecutor()
        handle = ExecutionHandle(execution_id="execution-2", executor_ref=executor.executor_ref)

        first = await executor.cancel(handle)
        second = await executor.cancel(handle)

        self.assertEqual(first.status, "cancelled")
        self.assertEqual(second.status, "cancelled")
        self.assertEqual(executor.cancel_calls, 2)

    def test_request_rejects_duplicate_inputs_and_sensitive_config(self):
        with self.assertRaises(ValueError):
            ExecutionRequest(
                execution_id="execution-3",
                idempotency_key="retry-key-3",
                inputs=(ExecutionInput(name="x", value=1), ExecutionInput(name="x", value=2)),
            )
        with self.assertRaises(ValueError):
            ExecutionRequest(
                execution_id="execution-4",
                idempotency_key="retry-key-4",
                config={"api_key": "must-not-cross-contract"},
            )

    def test_failed_result_requires_error_and_success_has_no_error(self):
        with self.assertRaises(ValueError):
            ExecutionResult(execution_id="execution-5", status="failed")
        with self.assertRaises(ValueError):
            ExecutionResult(execution_id="execution-6", status="succeeded", error="wrong state")


if __name__ == "__main__":
    unittest.main()

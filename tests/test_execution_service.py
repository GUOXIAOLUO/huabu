import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

from workbench.application.execution_service import ExecutionService, ExecutionServiceError
from workbench.domain.execution import CancelResult, ExecutionAttempt, ExecutionHandle, ExecutionInputProjection, ExecutionPolicy, ExecutionRun, ExecutorHealth, ExecutionRequest, PreparedExecution, ExecutionStatusSnapshot, ExecutionResult
from workbench.domain.project.models import ProjectRecord
from workbench.repositories.execution_attempt_repository import SqliteExecutionAttemptRepository
from workbench.repositories.execution_run_repository import SqliteExecutionRunRepository
from workbench.repositories.sqlite_project_canvas_repository import SqliteProjectCanvasRepository


class FakeExecutor:
    executor_ref = "fake"

    def __init__(self, result):
        self.result = result
        self.calls = 0

    async def prepare(self, request: ExecutionRequest) -> PreparedExecution: raise NotImplementedError
    async def start(self, prepared: PreparedExecution) -> ExecutionHandle: raise NotImplementedError
    async def stream(self, handle):
        if False: yield handle
    async def cancel(self, handle):
        self.calls += 1
        return self.result
    async def status(self, handle) -> ExecutionStatusSnapshot: raise NotImplementedError
    async def result(self, handle) -> ExecutionResult: raise NotImplementedError
    async def cleanup(self, handle): return None
    async def health(self) -> ExecutorHealth: raise NotImplementedError


class ExecutionServiceTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.database = Path(self.temp.name) / "workbench.sqlite3"
        self.now = datetime(2026, 9, 12, tzinfo=UTC)
        self.projects = SqliteProjectCanvasRepository(self.database, clock=lambda: self.now)
        self.projects.create_project(ProjectRecord(id="project-1", name="Project", workspace_id="local", created_by="owner", created_at=self.now, updated_at=self.now))
        self.runs = SqliteExecutionRunRepository(self.database, clock=lambda: self.now)
        self.attempts = SqliteExecutionAttemptRepository(self.database, clock=lambda: self.now)
        self.runs.create(ExecutionRun(id="run-1", project_id="project-1", task_id="task-1", execution_profile_ref="profile@1", policy=ExecutionPolicy(mode="batch", retry=1), input_projection=ExecutionInputProjection(inputs=[]), created_at=self.now), actor_id="owner")

    def tearDown(self):
        self.temp.cleanup()

    def add_attempt(self, attempt_id="attempt-1", status="prepared", retry_count=0, attempt_number=1, item_index=0):
        attempt = ExecutionAttempt(id=attempt_id, run_id="run-1", input_id="input-1", item_index=item_index, attempt_number=attempt_number, created_at=self.now, status=status, retry_count=retry_count)
        self.attempts.create(attempt, actor_id="owner")
        return attempt

    async def test_cancel_uses_executor_contract_and_normalizes_run(self):
        attempt = self.add_attempt(status="running")
        executor = FakeExecutor(CancelResult(execution_id=attempt.id, accepted=True, status="cancelled"))
        service = ExecutionService(self.runs, self.attempts, actor_id="owner", clock=lambda: self.now)
        cancelled = await service.cancel_run("run-1", controls={attempt.id: (executor, ExecutionHandle(execution_id=attempt.id, executor_ref="fake"))})
        self.assertEqual((cancelled.status, executor.calls, self.attempts.get(attempt.id, actor_id="owner").status), ("cancelled", 1, "cancelled"))
        self.assertEqual([event["event_type"] for event in self.projects.outbox_events() if event["event_type"].startswith("execution.")][-2:], ["execution.attempt.status_updated", "execution.run.status_updated"])

    async def test_cancel_attempt_directly_normalizes_parent_run(self):
        attempt = self.add_attempt(status="running")
        executor = FakeExecutor(CancelResult(execution_id=attempt.id, accepted=True, status="cancelled"))
        service = ExecutionService(self.runs, self.attempts, actor_id="owner", clock=lambda: self.now)
        await service.cancel_attempt(attempt, executor=executor, handle=ExecutionHandle(execution_id=attempt.id, executor_ref="fake"))
        self.assertEqual(self.runs.get("run-1", actor_id="owner").status, "cancelled")

    async def test_cancel_normalizes_mixed_terminal_batch_after_active_item_is_cancelled(self):
        succeeded = self.add_attempt(attempt_id="succeeded", status="succeeded")
        cancelled = self.add_attempt(attempt_id="cancelled", status="running", attempt_number=2)
        executor = FakeExecutor(CancelResult(execution_id=cancelled.id, accepted=True, status="cancelled"))
        service = ExecutionService(self.runs, self.attempts, actor_id="owner", clock=lambda: self.now)
        result = await service.cancel_run("run-1", controls={cancelled.id: (executor, ExecutionHandle(execution_id=cancelled.id, executor_ref="fake"))})
        self.assertEqual((result.status, self.attempts.get(succeeded.id, actor_id="owner").status), ("cancelled", "succeeded"))

    async def test_cancel_normalizes_completed_batch_without_overwriting_attempt_outcomes(self):
        self.runs.update_status("run-1", status="running", expected_revision=1, actor_id="owner", started_at=self.now)
        self.add_attempt(attempt_id="succeeded", status="succeeded")
        service = ExecutionService(self.runs, self.attempts, actor_id="owner", clock=lambda: self.now)
        result = await service.cancel_run("run-1")
        self.assertEqual(result.status, "succeeded")

    async def test_cancel_normalizes_terminal_attempts_from_prepared_run(self):
        self.add_attempt(attempt_id="succeeded", status="succeeded")
        service = ExecutionService(self.runs, self.attempts, actor_id="owner", clock=lambda: self.now)
        result = await service.cancel_run("run-1")
        self.assertEqual(result.status, "succeeded")

    async def test_normalization_uses_latest_attempt_per_item_after_retry(self):
        self.add_attempt(attempt_id="failed-first", status="failed")
        self.add_attempt(attempt_id="succeeded-retry", status="succeeded", attempt_number=2)
        service = ExecutionService(self.runs, self.attempts, actor_id="owner", clock=lambda: self.now)
        result = await service.cancel_run("run-1")
        self.assertEqual(result.status, "succeeded")

    async def test_unsupported_cancel_is_explicit_and_missing_handle_is_rejected(self):
        attempt = self.add_attempt(status="running")
        service = ExecutionService(self.runs, self.attempts, actor_id="owner", clock=lambda: self.now)
        with self.assertRaisesRegex(ExecutionServiceError, "executor and handle"):
            await service.cancel_attempt(attempt)
        executor = FakeExecutor(CancelResult(execution_id=attempt.id, accepted=False, status="unknown"))
        with self.assertRaisesRegex(ExecutionServiceError, "did not accept"):
            await service.cancel_attempt(attempt, executor=executor, handle=ExecutionHandle(execution_id=attempt.id, executor_ref="fake"))
        self.assertEqual(self.attempts.get(attempt.id, actor_id="owner").status, "running")

        with self.assertRaisesRegex(ExecutionServiceError, "does not own"):
            await service.cancel_attempt(attempt, executor=executor, handle=ExecutionHandle(execution_id=attempt.id, executor_ref="other"))
        with self.assertRaisesRegex(ExecutionServiceError, "another execution"):
            await service.cancel_attempt(attempt, executor=executor, handle=ExecutionHandle(execution_id="other-execution", executor_ref="fake"))

    async def test_retry_is_bounded_and_creates_next_item_attempt(self):
        failed = self.add_attempt(status="failed")
        service = ExecutionService(self.runs, self.attempts, actor_id="owner", id_factory=lambda: "attempt-2", clock=lambda: self.now)
        retried = service.retry_failed_attempt(failed.id)
        self.assertEqual((retried.id, retried.item_index, retried.attempt_number, retried.retry_count, retried.status), ("attempt-2", 0, 2, 1, "prepared"))
        self.assertEqual(self.runs.get("run-1", actor_id="owner").revision, 2)
        with self.assertRaisesRegex(ExecutionServiceError, "only failed"):
            service.retry_failed_attempt(retried.id)
        self.attempts.update_status(retried.id, status="running", expected_revision=1, actor_id="owner")
        self.attempts.update_status(retried.id, status="failed", expected_revision=2, actor_id="owner", retry_count=1)
        with self.assertRaisesRegex(ExecutionServiceError, "retry limit"):
            service.retry_failed_attempt(retried.id)

    async def test_retry_limit_is_enforced_per_item_across_repeated_requests(self):
        failed = self.add_attempt(status="failed")
        other_item = self.add_attempt(attempt_id="attempt-other", status="failed", item_index=1)
        identifiers = iter(["attempt-2", "attempt-3"])
        service = ExecutionService(self.runs, self.attempts, actor_id="owner", id_factory=lambda: next(identifiers), clock=lambda: self.now)
        first = service.retry_failed_attempt(failed.id)
        self.assertEqual((first.id, first.attempt_number, first.retry_count), ("attempt-2", 2, 1))
        with self.assertRaisesRegex(ExecutionServiceError, "latest failed attempt"):
            service.retry_failed_attempt(failed.id)
        self.assertEqual([item.id for item in self.attempts.list("run-1", actor_id="owner") if item.item_index == 0], ["attempt-1", "attempt-2"])
        self.attempts.update_status(first.id, status="running", expected_revision=1, actor_id="owner")
        self.attempts.update_status(first.id, status="failed", expected_revision=2, actor_id="owner")
        with self.assertRaisesRegex(ExecutionServiceError, "retry limit"):
            service.retry_failed_attempt(first.id)
        retried_other = service.retry_failed_attempt(other_item.id)
        self.assertEqual((retried_other.id, retried_other.item_index, retried_other.retry_count), ("attempt-3", 1, 1))
        self.attempts.update_status(retried_other.id, status="running", expected_revision=1, actor_id="owner")
        self.attempts.update_status(retried_other.id, status="failed", expected_revision=2, actor_id="owner")
        with self.assertRaisesRegex(ExecutionServiceError, "retry limit"):
            service.retry_failed_attempt(retried_other.id)

    async def test_retry_rejects_terminal_run_without_creating_orphan_attempt(self):
        failed = self.add_attempt(status="failed")
        self.runs.update_status("run-1", status="cancelled", expected_revision=1, actor_id="owner", finished_at=self.now)
        service = ExecutionService(self.runs, self.attempts, actor_id="owner", id_factory=lambda: "orphan", clock=lambda: self.now)
        with self.assertRaisesRegex(ExecutionServiceError, "terminal execution runs"):
            service.retry_failed_attempt(failed.id)
        self.assertEqual([item.id for item in self.attempts.list("run-1", actor_id="owner")], [failed.id])

    async def test_retry_requeues_a_failed_run_for_explicit_manual_retry(self):
        failed = self.add_attempt(status="failed")
        service = ExecutionService(self.runs, self.attempts, actor_id="owner", id_factory=lambda: "retry-after-failure", clock=lambda: self.now)
        self.runs.update_status("run-1", status="failed", expected_revision=1, actor_id="owner", finished_at=self.now)
        retried = service.retry_failed_attempt(failed.id)
        requeued = self.runs.get("run-1", actor_id="owner")
        self.assertEqual((retried.status, requeued.status, requeued.finished_at), ("prepared", "queued", None))

    async def test_retry_only_allows_the_latest_failed_attempt_for_an_item(self):
        failed = self.add_attempt(status="failed")
        self.add_attempt(attempt_id="newer", status="succeeded", attempt_number=2)
        service = ExecutionService(self.runs, self.attempts, actor_id="owner", id_factory=lambda: "orphan", clock=lambda: self.now)
        with self.assertRaisesRegex(ExecutionServiceError, "latest failed attempt"):
            service.retry_failed_attempt(failed.id)


if __name__ == "__main__":
    unittest.main()

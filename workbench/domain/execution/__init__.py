"""Provider-neutral execution contracts."""

from .contract import (
    EXECUTOR_CONTRACT_VERSION,
    CancelResult,
    ExecutionEvent,
    ExecutionHandle,
    ExecutionInput,
    ExecutionOutput,
    ExecutionRequest,
    ExecutionResult,
    ExecutionStatus,
    ExecutionStatusSnapshot,
    Executor,
    ExecutorHealth,
    ExecutorHealthStatus,
    PreparedExecution,
)
from .profile import (
    EXECUTION_PROFILE_REF_SCHEMA_VERSION,
    EXECUTION_PROFILE_SCHEMA_VERSION,
    ExecutionProfile,
    ExecutionProfileRef,
)
from .policy import EXECUTION_POLICY_SCHEMA_VERSION, ExecutionMode, ExecutionOrder, ExecutionPolicy
from .input_projection import EXECUTION_INPUT_PROJECTION_SCHEMA_VERSION, ExecutionInputProjection, ProjectedExecutionInput, ProjectionError
from .run import EXECUTION_RUN_SCHEMA_VERSION, EXECUTION_RUN_TRANSITIONS, ExecutionRun, ExecutionRunStatus
from .attempt import EXECUTION_ATTEMPT_SCHEMA_VERSION, ExecutionAttempt, ExecutionAttemptStatus
from .event import EXECUTION_EVENT_SCHEMA_VERSION, ExecutionEventRecord, ExecutionEventType
from .selection import (
    EXECUTION_RESULT_SELECTION_SCHEMA_VERSION,
    RESULT_SELECTION_MAX_COMMENT_LENGTH,
    RESULT_SELECTION_MAX_RATING,
    RESULT_SELECTION_MIN_RATING,
    ResultSelection,
)
from .branch import (
    EXECUTION_BRANCH_SCHEMA_VERSION,
    ExecutionBranch,
    ExecutionBranchKind,
)
from .result_identity import (
    EXECUTION_RESULT_IDENTITY_SCHEMA_VERSION,
    ExecutionResultIdentity,
)

__all__ = [
    "EXECUTOR_CONTRACT_VERSION",
    "CancelResult",
    "ExecutionEvent",
    "ExecutionHandle",
    "ExecutionInput",
    "ExecutionOutput",
    "ExecutionRequest",
    "ExecutionResult",
    "ExecutionStatus",
    "ExecutionStatusSnapshot",
    "Executor",
    "ExecutorHealth",
    "ExecutorHealthStatus",
    "PreparedExecution",
    "EXECUTION_PROFILE_REF_SCHEMA_VERSION",
    "EXECUTION_PROFILE_SCHEMA_VERSION",
    "ExecutionProfile",
    "ExecutionProfileRef",
    "EXECUTION_POLICY_SCHEMA_VERSION",
    "ExecutionMode",
    "ExecutionOrder",
    "ExecutionPolicy",
    "EXECUTION_INPUT_PROJECTION_SCHEMA_VERSION",
    "ExecutionInputProjection",
    "ProjectedExecutionInput",
    "ProjectionError",
    "EXECUTION_RUN_SCHEMA_VERSION",
    "EXECUTION_RUN_TRANSITIONS",
    "ExecutionRun",
    "ExecutionRunStatus",
    "EXECUTION_ATTEMPT_SCHEMA_VERSION",
    "ExecutionAttempt",
    "ExecutionAttemptStatus",
    "EXECUTION_EVENT_SCHEMA_VERSION",
    "ExecutionEventRecord",
    "ExecutionEventType",
    "EXECUTION_RESULT_SELECTION_SCHEMA_VERSION",
    "RESULT_SELECTION_MAX_COMMENT_LENGTH",
    "RESULT_SELECTION_MAX_RATING",
    "RESULT_SELECTION_MIN_RATING",
    "ResultSelection",
    "EXECUTION_BRANCH_SCHEMA_VERSION",
    "ExecutionBranch",
    "ExecutionBranchKind",
    "EXECUTION_RESULT_IDENTITY_SCHEMA_VERSION",
    "ExecutionResultIdentity",
]

"""Small, version-pinned stdio boundary for Codex App Server.

Raw JSONL protocol details remain here so future application code depends on
``CodexBridge`` rather than the Codex App Server protocol.
"""

from __future__ import annotations

import asyncio
import json
import re
import os
import shutil
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Awaitable, Callable, Mapping

from .protocol import (
    CodexProtocolCompatibility,
    CodexProtocolError,
    ConfigReadParams,
    ConfigReadResult,
    EmptyParams,
    EmptyResult,
    InitializeParams,
    InitializeResult,
    ModelListResult,
    ProtocolModel,
    ProtocolNotification,
    ProtocolRequest,
    ProtocolResponse,
    ProtocolServerRequest,
    ThreadResumeParams,
    ThreadStartParams,
    ThreadStartResult,
    TurnInterruptParams,
    TurnStartParams,
    TurnStartResult,
    parse_server_message,
)
from .events import CodexEventNormalizer, RuntimeEvent


CODEX_APP_SERVER_PROTOCOL = "v2"
CODEX_APP_SERVER_TESTED_VERSION = "0.153.1"
CODEX_EVENT_QUEUE_MAXSIZE = 256
_RETRYABLE_REQUESTS = frozenset({"initialize", "thread/resume", "model/list", "config/read"})


class CodexBridgeError(RuntimeError):
    """A local transport, protocol, or launch-policy failure."""


@dataclass(frozen=True)
class HarnessLaunchPolicy:
    """R1's deliberately restrictive process and turn policy."""

    workspace_root: Path
    executable: str = "codex"
    arguments: tuple[str, ...] = ("app-server",)
    timeout_seconds: float = 30.0
    max_request_attempts: int = 2
    retry_backoff_seconds: float = 0.05
    max_retry_backoff_seconds: float = 1.0
    allowed_environment: frozenset[str] = frozenset(
        {"PATH", "HOME", "CODEX_HOME", "TMPDIR", "LANG", "LC_ALL", "TERM", "USER", "LOGNAME", "SHELL"}
    )

    def __post_init__(self) -> None:
        if self.timeout_seconds <= 0:
            raise ValueError("Codex timeout_seconds must be positive")
        if self.max_request_attempts < 1:
            raise ValueError("Codex max_request_attempts must be at least one")
        if self.retry_backoff_seconds < 0 or self.max_retry_backoff_seconds < 0:
            raise ValueError("Codex retry backoff must not be negative")
        if self.max_retry_backoff_seconds < self.retry_backoff_seconds:
            raise ValueError("Codex max retry backoff must cover the initial backoff")

    def request_attempts(self, method: str) -> int:
        return self.max_request_attempts if method in _RETRYABLE_REQUESTS else 1

    def retry_delay(self, attempt: int) -> float:
        return min(self.max_retry_backoff_seconds, self.retry_backoff_seconds * (2 ** (attempt - 1)))

    def resolve_cwd(self, cwd: str | Path | None = None) -> Path:
        root = self.workspace_root.resolve()
        candidate = Path(cwd or root).resolve()
        try:
            candidate.relative_to(root)
        except ValueError as exc:
            raise CodexBridgeError("Codex working directory escapes the configured workspace") from exc
        return candidate

    def environment(self, source: Mapping[str, str] | None = None) -> dict[str, str]:
        source = source or os.environ
        return {key: source[key] for key in self.allowed_environment if source.get(key)}

    def command(self) -> list[str]:
        executable = shutil.which(self.executable) if os.path.sep not in self.executable else self.executable
        if not executable:
            raise CodexBridgeError("Codex CLI executable was not found")
        return [executable, *self.arguments]

    def thread_options(self, cwd: str | Path | None = None) -> dict[str, Any]:
        return {
            "cwd": str(self.resolve_cwd(cwd)),
            "approvalPolicy": "never",
            "sandbox": "read-only",
        }

    def turn_options(self, cwd: str | Path | None = None) -> dict[str, Any]:
        return {
            "cwd": str(self.resolve_cwd(cwd)),
            "approvalPolicy": "never",
            "sandboxPolicy": {"type": "readOnly", "networkAccess": False},
        }


class CodexBridge:
    """Async JSONL client for the version-pinned App Server v2 protocol."""

    def __init__(self, policy: HarnessLaunchPolicy):
        self.policy = policy
        self._process: asyncio.subprocess.Process | None = None
        self._next_id = 1
        self.events: asyncio.Queue[RuntimeEvent] = asyncio.Queue(maxsize=CODEX_EVENT_QUEUE_MAXSIZE)
        self._dropped_events = 0
        self._dropped_important_events = 0
        self._pending: dict[int, asyncio.Future[ProtocolResponse]] = {}
        self._reader_task: asyncio.Task[None] | None = None
        self._stderr_task: asyncio.Task[None] | None = None
        self._stderr_diagnostics: deque[str] = deque(maxlen=200)

    @property
    def running(self) -> bool:
        return self._process is not None and self._process.returncode is None

    async def start(self) -> InitializeResult:
        if self.running:
            return await self.health()
        self._process = await asyncio.create_subprocess_exec(
            *self.policy.command(),
            cwd=str(self.policy.resolve_cwd()),
            env=self.policy.environment(),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        self._reader_task = asyncio.create_task(self._read_messages())
        self._stderr_task = asyncio.create_task(self._drain_stderr(self._process.stderr))
        result = await self._request_result(
            InitializeResult,
            "initialize",
            InitializeParams(
                clientInfo={"name": "ai-workbench", "version": "r1"}, capabilities={}
            ),
        )
        try:
            CodexProtocolCompatibility.validate_initialize(result)
        except CodexProtocolError as exc:
            raise CodexBridgeError(str(exc)) from exc
        await self.notify("initialized", EmptyParams())
        return result

    async def health(self) -> Mapping[str, Any]:
        return {
            "running": self.running,
            "protocol": CODEX_APP_SERVER_PROTOCOL,
            "tested_codex_cli": CODEX_APP_SERVER_TESTED_VERSION,
            "pid": self._process.pid if self._process else None,
        }

    async def create_thread(self, cwd: str | Path | None = None) -> ThreadStartResult:
        return await self._request_result(
            ThreadStartResult, "thread/start", ThreadStartParams.model_validate(self.policy.thread_options(cwd))
        )

    async def resume_thread(self, thread_id: str, cwd: str | Path | None = None) -> ThreadStartResult:
        return await self._request_result(
            ThreadStartResult,
            "thread/resume",
            ThreadResumeParams.model_validate({"threadId": thread_id, **self.policy.thread_options(cwd)}),
        )

    async def start_turn(self, thread_id: str, text: str, cwd: str | Path | None = None) -> TurnStartResult:
        return await self._request_result(
            TurnStartResult,
            "turn/start",
            TurnStartParams.model_validate(
                {"threadId": thread_id, "input": [{"type": "text", "text": text}], **self.policy.turn_options(cwd)}
            ),
        )

    async def interrupt_turn(self, thread_id: str, turn_id: str) -> EmptyResult:
        return await self._request_result(
            EmptyResult, "turn/interrupt", TurnInterruptParams(threadId=thread_id, turnId=turn_id)
        )

    async def list_models(self) -> ModelListResult:
        return await self._request_result(ModelListResult, "model/list", EmptyParams())

    async def read_config(self, cwd: str | Path | None = None) -> ConfigReadResult:
        return await self._request_result(
            ConfigReadResult,
            "config/read",
            ConfigReadParams(cwd=str(self.policy.resolve_cwd(cwd)), includeLayers=True),
        )

    async def request(self, method: str, params: ProtocolModel) -> ProtocolResponse:
        if not self.running or not self._process or not self._process.stdin:
            raise CodexBridgeError("Codex App Server is not running")
        max_attempts = self.policy.request_attempts(method)
        for attempt in range(1, max_attempts + 1):
            request_id = self._next_id
            self._next_id += 1
            future: asyncio.Future[ProtocolResponse] = asyncio.get_running_loop().create_future()
            self._pending[request_id] = future
            request = ProtocolRequest(
                id=request_id,
                method=method,
                params=params.model_dump(by_alias=True, exclude_none=True),
            )
            try:
                await self._send(request)
                return await asyncio.wait_for(future, timeout=self.policy.timeout_seconds)
            except asyncio.TimeoutError as exc:
                self._pending.pop(request_id, None)
                if attempt < max_attempts:
                    await asyncio.sleep(self.policy.retry_delay(attempt))
                    continue
                self._publish_event(
                    CodexEventNormalizer.error(
                        "request-timeout",
                        {"method": method, "attempts": attempt, "timeout_seconds": self.policy.timeout_seconds},
                        protocol_method=method,
                    )
                )
                raise CodexBridgeError(
                    f"Codex request timed out: {method} after {attempt} attempt(s)"
                ) from exc
            finally:
                self._pending.pop(request_id, None)
        raise AssertionError("Codex request loop exhausted without a result")

    async def notify(self, method: str, params: ProtocolModel) -> None:
        await self._send(ProtocolNotification(method=method, params=params.model_dump(by_alias=True, exclude_none=True)))

    async def _request_result(self, result_type: type[Any], method: str, params: ProtocolModel) -> Any:
        response = await self.request(method, params)
        if response.error is not None:
            raise CodexBridgeError(str(response.error))
        try:
            return result_type.model_validate(response.result or {})
        except ValueError as exc:
            raise CodexBridgeError(f"invalid {method} response: {exc}") from exc

    async def shutdown(self) -> None:
        process, self._process = self._process, None
        tasks = [task for task in (self._reader_task, self._stderr_task) if task]
        self._reader_task = None
        self._stderr_task = None
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        if process and process.returncode is None:
            process.terminate()
            try:
                await asyncio.wait_for(process.wait(), timeout=self.policy.timeout_seconds)
            except TimeoutError:
                process.kill()
                await process.wait()
        for future in self._pending.values():
            if not future.done():
                future.set_exception(CodexBridgeError("Codex App Server stopped"))
        self._pending.clear()

    async def recover(self) -> InitializeResult:
        await self.shutdown()
        return await self.start()

    async def _send(self, message: ProtocolModel) -> None:
        if not self._process or not self._process.stdin:
            raise CodexBridgeError("Codex App Server stdin is unavailable")
        payload = message.model_dump(by_alias=True, exclude_none=True)
        self._process.stdin.write((json.dumps(payload, separators=(",", ":")) + "\n").encode())
        await self._process.stdin.drain()

    async def _read_messages(self) -> None:
        assert self._process and self._process.stdout
        while line := await self._process.stdout.readline():
            try:
                message = parse_server_message(line)
            except CodexProtocolError as exc:
                self._publish_event(
                    CodexEventNormalizer.error("invalid-message", {"error": str(exc)}, protocol_method="unknown")
                )
                continue
            if isinstance(message, ProtocolResponse):
                if (future := self._pending.get(message.id)) and not future.done():
                    if message.error is not None:
                        future.set_exception(CodexBridgeError(str(message.error)))
                    else:
                        future.set_result(message)
                continue
            method = message.method
            self._publish_event(CodexEventNormalizer.normalize(method, message.params))
            # R1 has no approval UI or mutation authority. Any server request is denied.
            if isinstance(message, ProtocolServerRequest):
                await self._send(ProtocolResponse(id=message.id, result={"decision": "decline"}))
        error = CodexBridgeError("Codex App Server exited unexpectedly (stdout EOF)")
        self._fail_pending(error)
        self._publish_event(CodexEventNormalizer.error("unexpected-eof", {"error": str(error)}, protocol_method="transport"))

    def _publish_event(self, event: RuntimeEvent) -> None:
        """Publish without allowing a notification storm to block the reader."""
        important = self._is_important(event)
        normal_limit = max(0, self.events.maxsize - 1)
        if not important and self.events.qsize() >= normal_limit:
            self._dropped_events += 1
            return
        try:
            self.events.put_nowait(self._with_drop_count(event) if important else event)
        except asyncio.QueueFull:
            if not important:
                self._dropped_events += 1
                return
            # Critical events must not evict another critical event. Rebuild the
            # small in-memory queue around the oldest ordinary event instead.
            buffered: list[RuntimeEvent] = []
            while not self.events.empty():
                buffered.append(self.events.get_nowait())
            evicted = next((index for index, item in enumerate(buffered) if not self._is_important(item)), None)
            if evicted is None:
                self._dropped_important_events += 1
                for item in buffered:
                    self.events.put_nowait(item)
                return
            buffered.pop(evicted)
            self._dropped_events += 1
            for item in buffered:
                self.events.put_nowait(item)
            self.events.put_nowait(self._with_drop_count(event))

    def _with_drop_count(self, event: RuntimeEvent) -> RuntimeEvent:
        if not self._dropped_events:
            return event
        return RuntimeEvent(
            event.kind,
            event.status,
            event.operation,
            {**dict(event.payload), "dropped_events": self._dropped_events},
            event.diagnostic_ref,
        )

    @staticmethod
    def _is_important(event: RuntimeEvent) -> bool:
        return event.kind in {"error", "approval"} or event.status in {"completed", "failed", "cancelled"}

    def event_queue_stats(self) -> dict[str, int]:
        """Return bounded queue state and explicit overflow accounting."""
        return {
            "maxsize": self.events.maxsize,
            "size": self.events.qsize(),
            "dropped": self._dropped_events,
            "dropped_important": self._dropped_important_events,
        }

    def _fail_pending(self, error: CodexBridgeError) -> None:
        for future in self._pending.values():
            if not future.done():
                future.set_exception(error)
        self._pending.clear()

    async def _drain_stderr(self, stream: asyncio.StreamReader | None) -> None:
        if stream is None:
            return
        while line := await stream.readline():
            diagnostic = self._sanitize_stderr(line.decode(errors="replace"))
            if diagnostic:
                self._stderr_diagnostics.append(diagnostic)

    @staticmethod
    def _sanitize_stderr(value: str) -> str:
        bounded = value.strip()[:4096]
        return re.sub(
            r"(?i)(api[_-]?key|token|password|secret)\s*[:=]\s*[^\s,;]+",
            r"\1=<redacted>",
            bounded,
        )

    def stderr_diagnostics(self) -> tuple[str, ...]:
        """Return bounded, redacted stderr diagnostics retained from the child."""
        return tuple(self._stderr_diagnostics)

class CodexExecCompatibilityAdapter:
    """Keeps existing ``codex exec`` callers outside the App Server bridge."""

    def __init__(self, runner: Callable[..., Awaitable[Any]]):
        self._runner = runner

    async def run(self, prompt: str, **options: Any) -> Any:
        return await self._runner(prompt, **options)

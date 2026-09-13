"""Focused tests for the R8-15 MCP executor contract.

The DoD is "Generic contract is testable with a fake MCP server/client", so
these tests drive the seam through an in-process fake MCP peer that speaks MCP
semantics (capability catalog, deterministic action per capability kind,
``isError`` reported inside a successful response, JSON-RPC error codes) rather
than through a bare transport stub.
"""

import ast
import asyncio
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

from workbench.application.execution_event_service import ExecutionEventService
from workbench.application.execution_service import ExecutionService
from workbench.application.executor_registry import ExecutorRegistration, ExecutorRegistry
from workbench.domain.execution import (
    ExecutionHandle,
    ExecutionInput,
    ExecutionInputProjection,
    ExecutionPolicy,
    ExecutionProfile,
    ExecutionRequest,
    ExecutionRun,
    Executor,
)
from workbench.domain.project.models import ProjectRecord
from workbench.mcp import (
    CAPABILITY_ACTIONS,
    MCP_EXECUTOR_REF,
    MCPCall,
    MCPCapability,
    MCPCapabilityRef,
    MCPExecutor,
    MCPExecutorError,
    MCPInputBinding,
    MCPOutputItem,
    MCPRawEvent,
    MCPSubmission,
    MCPTransport,
    MCPTransportError,
)
from workbench.repositories.execution_attempt_repository import SqliteExecutionAttemptRepository
from workbench.repositories.execution_event_repository import SqliteExecutionEventRepository
from workbench.repositories.execution_run_repository import SqliteExecutionRunRepository
from workbench.repositories.sqlite_project_canvas_repository import SqliteProjectCanvasRepository


FORBIDDEN_PROVIDER_SDK_IMPORTS = (
    "openai",
    "anthropic",
    "httpx",
    "requests",
    "boto3",
    "cohere",
    "replicate",
    "together",
    "mistralai",
    "google.generativeai",
    "urllib",
    "http.client",
    "socket",
    "websockets",
    "subprocess",
)
# An MCP client library is transport, so it belongs to the adapter, not the seam.
FORBIDDEN_MCP_CLIENT_IMPORTS = ("mcp", "fastmcp", "mcp.client", "modelcontextprotocol")
# DoD: MCP must be an executor route, not a Canvas runtime owner.
FORBIDDEN_BOUNDARY_MARKERS = ("canvas", "legacy")


def _imported_modules(path: Path, root: Path) -> set[str]:
    """Absolute dotted module names referenced by imports in one file."""
    package_parts = path.parent.relative_to(root).parts
    modules: set[str] = set()
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
            if node.level:
                base = package_parts[: len(package_parts) - (node.level - 1)] if node.level > 1 else package_parts
                modules.add(".".join([*base, node.module]))
    return modules


class MCPToolError(Exception):
    """A capability-level failure, reported by MCP inside a successful reply."""

    def __init__(self, code: int, message: str):
        self.code = code
        super().__init__(message)


class FakeMCPServer:
    """A minimal in-process MCP peer: capability catalog plus JSON-RPC replies."""

    def __init__(self, capabilities=()):
        self.capabilities = {capability.ref.ref: capability for capability in capabilities}
        self.handlers = {}
        self.dispatched: list[MCPCall] = []

    def register(self, capability, handler=None):
        self.capabilities[capability.ref.ref] = capability
        if handler is not None:
            self.handlers[capability.ref.ref] = handler
        return self

    def dispatch(self, call: MCPCall) -> list[MCPRawEvent]:
        """Translate one call into MCP-shaped raw events."""
        self.dispatched.append(call)
        key = call.capability_ref
        capability = self.capabilities.get(key)
        if capability is None:
            return [MCPRawEvent(kind="completed", is_error=True, error_code=-32601, message=f"capability not found: {key}")]
        if capability.action != call.action:
            return [MCPRawEvent(kind="completed", is_error=True, error_code=-32602, message=f"action mismatch for {key}")]
        handler = self.handlers.get(key)
        if handler is None:
            return [MCPRawEvent(kind="accepted"), MCPRawEvent(kind="completed", items=(MCPOutputItem(kind="text", text=key),))]
        try:
            produced = list(handler(call.arguments))
        except MCPToolError as error:
            # MCP reports a failed call inside a successful response.
            return [MCPRawEvent(kind="completed", is_error=True, error_code=error.code, message=str(error))]
        return [MCPRawEvent(kind="accepted"), *produced]


class FakeMCPClient:
    """An MCPTransport implementation backed by the fake server."""

    def __init__(self, server: FakeMCPServer, *, accept_cancel=True, hang=False, fail_invoke=False, fail_stream=False, script=None):
        self.server = server
        self.accept_cancel = accept_cancel
        self.hang = hang
        self.fail_invoke = fail_invoke
        self.fail_stream = fail_stream
        self.script = list(script) if script is not None else None
        self.release = asyncio.Event()
        self.calls: list[MCPCall] = []
        self.cancel_calls = 0
        self.closed = 0
        self._queue: list[MCPRawEvent] = []

    async def invoke(self, call):
        self.calls.append(call)
        if self.fail_invoke:
            raise MCPTransportError("mcp server refused the invocation")
        self._queue = list(self.script) if self.script is not None else list(self.server.dispatch(call))
        return MCPSubmission(invocation_id=f"invocation-{len(self.calls)}")

    async def next_event(self, submission):
        if self.hang:
            await self.release.wait()
        if self.fail_stream:
            raise MCPTransportError("mcp server stream failed")
        if not self._queue:
            return None
        return self._queue.pop(0)

    async def cancel(self, submission):
        self.cancel_calls += 1
        return self.accept_cancel

    async def close(self, submission):
        self.closed += 1


def sample_capability(**overrides):
    payload = {
        "kind": "tool",
        "name": "search",
        "title": "Search",
        "input_bindings": (
            MCPInputBinding(role="query", argument="q"),
            MCPInputBinding(role="limit", argument="limit", required=False),
        ),
    }
    payload.update(overrides)
    return MCPCapability(**payload)


class MCPCapabilityContractTests(unittest.TestCase):
    def test_capability_reference_rules_are_strict(self):
        self.assertEqual(MCPCapabilityRef.parse("tool:search").ref, "tool:search")
        self.assertEqual(MCPCapabilityRef.parse("resource:file:///notes.md").ref, "resource:file:///notes.md")
        self.assertEqual(MCPCapabilityRef.parse({"kind": "prompt", "name": "summarize"}).ref, "prompt:summarize")
        with self.assertRaises(ValueError):
            MCPCapabilityRef.parse("search")
        with self.assertRaises(ValueError):
            MCPCapabilityRef.parse("other:search")
        with self.assertRaises(ValueError):
            MCPCapabilityRef.parse("tool:")
        with self.assertRaises(ValueError):
            MCPCapabilityRef.parse({"kind": "tool"})
        with self.assertRaises(ValueError):
            MCPCapabilityRef.parse({"kind": "other", "name": "search"})
        with self.assertRaises(ValueError):
            MCPCapabilityRef.parse(7)

    def test_capability_kind_maps_to_exactly_one_action(self):
        self.assertEqual(dict(CAPABILITY_ACTIONS), {"tool": "call_tool", "prompt": "get_prompt", "resource": "read_resource"})
        self.assertEqual(sample_capability(kind="tool").action, "call_tool")
        self.assertEqual(sample_capability(kind="prompt", name="summarize").action, "get_prompt")
        self.assertEqual(sample_capability(kind="resource", name="notes").action, "read_resource")

    def test_call_cannot_carry_an_action_that_disagrees_with_its_kind(self):
        base = {
            "execution_id": "execution-1",
            "idempotency_key": "idempotency-1",
            "capability_kind": "tool",
            "capability_name": "search",
        }
        self.assertEqual(MCPCall(**base, action="call_tool").capability_ref, "tool:search")
        with self.assertRaises(ValueError):
            MCPCall(**base, action="read_resource")

    def test_capability_rejects_duplicate_roles_and_arguments(self):
        with self.assertRaises(ValueError):
            sample_capability(input_bindings=(
                MCPInputBinding(role="query", argument="q"),
                MCPInputBinding(role="query", argument="q2"),
            ))
        with self.assertRaises(ValueError):
            sample_capability(input_bindings=(
                MCPInputBinding(role="query", argument="q"),
                MCPInputBinding(role="other", argument="q"),
            ))

    def test_call_rejects_credential_parameters_but_allows_argument_payload(self):
        base = {
            "execution_id": "execution-1",
            "idempotency_key": "idempotency-1",
            "capability_kind": "tool",
            "capability_name": "search",
            "action": "call_tool",
        }
        with self.assertRaises(ValueError):
            MCPCall(**base, parameters={"api_key": "must-not-cross-the-boundary"})
        # A capability may legitimately declare such an argument name; only the
        # profile/config passthrough is scanned.
        self.assertEqual(MCPCall(**base, arguments={"api_key": "tool-declared"}).arguments["api_key"], "tool-declared")


class MCPExecutorRouteTests(unittest.IsolatedAsyncioTestCase):
    def executor(self, *, capability=None, client=None, profile=None, timeout_seconds=1.0):
        resolved = capability if capability is not None else sample_capability()
        self.client = client if client is not None else FakeMCPClient(FakeMCPServer((resolved,)))
        budgets = {} if profile is not None else {"timeout_seconds": timeout_seconds, "cancel_timeout_seconds": 0.1}
        return MCPExecutor(
            transport=self.client,
            capability_resolver=lambda ref: resolved if ref.ref == resolved.ref.ref else None,
            profile=profile,
            **budgets,
        )

    def request(self, **overrides):
        payload = {
            "execution_id": "execution-1",
            "idempotency_key": "idempotency-1",
            "inputs": (ExecutionInput(name="query", value="garden lights"),),
            "config": {"capability_ref": "tool:search"},
        }
        payload.update(overrides)
        return ExecutionRequest(**payload)

    async def test_connection_capability_and_action_are_resolved(self):
        profile = ExecutionProfile(
            id="profile-mcp", version=1, name="MCP", executor_ref=MCP_EXECUTOR_REF,
            runtime_connection_ref="mcp-server-1", default_params={"capability_ref": "tool:search"},
        )
        executor = self.executor(profile=profile)
        request = self.request(execution_profile_ref="profile-mcp@1", config={})

        prepared = await executor.prepare(request)
        handle = await executor.start(prepared)
        call = self.client.calls[0]

        self.assertEqual(prepared.executor_ref, MCP_EXECUTOR_REF)
        self.assertEqual((call.capability_ref, call.action), ("tool:search", "call_tool"))
        self.assertEqual(call.connection_ref, "mcp-server-1")
        self.assertEqual(call.arguments, {"q": "garden lights"})
        self.assertEqual(prepared.metadata["capability_ref"], "tool:search")
        self.assertEqual(prepared.metadata["action"], "call_tool")
        self.assertEqual(prepared.metadata["connection_ref"], "mcp-server-1")
        self.assertEqual(prepared.metadata["requested_connection_ref"], "mcp-server-1")
        self.assertEqual(prepared.metadata["connection_source"], "request")
        self.assertEqual(prepared.metadata["input_roles"], ("query", "limit"))
        self.assertEqual(handle.execution_id, request.execution_id)

    async def test_the_execution_profile_connection_outranks_a_capability_declaration(self):
        declared = sample_capability(connection_ref="capability-declared-server")
        profile = ExecutionProfile(
            id="profile-mcp", version=1, name="MCP", executor_ref=MCP_EXECUTOR_REF,
            runtime_connection_ref="profile-configured-server", default_params={"capability_ref": "tool:search"},
        )
        executor = self.executor(capability=declared, profile=profile)
        prepared = await executor.prepare(self.request(execution_profile_ref="profile-mcp@1", config={}))
        await executor.start(prepared)

        self.assertEqual(self.client.calls[0].connection_ref, "profile-configured-server")
        self.assertEqual(prepared.metadata["requested_connection_ref"], "profile-configured-server")
        self.assertEqual(prepared.metadata["connection_source"], "request")

    async def test_a_capability_declared_connection_only_fills_an_unspecified_request(self):
        declared = sample_capability(connection_ref="capability-declared-server")
        executor = self.executor(capability=declared)
        prepared = await executor.prepare(self.request())
        await executor.start(prepared)

        self.assertEqual(self.client.calls[0].connection_ref, "capability-declared-server")
        self.assertEqual(prepared.metadata["connection_ref"], "capability-declared-server")
        self.assertEqual(prepared.metadata["requested_connection_ref"], "")
        self.assertEqual(prepared.metadata["connection_source"], "capability")

    async def test_an_explicit_call_connection_outranks_the_profile_and_the_capability(self):
        declared = sample_capability(connection_ref="capability-declared-server")
        profile = ExecutionProfile(
            id="profile-mcp", version=1, name="MCP", executor_ref=MCP_EXECUTOR_REF,
            runtime_connection_ref="profile-configured-server", default_params={"capability_ref": "tool:search"},
        )
        executor = self.executor(capability=declared, profile=profile)
        prepared = await executor.prepare(self.request(
            execution_profile_ref="profile-mcp@1",
            config={"capability_ref": "tool:search", "connection_ref": "call-declared-server"},
        ))
        await executor.start(prepared)

        self.assertEqual(self.client.calls[0].connection_ref, "call-declared-server")
        self.assertEqual(prepared.metadata["requested_connection_ref"], "call-declared-server")
        self.assertEqual(prepared.metadata["connection_source"], "request")

    async def test_missing_capability_reference_is_rejected(self):
        executor = self.executor()

        with self.assertRaises(MCPExecutorError) as caught:
            await executor.prepare(self.request(config={}))
        self.assertIn("capability reference", str(caught.exception))
        self.assertEqual(self.client.calls, [])

    async def test_unknown_capability_is_rejected(self):
        executor = self.executor()

        with self.assertRaises(MCPExecutorError) as caught:
            await executor.prepare(self.request(config={"capability_ref": "tool:unknown"}))
        self.assertIn("not available", str(caught.exception))

    async def test_capability_reference_mismatch_is_not_substituted(self):
        for wrong in (sample_capability(name="other"), sample_capability(kind="prompt")):
            executor = MCPExecutor(
                transport=FakeMCPClient(FakeMCPServer()),
                capability_resolver=lambda ref, wrong=wrong: wrong,
                timeout_seconds=1.0,
                cancel_timeout_seconds=0.1,
            )
            with self.assertRaises(MCPExecutorError) as caught:
                await executor.prepare(self.request())
            self.assertIn("mismatch", str(caught.exception))

    async def test_unknown_role_and_missing_required_role_are_rejected(self):
        executor = self.executor()

        with self.assertRaises(MCPExecutorError) as caught:
            await executor.prepare(self.request(inputs=(ExecutionInput(name="caption", value="x"),)))
        self.assertIn("no argument binding for role", str(caught.exception))

        with self.assertRaises(MCPExecutorError) as caught:
            await executor.prepare(self.request(inputs=(ExecutionInput(name="limit", value=3),)))
        self.assertIn("missing required input role", str(caught.exception))

    async def test_declared_input_roles_map_onto_arguments(self):
        executor = self.executor()
        request = self.request(
            inputs=(ExecutionInput(name="input-1", value="a cat"), ExecutionInput(name="input-2", value=5)),
            config={"capability_ref": "tool:search", "input_roles": {"input-1": "query", "input-2": "limit"}},
        )

        await executor.start(await executor.prepare(request))

        self.assertEqual(self.client.calls[0].arguments, {"q": "a cat", "limit": 5})

    async def test_prompt_and_resource_capabilities_use_their_own_actions(self):
        prompt = sample_capability(kind="prompt", name="summarize", input_bindings=(MCPInputBinding(role="text", argument="text"),))
        executor = self.executor(capability=prompt)
        await executor.start(await executor.prepare(self.request(
            inputs=(ExecutionInput(name="text", value="long body"),),
            config={"capability_ref": "prompt:summarize"},
        )))
        self.assertEqual((self.client.calls[0].action, self.client.calls[0].arguments), ("get_prompt", {"text": "long body"}))

        resource = sample_capability(kind="resource", name="notes", input_bindings=())
        executor = self.executor(capability=resource)
        await executor.start(await executor.prepare(self.request(
            inputs=(), config={"capability_ref": "resource:notes"},
        )))
        self.assertEqual((self.client.calls[0].action, self.client.calls[0].arguments), ("read_resource", {}))

    async def test_integration_reference_is_carried_opaquely(self):
        executor = self.executor()
        prepared = await executor.prepare(self.request(config={"capability_ref": "tool:search", "integration_ref": "integration-7"}))
        await executor.start(prepared)
        self.assertEqual((self.client.calls[0].integration_ref, prepared.metadata["integration_ref"]), ("integration-7", "integration-7"))

        declared = sample_capability(integration_ref="integration-9")
        executor = self.executor(capability=declared)
        await executor.start(await executor.prepare(self.request()))
        self.assertEqual(self.client.calls[0].integration_ref, "integration-9")

        executor = self.executor()
        await executor.start(await executor.prepare(self.request()))
        self.assertIsNone(self.client.calls[0].integration_ref)

    async def test_progress_and_result_events_are_normalized(self):
        def handler(arguments):
            return [
                MCPRawEvent(kind="progress", message=f"searching {arguments['q']}"),
                MCPRawEvent(kind="completed", items=(
                    MCPOutputItem(kind="text", text="2 results"),
                    MCPOutputItem(kind="json", name="payload", data={"items": []}),
                    MCPOutputItem(kind="image", uri="https://files.example.test/a.png", mime_type="image/png"),
                )),
            ]

        capability = sample_capability()
        executor = self.executor(client=FakeMCPClient(FakeMCPServer((capability,)).register(capability, handler)))

        handle = await executor.start(await executor.prepare(self.request()))
        events = [event async for event in executor.stream(handle)]
        result = await executor.result(handle)

        self.assertEqual([event.kind for event in events], ["started", "progress", "progress", "completed"])
        self.assertEqual(events[1].message, "MCP invocation accepted")
        self.assertEqual(events[2].message, "searching garden lights")
        self.assertEqual(events[-1].metadata["capability_ref"], "tool:search")
        self.assertEqual([output.name for output in result.outputs], ["text.1", "payload", "image.3"])
        self.assertEqual(result.outputs[0].value, "2 results")
        self.assertEqual(result.outputs[1].value, {"kind": "json", "data": {"items": []}})
        self.assertEqual(result.outputs[2].value, {"kind": "image", "uri": "https://files.example.test/a.png", "mime_type": "image/png"})
        self.assertEqual(result.status, "succeeded")
        await executor.cleanup(handle)

    async def test_tool_error_inside_a_successful_response_becomes_failed(self):
        def handler(arguments):
            raise MCPToolError(-32602, "invalid params: q")

        capability = sample_capability()
        executor = self.executor(client=FakeMCPClient(FakeMCPServer((capability,)).register(capability, handler)))

        handle = await executor.start(await executor.prepare(self.request()))
        events = [event async for event in executor.stream(handle)]
        result = await executor.result(handle)

        self.assertEqual((events[-1].kind, result.status, result.error), ("failed", "failed", "invalid params: q"))
        self.assertEqual(events[-1].metadata["error_code"], -32602)
        self.assertTrue(events[-1].metadata["is_error"])
        await executor.cleanup(handle)

    async def test_failed_event_becomes_typed_failed_result(self):
        executor = self.executor(client=FakeMCPClient(
            FakeMCPServer(), script=[MCPRawEvent(kind="failed", error_code=-32000, message="server error")],
        ))

        handle = await executor.start(await executor.prepare(self.request()))
        events = [event async for event in executor.stream(handle)]
        result = await executor.result(handle)

        self.assertEqual((events[-1].kind, result.status, result.error), ("failed", "failed", "server error"))
        self.assertEqual(events[-1].metadata["error_code"], -32000)
        await executor.cleanup(handle)

    async def test_partial_output_and_stream_end_completion(self):
        executor = self.executor(client=FakeMCPClient(
            FakeMCPServer(), script=[MCPRawEvent(kind="output", items=(MCPOutputItem(kind="text", text="partial"),))],
        ))

        handle = await executor.start(await executor.prepare(self.request()))
        events = [event async for event in executor.stream(handle)]
        result = await executor.result(handle)

        self.assertEqual(events[1].kind, "partial_result")
        self.assertEqual(events[-1].kind, "completed")
        self.assertEqual((result.status, len(result.outputs)), ("succeeded", 1))
        await executor.cleanup(handle)

    async def test_transport_failure_becomes_typed_failed_result(self):
        executor = self.executor(client=FakeMCPClient(FakeMCPServer(), fail_stream=True))

        handle = await executor.start(await executor.prepare(self.request()))
        events = [event async for event in executor.stream(handle)]
        result = await executor.result(handle)

        self.assertEqual((events[-1].kind, result.status, result.error), ("failed", "failed", "mcp server stream failed"))
        await executor.cleanup(handle)

    async def test_stream_timeout_becomes_typed_failed_result(self):
        executor = self.executor(client=FakeMCPClient(FakeMCPServer(), hang=True), timeout_seconds=0.05)

        handle = await executor.start(await executor.prepare(self.request()))
        events = [event async for event in executor.stream(handle)]
        result = await executor.result(handle)

        self.assertEqual((events[-1].kind, events[-1].status, result.status), ("failed", "failed", "failed"))
        self.assertIn("timed out", result.error)
        await executor.cleanup(handle)

    async def test_invoke_failure_reports_before_any_execution_state(self):
        executor = self.executor(client=FakeMCPClient(FakeMCPServer(), fail_invoke=True))
        prepared = await executor.prepare(self.request())

        with self.assertRaises(MCPExecutorError) as caught:
            await executor.start(prepared)
        self.assertIn("refused the invocation", str(caught.exception))

    async def test_cancel_is_explicit_repeatable_and_terminal(self):
        executor = self.executor(client=FakeMCPClient(FakeMCPServer(), hang=True))

        handle = await executor.start(await executor.prepare(self.request()))
        first = await executor.cancel(handle)
        second = await executor.cancel(handle)
        status = await executor.status(handle)
        result = await executor.result(handle)

        self.assertEqual(
            (first.accepted, first.status, second.status, status.status, result.status),
            (True, "cancelled", "cancelled", "cancelled", "cancelled"),
        )
        self.assertEqual(self.client.cancel_calls, 1)
        await executor.cleanup(handle)

    async def test_cancel_interrupts_a_waiting_stream(self):
        executor = self.executor(client=FakeMCPClient(FakeMCPServer(), hang=True))

        handle = await executor.start(await executor.prepare(self.request()))
        stream = executor.stream(handle).__aiter__()
        await stream.__anext__()
        waiting = asyncio.create_task(stream.__anext__())
        await asyncio.sleep(0)

        await executor.cancel(handle)
        event = await asyncio.wait_for(waiting, timeout=0.5)

        self.assertEqual((event.kind, event.status), ("cancelled", "cancelled"))
        await executor.cleanup(handle)

    async def test_unaccepted_cancellation_is_reported_explicitly(self):
        executor = self.executor(client=FakeMCPClient(FakeMCPServer(), hang=True, accept_cancel=False))

        handle = await executor.start(await executor.prepare(self.request()))
        cancel_result = await executor.cancel(handle)
        status = await executor.status(handle)

        self.assertEqual((cancel_result.accepted, cancel_result.status, status.status), (False, "unknown", "running"))
        self.client.release.set()
        await executor.cleanup(handle)

    async def test_prepare_start_and_unknown_execution_are_bounded(self):
        executor = self.executor()
        prepared = await executor.prepare(self.request())

        with self.assertRaises(MCPExecutorError):
            await executor.prepare(self.request())
        handle = await executor.start(prepared)
        with self.assertRaises(MCPExecutorError):
            await executor.start(prepared)
        with self.assertRaises(MCPExecutorError):
            await executor.result(ExecutionHandle(execution_id="other", executor_ref=MCP_EXECUTOR_REF))
        with self.assertRaises(MCPExecutorError):
            await executor.result(ExecutionHandle(execution_id=handle.execution_id, executor_ref="comfyui"))

        self.assertEqual((await executor.health()).status, "healthy")
        await executor.cleanup(handle)

    def test_profile_is_the_timeout_and_executor_identity_authority(self):
        profile = ExecutionProfile(
            id="profile-mcp", version=1, name="MCP", executor_ref=MCP_EXECUTOR_REF,
            timeout_seconds=42.5, cancel_timeout_seconds=2.5,
        )
        configured = MCPExecutor(
            transport=FakeMCPClient(FakeMCPServer()), capability_resolver=lambda ref: sample_capability(), profile=profile,
        )
        self.assertEqual((configured._timeout_seconds, configured._cancel_timeout_seconds), (42.5, 2.5))

        with self.assertRaises(ValueError):
            MCPExecutor(
                transport=FakeMCPClient(FakeMCPServer()), capability_resolver=lambda ref: None,
                profile=profile, timeout_seconds=1,
            )
        with self.assertRaises(ValueError):
            MCPExecutor(
                transport=FakeMCPClient(FakeMCPServer()), capability_resolver=lambda ref: None,
                profile=ExecutionProfile(id="p", version=1, name="Comfy", executor_ref="comfyui"),
            )

    def test_seam_has_no_canvas_provider_sdk_or_mcp_client_dependency(self):
        root = Path(__file__).resolve().parent.parent
        violations = []
        for path in sorted((root / "workbench" / "mcp").rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            for module in _imported_modules(path, root):
                lowered = module.lower()
                if module in FORBIDDEN_PROVIDER_SDK_IMPORTS or module.split(".")[0] in FORBIDDEN_PROVIDER_SDK_IMPORTS:
                    violations.append(f"{path.relative_to(root)} -> provider sdk {module}")
                if module in FORBIDDEN_MCP_CLIENT_IMPORTS or module.split(".")[0] in FORBIDDEN_MCP_CLIENT_IMPORTS:
                    violations.append(f"{path.relative_to(root)} -> mcp client library {module}")
                if any(marker in lowered for marker in FORBIDDEN_BOUNDARY_MARKERS):
                    violations.append(f"{path.relative_to(root)} -> canvas/legacy {module}")
        self.assertEqual(violations, [])


class MCPExecutorFakeServerTests(unittest.IsolatedAsyncioTestCase):
    """The DoD test: the generic contract is exercised against a fake MCP peer."""

    async def test_generic_contract_is_testable_with_a_fake_mcp_server(self):
        def echo(arguments):
            return [MCPRawEvent(kind="completed", items=(MCPOutputItem(kind="text", text=f"echo:{arguments['q']}"),))]

        capability = sample_capability()
        server = FakeMCPServer((capability,)).register(capability, echo)
        executor = MCPExecutor(
            transport=FakeMCPClient(server),
            capability_resolver=lambda ref: server.capabilities.get(ref.ref),
            timeout_seconds=1.0,
            cancel_timeout_seconds=0.1,
        )
        request = ExecutionRequest(
            execution_id="execution-fake",
            idempotency_key="idempotency-fake",
            inputs=(ExecutionInput(name="query", value="hello"),),
            config={"capability_ref": "tool:search", "connection_ref": "mcp-server-1"},
        )

        prepared = await executor.prepare(request)
        handle = await executor.start(prepared)
        events = [event async for event in executor.stream(handle)]
        result = await executor.result(handle)

        self.assertIsInstance(executor, Executor)
        self.assertIsInstance(executor._transport, MCPTransport)
        self.assertEqual(result.status, "succeeded")
        self.assertEqual(result.outputs[0].value, "echo:hello")
        self.assertEqual([event.kind for event in events], ["started", "progress", "completed"])
        self.assertEqual(server.dispatched[0].arguments, {"q": "hello"})
        self.assertEqual(server.dispatched[0].connection_ref, "mcp-server-1")
        await executor.cleanup(handle)


class MCPExecutorRegistryTests(unittest.IsolatedAsyncioTestCase):
    async def test_registry_resolves_the_mcp_runtime_route_without_substitution(self):
        executor = MCPExecutor(
            transport=FakeMCPClient(FakeMCPServer()), capability_resolver=lambda ref: sample_capability(),
        )
        self.assertIsInstance(executor, Executor)
        registry = ExecutorRegistry((
            ExecutorRegistration(
                executor=executor,
                capabilities=("mcp_tool",),
                runtime_routes=("mcp",),
                execution_profiles=("profile-mcp@1",),
            ),
        ))

        resolved = registry.resolve(runtime_route_ref="mcp", execution_profile_ref="profile-mcp@1", required_capabilities=("mcp_tool",))
        other = registry.resolve(runtime_route_ref="runninghub")

        self.assertTrue(resolved.resolved)
        self.assertEqual(resolved.executor.executor_ref, MCP_EXECUTOR_REF)
        self.assertFalse(other.resolved)
        self.assertEqual(other.reason, "runtime_route_unavailable")


class MCPExecutionServiceTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.database = Path(self.temp.name) / "workbench.sqlite3"
        self.now = datetime(2026, 9, 12, tzinfo=UTC)
        SqliteProjectCanvasRepository(self.database, clock=lambda: self.now).create_project(ProjectRecord(
            id="project-1", name="Project", workspace_id="local", created_by="owner",
            created_at=self.now, updated_at=self.now,
        ))
        self.runs = SqliteExecutionRunRepository(self.database, clock=lambda: self.now)
        self.attempts = SqliteExecutionAttemptRepository(self.database, clock=lambda: self.now)
        self.events = ExecutionEventService(
            SqliteExecutionEventRepository(self.database, clock=lambda: self.now),
            actor_id="owner",
            id_factory=iter(["event-1", "event-2", "event-3", "event-4", "event-5"]).__next__,
            clock=lambda: self.now,
        )

    def tearDown(self):
        self.temp.cleanup()

    def profile(self):
        return ExecutionProfile(
            id="profile-mcp", version=1, name="MCP", executor_ref=MCP_EXECUTOR_REF,
            runtime_connection_ref="mcp-server-1",
            default_params={"capability_ref": "tool:search"},
        )

    def run_record(self, run_id: str, task_id: str):
        return ExecutionRun(
            id=run_id, project_id="project-1", task_id=task_id, execution_profile_ref="profile-mcp@1",
            policy=ExecutionPolicy(),
            input_projection=ExecutionInputProjection(
                inputs=[{
                    "input_id": "input-1", "binding_id": "binding-1", "target": "capability.query",
                    "role": "query", "order": 0, "source_type": "literal", "source_ref": "literal-1",
                    "value": "garden lights", "source_snapshot": "garden lights",
                }],
                parameters={"capability_ref": "tool:search", "input_roles": {"input-1": "query"}},
            ),
            created_at=self.now,
        )

    def executor(self, client):
        return MCPExecutor(
            transport=client,
            capability_resolver=lambda ref: sample_capability() if ref.ref == "tool:search" else None,
            profile=self.profile(),
        )

    async def test_task_runs_as_an_executor_route_not_a_canvas_runtime(self):
        self.runs.create(self.run_record("run-mcp", "task-mcp"), actor_id="owner")
        capability = sample_capability()
        server = FakeMCPServer((capability,)).register(capability, lambda arguments: [
            MCPRawEvent(kind="completed", items=(MCPOutputItem(kind="text", text=f"results for {arguments['q']}"),)),
        ])
        client = FakeMCPClient(server)
        service = ExecutionService(
            self.runs,
            self.attempts,
            actor_id="owner",
            event_service=self.events,
            id_factory=iter(["attempt-mcp", "idempotency-mcp"]).__next__,
            clock=lambda: self.now,
        )

        result = await service.execute_run("run-mcp", executor=self.executor(client))

        self.assertEqual(result.status, "succeeded")
        self.assertEqual(result.outputs[0].value, "results for garden lights")
        self.assertEqual(self.runs.get("run-mcp", actor_id="owner").status, "succeeded")
        attempt = self.attempts.get("attempt-mcp", actor_id="owner")
        self.assertEqual(
            (attempt.status, attempt.summary["output_count"], attempt.summary["executor_ref"]),
            ("succeeded", 1, MCP_EXECUTOR_REF),
        )
        self.assertEqual(
            [event.event_type for event in self.events.stream("run-mcp")],
            ["started", "progress", "completed"],
        )
        call = client.calls[0]
        self.assertEqual((call.capability_ref, call.action, call.connection_ref), ("tool:search", "call_tool", "mcp-server-1"))
        self.assertEqual(call.arguments, {"q": "garden lights"})

    async def test_execution_service_cancel_uses_the_active_mcp_handle(self):
        self.runs.create(self.run_record("run-cancel", "task-mcp"), actor_id="owner")
        client = FakeMCPClient(FakeMCPServer(), hang=True)
        service = ExecutionService(
            self.runs,
            self.attempts,
            actor_id="owner",
            id_factory=iter(["attempt-cancel", "idempotency-cancel"]).__next__,
            clock=lambda: self.now,
        )

        running = asyncio.create_task(service.execute("run-cancel", executor=self.executor(client)))
        for _ in range(20):
            if "attempt-cancel" in service._active_controls:
                break
            await asyncio.sleep(0)

        cancelled = await service.cancel_run("run-cancel")
        result = await running

        self.assertEqual((cancelled.status, result.status), ("cancelled", "cancelled"))
        self.assertEqual(self.attempts.get("attempt-cancel", actor_id="owner").status, "cancelled")
        self.assertEqual(client.cancel_calls, 1)


if __name__ == "__main__":
    unittest.main()

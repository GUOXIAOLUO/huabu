import asyncio
import sys
import tempfile
import unittest
from pathlib import Path

from workbench.codex.bridge import CodexBridge, CodexBridgeError, HarnessLaunchPolicy
from workbench.codex.events import RuntimeEvent


FAKE_SERVER = r'''import json, sys
pending_turn = None
for raw in sys.stdin:
    message = json.loads(raw)
    if message.get("method") == "initialized": continue
    if message.get("method") == "initialize":
        print(json.dumps({"id": message["id"], "result": {"protocolVersion": "2"}}), flush=True)
    elif message.get("method") == "thread/start":
        print(json.dumps({"id": message["id"], "result": {"thread": {"id": "thread-1"}}}), flush=True)
    elif message.get("method") == "turn/start":
        pending_turn = message["id"]
        print(json.dumps({"id": 99, "method": "item/commandExecution/requestApproval", "params": {"reason": "fixture"}}), flush=True)
    elif message.get("id") == 99 and pending_turn:
        assert message["result"] == {"decision": "decline"}
        print(json.dumps({"method": "turn/completed", "params": {"turn": {"id": "turn-1"}}}), flush=True)
        print(json.dumps({"id": pending_turn, "result": {"turn": {"id": "turn-1"}}}), flush=True)
        pending_turn = None
    elif message.get("method") == "turn/interrupt":
        print(json.dumps({"id": message["id"], "result": {}}), flush=True)
    elif message.get("method") == "model/list":
        print(json.dumps({"id": message["id"], "result": {"data": []}}), flush=True)
    elif message.get("method") == "config/read":
        print(json.dumps({"id": message["id"], "result": {"config": {}}}), flush=True)
'''

NOISY_SERVER = r'''import json, sys
for index in range(20000):
    print(f"diagnostic-{index} api_key=fixture-secret", file=sys.stderr, flush=True)
for raw in sys.stdin:
    message = json.loads(raw)
    if message.get("method") == "initialize":
        print(json.dumps({"id": message["id"], "result": {"protocolVersion": "2"}}), flush=True)
'''

EOF_SERVER = r'''import json, sys
for raw in sys.stdin:
    message = json.loads(raw)
    if message.get("method") == "initialize":
        print(json.dumps({"id": message["id"], "result": {"protocolVersion": "2"}}), flush=True)
    elif message.get("method") == "thread/start":
        sys.exit(0)
'''

RETRY_SERVER = r'''import json, sys
model_requests = 0
for raw in sys.stdin:
    message = json.loads(raw)
    if message.get("method") == "initialize":
        print(json.dumps({"id": message["id"], "result": {"protocolVersion": "2"}}), flush=True)
    elif message.get("method") == "model/list":
        model_requests += 1
        if model_requests == 2:
            print(json.dumps({"id": message["id"], "result": {"data": [{"id": "retry-model"}]}}), flush=True)
'''

TIMEOUT_SERVER = r'''import json, sys
for raw in sys.stdin:
    message = json.loads(raw)
    if message.get("method") == "initialize":
        print(json.dumps({"id": message["id"], "result": {"protocolVersion": "2"}}), flush=True)
'''


class CodexBridgeTests(unittest.IsolatedAsyncioTestCase):
    async def test_bridge_initializes_uses_restrictive_options_and_normalizes_events(self):
        with tempfile.TemporaryDirectory() as directory:
            policy = HarnessLaunchPolicy(
                Path(directory), executable=sys.executable, arguments=("-u", "-c", FAKE_SERVER)
            )
            bridge = CodexBridge(policy)
            initialized = await bridge.start()
            thread = await bridge.create_thread()
            turn = await bridge.start_turn(thread.thread.id, "hello")
            self.assertEqual((await bridge.list_models()).data, ())
            self.assertEqual((await bridge.read_config()).config, {})
            approval = await asyncio.wait_for(bridge.events.get(), timeout=1)
            event = await asyncio.wait_for(bridge.events.get(), timeout=1)
            self.assertEqual(initialized.protocol_version, "2")
            self.assertEqual(turn.turn.id, "turn-1")
            self.assertEqual((approval.kind, approval.status), ("approval", "waiting"))
            self.assertEqual((event.kind, event.status), ("lifecycle", "completed"))
            self.assertEqual(policy.turn_options()["sandboxPolicy"], {"type": "readOnly", "networkAccess": False})
            self.assertEqual(policy.thread_options()["approvalPolicy"], "never")
            await bridge.shutdown()

    async def test_interrupt_and_explicit_recovery_are_supported(self):
        with tempfile.TemporaryDirectory() as directory:
            policy = HarnessLaunchPolicy(
                Path(directory), executable=sys.executable, arguments=("-u", "-c", FAKE_SERVER)
            )
            bridge = CodexBridge(policy)
            await bridge.start()
            self.assertEqual((await bridge.interrupt_turn("thread-1", "turn-1")).model_dump(), {})
            recovered = await bridge.recover()
            self.assertEqual(recovered.protocol_version, "2")
            await bridge.shutdown()

    async def test_policy_bounds_cwd_and_filters_secrets(self):
        with tempfile.TemporaryDirectory() as directory:
            policy = HarnessLaunchPolicy(Path(directory))
            self.assertEqual(policy.environment({"PATH": "/bin", "OPENAI_API_KEY": "secret"}), {"PATH": "/bin"})
            with self.assertRaises(CodexBridgeError):
                policy.resolve_cwd(Path(directory).parent)

    async def test_stderr_is_drained_bounded_and_redacted_until_shutdown(self):
        with tempfile.TemporaryDirectory() as directory:
            policy = HarnessLaunchPolicy(
                Path(directory), executable=sys.executable, arguments=("-u", "-c", NOISY_SERVER), timeout_seconds=3
            )
            bridge = CodexBridge(policy)
            initialized = await asyncio.wait_for(bridge.start(), timeout=2)
            self.assertEqual(initialized.protocol_version, "2")
            await asyncio.sleep(0.05)
            diagnostics = bridge.stderr_diagnostics()
            self.assertGreater(len(diagnostics), 0)
            self.assertLessEqual(len(diagnostics), 200)
            self.assertTrue(all(len(item) <= 4096 for item in diagnostics))
            self.assertTrue(all("fixture-secret" not in item for item in diagnostics))
            await bridge.shutdown()
            self.assertFalse(bridge.running)

    async def test_unexpected_stdout_eof_fails_pending_request_and_allows_explicit_recovery(self):
        with tempfile.TemporaryDirectory() as directory:
            policy = HarnessLaunchPolicy(
                Path(directory), executable=sys.executable, arguments=("-u", "-c", EOF_SERVER), timeout_seconds=3
            )
            bridge = CodexBridge(policy)
            initialized = await bridge.start()
            self.assertEqual(initialized.protocol_version, "2")
            with self.assertRaisesRegex(CodexBridgeError, "stdout EOF"):
                await asyncio.wait_for(bridge.create_thread(), timeout=1)
            self.assertFalse(bridge._pending)
            terminal = await asyncio.wait_for(bridge.events.get(), timeout=1)
            self.assertEqual((terminal.kind, terminal.status), ("error", "failed"))
            self.assertEqual(terminal.diagnostic_ref.code, "unexpected-eof")
            recovered = await bridge.recover()
            self.assertEqual(recovered.protocol_version, "2")
            await bridge.shutdown()

    async def test_event_storm_is_bounded_and_preserves_critical_event(self):
        with tempfile.TemporaryDirectory() as directory:
            bridge = CodexBridge(HarnessLaunchPolicy(Path(directory)))
            for index in range(5000):
                bridge._publish_event(RuntimeEvent("progress", "running", "runtime", {"index": index}))
            bridge._publish_event(RuntimeEvent("error", "failed", "transport", {"error": "fixture"}))

            stats = bridge.event_queue_stats()
            self.assertEqual(stats["maxsize"], 256)
            self.assertEqual(stats["size"], 256)
            self.assertGreater(stats["dropped"], 0)
            events = [bridge.events.get_nowait() for _ in range(stats["size"])]
            terminal = next(event for event in events if event.kind == "error")
            self.assertEqual(terminal.operation, "transport")
            self.assertEqual(terminal.payload["dropped_events"], stats["dropped"])
            for index in range(257):
                bridge._publish_event(RuntimeEvent("error", "failed", "transport", {"index": index}))
            critical_stats = bridge.event_queue_stats()
            self.assertEqual(critical_stats["dropped_important"], 1)
            self.assertEqual(critical_stats["size"], 256)

    async def test_retryable_timeout_retries_with_bounded_backoff(self):
        with tempfile.TemporaryDirectory() as directory:
            policy = HarnessLaunchPolicy(
                Path(directory),
                executable=sys.executable,
                arguments=("-u", "-c", RETRY_SERVER),
                timeout_seconds=0.03,
                max_request_attempts=2,
                retry_backoff_seconds=0.001,
            )
            bridge = CodexBridge(policy)
            await bridge.start()
            result = await bridge.list_models()
            self.assertEqual(result.data[0].id, "retry-model")
            self.assertEqual(policy.request_attempts("model/list"), 2)
            self.assertEqual(policy.retry_delay(1), 0.001)
            self.assertFalse(bridge._pending)
            await bridge.shutdown()

    async def test_non_retryable_timeout_is_bounded_and_observable(self):
        with tempfile.TemporaryDirectory() as directory:
            policy = HarnessLaunchPolicy(
                Path(directory), executable=sys.executable, arguments=("-u", "-c", TIMEOUT_SERVER), timeout_seconds=0.02
            )
            bridge = CodexBridge(policy)
            await bridge.start()
            with self.assertRaisesRegex(CodexBridgeError, r"turn/start after 1 attempt"):
                await bridge.start_turn("thread-1", "hello")
            self.assertFalse(bridge._pending)
            timeout_event = await asyncio.wait_for(bridge.events.get(), timeout=1)
            self.assertEqual((timeout_event.kind, timeout_event.status), ("error", "failed"))
            self.assertEqual(timeout_event.diagnostic_ref.code, "request-timeout")
            self.assertEqual(timeout_event.payload["attempts"], 1)
            await bridge.shutdown()

    async def test_request_cancellation_does_not_retry_or_leak_pending_future(self):
        with tempfile.TemporaryDirectory() as directory:
            policy = HarnessLaunchPolicy(
                Path(directory), executable=sys.executable, arguments=("-u", "-c", TIMEOUT_SERVER), timeout_seconds=1
            )
            bridge = CodexBridge(policy)
            await bridge.start()
            request = asyncio.create_task(bridge.list_models())
            await asyncio.sleep(0.01)
            request.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await request
            self.assertFalse(bridge._pending)
            await bridge.shutdown()

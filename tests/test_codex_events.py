import unittest

from workbench.codex.events import CodexEventNormalizer


class CodexEventNormalizerTests(unittest.TestCase):
    def test_normalizes_lifecycle_progress_output_and_approval_events(self):
        cases = {
            "turn/started": ("lifecycle", "started", "turn"),
            "turn/completed": ("lifecycle", "completed", "turn"),
            "item/started": ("progress", "running", "item"),
            "item/completed": ("output", "completed", "item"),
            "item/commandExecution/requestApproval": ("approval", "waiting", "approval"),
        }
        for method, expected in cases.items():
            event = CodexEventNormalizer.normalize(method, {"fixture": True})
            self.assertEqual((event.kind, event.status, event.operation), expected)
            self.assertEqual(event.payload, {})

    def test_normalizes_errors_and_retains_only_an_explicit_diagnostic_reference(self):
        event = CodexEventNormalizer.error("unexpected-eof", {"message": "closed"}, protocol_method="transport")
        self.assertEqual((event.kind, event.status, event.operation), ("error", "failed", "transport"))
        self.assertEqual(event.diagnostic_ref.protocol_method, "transport")
        self.assertEqual(event.diagnostic_ref.code, "unexpected-eof")
        unknown = CodexEventNormalizer.normalize("future/event", {})
        self.assertEqual((unknown.kind, unknown.status, unknown.operation), ("progress", "running", "runtime"))
        self.assertEqual(unknown.diagnostic_ref.code, "notification")
        projected = CodexEventNormalizer.normalize(
            "item/completed", {"item": {"id": "item-1", "type": "text", "text": "answer"}, "private": "discarded"}
        )
        self.assertEqual(projected.payload, {"item_id": "item-1", "item_type": "text", "text": "answer"})

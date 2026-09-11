import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from fastapi import Request

import main


class RecordingSocket:
    def __init__(self):
        self.messages = []

    async def send_text(self, message):
        self.messages.append(message)

    async def accept(self):
        return None


class FailingSocket:
    async def send_text(self, _message):
        raise RuntimeError("closed")

    async def accept(self):
        return None


class EventContractTests(unittest.IsolatedAsyncioTestCase):
    async def test_same_client_two_sockets_disconnect_and_send_failure_keep_indexes_consistent(self):
        manager = main.ConnectionManager()
        first, second = RecordingSocket(), RecordingSocket()
        with patch("builtins.print"):
            await manager.connect(first, "client-1")
            await manager.connect(second, "client-1")
            await manager.disconnect(first, "client-1")
        self.assertEqual(manager.user_connections["client-1"], {second})
        self.assertEqual(manager.online_count(), 1)
        await manager.send_personal_message({"type": "notice"}, "client-1")
        self.assertEqual(json.loads(second.messages[-1]), {"type": "notice"})

        failed = FailingSocket()
        await manager.connect(failed, "client-1")
        with patch("builtins.print"):
            await manager.send_personal_message({"type": "notice"}, "client-1")
        self.assertNotIn(failed, manager.active_connections)
        self.assertNotIn(failed, manager.connection_clients)
        self.assertEqual(manager.user_connections["client-1"], {second})

    async def test_canvas_invalidation_message_has_stable_payload(self):
        manager = main.ConnectionManager()
        receiver = RecordingSocket()
        failed = FailingSocket()
        manager.active_connections = [receiver, failed]

        with patch("builtins.print"):
            await manager.broadcast_canvas_updated("canvas-1", 123, "client-1")

        self.assertEqual(
            json.loads(receiver.messages[0]),
            {
                "type": "canvas_updated",
                "canvas_id": "canvas-1",
                "updated_at": 123,
                "client_id": "client-1",
                "revision": 0,
            },
        )
        self.assertEqual(manager.active_connections, [receiver])

        revision_broadcasts = []
        await manager.broadcast_canvas_updated("canvas-1", 124, "client-1", revision=7)
        self.assertEqual(json.loads(receiver.messages[1])["revision"], 7)

    async def test_chat_sse_emits_meta_delta_and_done_without_provider_network(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            request = Request(
                {
                    "type": "http",
                    "method": "POST",
                    "path": "/api/chat/stream",
                    "headers": [],
                    "client": ("127.0.0.1", 12345),
                    "scheme": "http",
                    "server": ("testserver", 80),
                }
            )
            payload = main.ChatRequest(message="hello", provider="fixture-codex", model="fixture-model")
            provider = {"id": "fixture-codex", "protocol": "codex", "chat_models": ["fixture-model"]}
            with (
                patch.object(main, "CONVERSATION_DIR", temp_dir),
                patch.object(main, "get_api_provider", return_value=provider),
                patch.object(main, "codex_chat_text", new=AsyncMock(return_value=("fixture reply", {"source": "test"}))),
            ):
                response = await main.chat_stream(payload, request, "fixture-user")
                chunks = [chunk async for chunk in response.body_iterator]

        self.assertEqual(response.media_type, "text/event-stream")
        text_chunks = [chunk.decode("utf-8") if isinstance(chunk, bytes) else chunk for chunk in chunks]
        events = [json.loads(chunk[6:].strip()) for chunk in text_chunks]
        self.assertEqual([event["type"] for event in events], ["meta", "delta", "done"])
        self.assertEqual(events[1], {"type": "delta", "delta": "fixture reply"})
        self.assertEqual(events[2]["message"]["content"], "fixture reply")
        self.assertEqual(events[2]["conversation"]["messages"][0]["content"], "hello")

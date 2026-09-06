"""Behavioral tests for the canonical Canvas transport API (R4-05)."""

import asyncio
import json
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

import main
from fastapi import HTTPException

from workbench.api.canvases import CanonicalCanvasPutPayload


def _legacy_payload(canvas_id: str, title: str) -> dict:
    return {
        "id": canvas_id,
        "project": "default",
        "owner": "",
        "title": title,
        "kind": "classic",
        "created_at": 1788000000000,
        "updated_at": 1788000001000,
        "viewport": {"x": 0, "y": 0, "scale": 1},
        "nodes": [],
        "connections": [],
    }


class CanonicalCanvasApiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.canvas_dir = self.root / "canvases"
        self.canvas_dir.mkdir()
        self.database = self.root / "workbench.sqlite3"
        self.patches = [
            patch.object(main, "CANVAS_DIR", str(self.canvas_dir)),
            patch.object(main, "WORKBENCH_DATABASE_PATH", str(self.database)),
        ]
        for item in self.patches:
            item.start()

    def tearDown(self):
        for item in reversed(self.patches):
            item.stop()
        self.temp.cleanup()

    def _set_flag(self, enabled):
        patcher = patch.object(main, "WORKBENCH_CANONICAL_CANVAS_ROUTING_ENABLED", enabled)
        patcher.start()
        self.addCleanup(patcher.stop)

    def _activate_sqlite_authority(self):
        payload = _legacy_payload("canvas-1", "One")
        (self.canvas_dir / "canvas-1.json").write_text(json.dumps(payload), encoding="utf-8")
        service = main.project_canvas_migration_service()
        service.backfill([{"id": "default", "name": "Default"}], [payload], now=datetime.now(UTC))
        main.canonical_project_canvas_repository().activate_sqlite_authority([payload])
        self._set_flag(True)

    def _endpoint(self, path, method):
        pending = list(main.app.routes)
        while pending:
            route = pending.pop()
            if getattr(route, "path", None) == path and method in getattr(route, "methods", set()):
                return route.endpoint
            pending.extend(getattr(route, "routes", []))
            pending.extend(getattr(getattr(route, "original_router", None), "routes", []))
        self.fail(f"canonical canvas {method} route is not registered: {path}")

    def _get_canvas(self, canvas_id):
        return asyncio.run(self._endpoint("/api/v1/canvases/{canvas_id}", "GET")(canvas_id=canvas_id))

    def _put_canvas(self, canvas_id, payload, expected_revision):
        body = CanonicalCanvasPutPayload(payload=payload, expected_revision=expected_revision)
        return asyncio.run(self._endpoint("/api/v1/canvases/{canvas_id}", "PUT")(canvas_id=canvas_id, body=body))

    def test_get_returns_canvas_with_logical_revision_and_updated_at(self):
        self._activate_sqlite_authority()
        body = self._get_canvas("canvas-1")
        self.assertEqual(body["canvas"]["id"], "canvas-1")
        self.assertEqual(body["revision"], 1)
        self.assertFalse(body["deleted"])
        self.assertTrue(body["updated_at"])

    def test_put_with_matching_revision_performs_cas_and_increments(self):
        self._activate_sqlite_authority()
        current = self._get_canvas("canvas-1")
        payload = dict(current["canvas"])
        payload["title"] = "Renamed via canonical CAS"

        body = self._put_canvas("canvas-1", payload, expected_revision=current["revision"])
        self.assertEqual(body["revision"], 2)
        self.assertEqual(body["canvas"]["title"], "Renamed via canonical CAS")
        # updated_at is display/compat metadata kept fresh server-side; the
        # logical revision is the only concurrency cursor.
        self.assertIsInstance(body["canvas"]["updated_at"], int)
        self.assertGreater(body["canvas"]["updated_at"], 1788000001000)

        refreshed = self._get_canvas("canvas-1")
        self.assertEqual(refreshed["revision"], 2)
        self.assertEqual(refreshed["canvas"]["title"], "Renamed via canonical CAS")

    def test_put_with_stale_revision_returns_explicit_conflict(self):
        self._activate_sqlite_authority()
        stale = self._get_canvas("canvas-1")
        self._put_canvas("canvas-1", dict(stale["canvas"]), expected_revision=1)  # revision -> 2

        with self.assertRaises(HTTPException) as caught:
            self._put_canvas("canvas-1", dict(stale["canvas"]), expected_revision=1)
        self.assertEqual(caught.exception.status_code, 409)
        detail = caught.exception.detail
        self.assertEqual(detail["error"], "stale_revision")
        self.assertEqual(detail["expected_revision"], 1)
        self.assertEqual(detail["current_revision"], 2)
        self.assertTrue(detail["current_updated_at"])
        # The current payload rides along so conflict-merging clients keep
        # their characterized recovery semantics.
        self.assertEqual(detail["canvas"]["id"], "canvas-1")
        self.assertEqual(detail["canvas"]["title"], "One")

    def test_canonical_transport_requires_sqlite_authority(self):
        main.canonical_project_canvas_repository()  # authority stays legacy_json
        with self.assertRaises(HTTPException) as get_error:
            self._get_canvas("canvas-1")
        self.assertEqual(get_error.exception.status_code, 503)
        self.assertEqual(get_error.exception.detail["error"], "canonical_canvas_api_requires_sqlite_authority")
        with self.assertRaises(HTTPException) as put_error:
            self._put_canvas("canvas-1", _legacy_payload("canvas-1", "x"), expected_revision=1)
        self.assertEqual(put_error.exception.status_code, 503)

    def test_get_unknown_canvas_returns_404(self):
        self._activate_sqlite_authority()
        with self.assertRaises(HTTPException) as caught:
            self._get_canvas("missing-canvas")
        self.assertEqual(caught.exception.status_code, 404)

    def test_legacy_transport_keeps_its_characterized_shape_without_revision(self):
        self._activate_sqlite_authority()
        legacy_get = asyncio.run(self._endpoint("/api/canvases/{canvas_id}", "GET")(canvas_id="canvas-1"))
        self.assertIn("canvas", legacy_get)
        self.assertNotIn("revision", legacy_get)
        self.assertNotIn("revision", legacy_get["canvas"])

    def test_http_round_trip_cas_recovers_from_a_stale_write(self):
        from fastapi.testclient import TestClient

        self._activate_sqlite_authority()
        client = TestClient(main.app)

        loaded = client.get("/api/v1/canvases/canvas-1")
        self.assertEqual(loaded.status_code, 200)
        revision = loaded.json()["revision"]

        payload = dict(loaded.json()["canvas"])
        payload["title"] = "HTTP writer A"
        saved = client.put("/api/v1/canvases/canvas-1", json={"payload": payload, "expected_revision": revision})
        self.assertEqual(saved.status_code, 200)
        self.assertEqual(saved.json()["revision"], revision + 1)

        stale = client.put("/api/v1/canvases/canvas-1", json={"payload": payload, "expected_revision": revision})
        self.assertEqual(stale.status_code, 409)
        conflict = stale.json()["detail"]
        self.assertEqual(conflict["current_revision"], revision + 1)
        self.assertEqual(conflict["canvas"]["title"], "HTTP writer A")

        recovered = client.put(
            "/api/v1/canvases/canvas-1",
            json={"payload": {**payload, "title": "HTTP writer B"}, "expected_revision": conflict["current_revision"]},
        )
        self.assertEqual(recovered.status_code, 200)
        self.assertEqual(recovered.json()["revision"], revision + 2)


if __name__ == "__main__":
    unittest.main()

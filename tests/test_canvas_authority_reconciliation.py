"""Behavioral tests for the read-only Legacy/SQLite canvas reconciliation tool."""

import json
import subprocess
import sys
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

from workbench.application.project_canvas_migration import ProjectCanvasMigrationService
from workbench.repositories.sqlite_project_canvas_repository import SqliteProjectCanvasRepository

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def _classic_payload(canvas_id: str, *, node_x: float = 10.0, deleted_at=None) -> dict:
    return {
        "id": canvas_id,
        "project": "default",
        "owner": "",
        "title": f"Canvas {canvas_id}",
        "kind": "classic",
        "created_at": 1788000000000,
        "updated_at": 1788000001000,
        "deleted_at": deleted_at,
        "viewport": {"x": 0, "y": 0, "scale": 1},
        "nodes": [
            {"id": f"{canvas_id}-node-1", "type": "image", "title": "n1", "x": node_x, "y": 20.0, "w": 100, "h": 80},
            {"id": f"{canvas_id}-node-2", "type": "prompt", "title": "n2", "x": 30.0, "y": 40.0, "w": 100, "h": 80},
        ],
        "connections": [
            {"from": f"{canvas_id}-node-1", "to": f"{canvas_id}-node-2", "kind": "input"},
        ],
        "unknown_future_field": {"preserve": True},
    }


class CanvasAuthorityReconciliationTests(unittest.TestCase):
    def _build_fixture(self, root: Path) -> tuple[Path, Path, Path, SqliteProjectCanvasRepository]:
        projects = root / "projects.json"
        canvases_dir = root / "canvases"
        canvases_dir.mkdir()
        database = root / "workbench.sqlite3"
        projects.write_text(json.dumps({"projects": [{"id": "default", "name": "Default"}]}), encoding="utf-8")
        repository = SqliteProjectCanvasRepository(database)
        service = ProjectCanvasMigrationService(repository)
        legacy = [_classic_payload("canvas-1"), _classic_payload("canvas-2", deleted_at=1788000002000)]
        for payload in legacy:
            path = canvases_dir / f"{payload['id']}.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
        service.backfill([{"id": "default", "name": "Default"}], legacy, now=datetime.now(UTC))
        return projects, canvases_dir, database, repository

    def test_converged_datasets_report_zero_differences_and_authority_state(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            projects, canvases_dir, database, repository = self._build_fixture(root)

            command = [
                sys.executable, "tools/reconcile_canvas_authority.py",
                "--canvases-dir", str(canvases_dir), "--database", str(database),
                "--projects", str(projects), "--report", str(root / "report.json"),
            ]
            result = subprocess.run(command, cwd=REPOSITORY_ROOT, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)

            report = json.loads((root / "report.json").read_text(encoding="utf-8"))
            self.assertEqual(report["schema_version"], "workbench.canvas-authority-reconciliation-report/1")
            self.assertEqual(report["legacy"]["file_count"], 2)
            self.assertEqual(report["legacy"]["id_count"], 2)
            self.assertEqual(report["sqlite"]["row_count"], 2)
            self.assertEqual(report["sqlite"]["active_count"], 1)
            self.assertEqual(report["sqlite"]["deleted_count"], 1)
            self.assertEqual(report["legacy"]["legacy_only_ids"], [])
            self.assertEqual(report["sqlite"]["sqlite_only_ids"], [])
            self.assertEqual(report["unexpected_rows"], [])
            self.assertTrue(all(comparison["matches"] for comparison in report["comparisons"]))
            self.assertTrue(report["converged"])
            self.assertEqual(report["canvas_authority"], repository.canvas_authority())

    def test_detects_position_drift_legacy_only_and_sqlite_only_rows(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            projects, canvases_dir, database, repository = self._build_fixture(root)

            drifted = json.loads((canvases_dir / "canvas-1.json").read_text(encoding="utf-8"))
            drifted["nodes"][0]["x"] = 555.5
            (canvases_dir / "canvas-1.json").write_text(json.dumps(drifted), encoding="utf-8")
            (canvases_dir / "canvas-2.json").unlink()
            repository.create_canvas_payload(
                actor_id="local-workspace-actor",
                payload={"id": "canvas-extra", "project": "default", "title": "Extra", "kind": "classic",
                         "nodes": [], "connections": [], "viewport": {}},
            )

            command = [
                sys.executable, "tools/reconcile_canvas_authority.py",
                "--canvases-dir", str(canvases_dir), "--database", str(database),
            ]
            result = subprocess.run(command, cwd=REPOSITORY_ROOT, capture_output=True, text=True)
            self.assertEqual(result.returncode, 1, result.stderr)

            report = json.loads(result.stdout)
            self.assertEqual(report["legacy"]["legacy_only_ids"], [])
            self.assertEqual(report["sqlite"]["sqlite_only_ids"], ["canvas-2", "canvas-extra"])
            comparison = next(item for item in report["comparisons"] if item["canvas_id"] == "canvas-1")
            self.assertFalse(comparison["matches"])
            self.assertEqual(
                comparison["node_position_differences"],
                [{"node_id": "canvas-1-node-1", "legacy": [555.5, 20.0], "sqlite": [10.0, 20.0]}],
            )
            self.assertFalse(report["converged"])

    def test_detects_trash_state_mismatch_without_touching_data(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            projects, canvases_dir, database, repository = self._build_fixture(root)

            database_bytes_before = database.read_bytes()
            trashed = json.loads((canvases_dir / "canvas-1.json").read_text(encoding="utf-8"))
            trashed["deleted_at"] = 1788000003000
            (canvases_dir / "canvas-1.json").write_text(json.dumps(trashed), encoding="utf-8")

            command = [
                sys.executable, "tools/reconcile_canvas_authority.py",
                "--canvases-dir", str(canvases_dir), "--database", str(database),
                "--report", str(root / "report.json"),
            ]
            result = subprocess.run(command, cwd=REPOSITORY_ROOT, capture_output=True, text=True)
            self.assertEqual(result.returncode, 1, result.stderr)

            comparison = next(
                item for item in json.loads((root / "report.json").read_text(encoding="utf-8"))["comparisons"]
                if item["canvas_id"] == "canvas-1"
            )
            self.assertEqual(
                comparison["trash_state_mismatch"], {"legacy_trashed": True, "sqlite_trashed": False}
            )
            self.assertEqual(database.read_bytes(), database_bytes_before)


if __name__ == "__main__":
    unittest.main()

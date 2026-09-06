"""Behavioral tests for the R4 canvas authority resolver/policy seam."""

import sqlite3
import tempfile
import unittest
from pathlib import Path

from workbench.application.canvas_authority_policy import (
    read_canvas_authority_state,
    resolve_canvas_authority,
)
from workbench.repositories.sqlite_project_canvas_repository import SqliteProjectCanvasRepository


class CanvasAuthorityPolicyResolverTests(unittest.TestCase):
    def test_sqlite_authority_with_canonical_routing_uses_sqlite(self):
        decision = resolve_canvas_authority(authority_state="sqlite", canonical_routing_enabled=True)
        self.assertTrue(decision.use_sqlite)
        self.assertFalse(decision.split_brain_forbidden)
        self.assertEqual(decision.reason, "sqlite_authority_with_canonical_routing")

    def test_sqlite_authority_with_disabled_routing_is_split_brain_forbidden(self):
        decision = resolve_canvas_authority(authority_state="sqlite", canonical_routing_enabled=False)
        self.assertFalse(decision.use_sqlite)
        self.assertTrue(decision.split_brain_forbidden)
        self.assertEqual(decision.reason, "sqlite_authority_with_disabled_routing_would_fork_writes")

    def test_legacy_json_authority_never_forbids_legacy_recovery_routing(self):
        for enabled in (True, False):
            decision = resolve_canvas_authority(authority_state="legacy_json", canonical_routing_enabled=enabled)
            self.assertFalse(decision.use_sqlite)
            self.assertFalse(decision.split_brain_forbidden)
            self.assertEqual(decision.reason, "legacy_json_authority")

    def test_unavailable_authority_state_keeps_legacy_routing_available(self):
        decision = resolve_canvas_authority(authority_state=None, canonical_routing_enabled=False)
        self.assertFalse(decision.use_sqlite)
        self.assertFalse(decision.split_brain_forbidden)
        self.assertEqual(decision.reason, "authority_state_unavailable")


class ReadCanvasAuthorityStateTests(unittest.TestCase):
    def test_missing_database_reads_as_unavailable(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertIsNone(read_canvas_authority_state(Path(directory) / "absent.sqlite3"))

    def test_reads_activated_and_inactive_authority_states(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "workbench.sqlite3"
            repository = SqliteProjectCanvasRepository(database)
            self.assertEqual(repository.canvas_authority(), "legacy_json")
            self.assertEqual(read_canvas_authority_state(database), "legacy_json")
            repository.activate_sqlite_authority([])
            self.assertEqual(read_canvas_authority_state(database), "sqlite")

    def test_database_without_authority_state_table_reads_as_unavailable(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "unrelated.sqlite3"
            connection = sqlite3.connect(database)
            connection.execute("CREATE TABLE other (id INTEGER PRIMARY KEY)")
            connection.commit()
            connection.close()
            self.assertIsNone(read_canvas_authority_state(database))


if __name__ == "__main__":
    unittest.main()

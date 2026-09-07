import unittest
from pathlib import Path

import main


ROOT = Path(__file__).resolve().parents[1]


class RepositoryIndependenceTests(unittest.TestCase):
    def test_product_no_longer_exposes_source_repository_update_routes(self):
        paths = {route.path for route in main.app.routes if hasattr(route, "path")}
        self.assertTrue({
            "/api/check-update",
            "/api/update-connectivity",
            "/api/update-connectivity/probe",
            "/api/update-from-github",
            "/api/update-backups",
            "/api/update-rollback",
        }.isdisjoint(paths))

    def test_legacy_repository_self_update_implementation_is_removed(self):
        backend = (ROOT / "main.py").read_text(encoding="utf-8")
        shell = (ROOT / "static" / "index.html").read_text(encoding="utf-8")
        for token in (
            "GITHUB_REPO_URL",
            "GITHUB_VERSION_URL",
            "def update_from_github",
            "def schedule_self_restart",
            "def rollback_update",
            "def update_connectivity",
        ):
            self.assertNotIn(token, backend)
        for token in (
            "https://github.com/GUOXIAOLUO/canvas",
            "/api/update-from-github",
            "/api/check-update",
            "/api/update-connectivity",
            "function checkForUpdates",
            "function confirmProjectUpdate",
        ):
            self.assertNotIn(token, shell)

    def test_app_info_contains_local_runtime_information_only(self):
        info = main.app_info()
        self.assertIn("version", info)
        self.assertIn("server", info)
        self.assertNotIn("repo_url", info)
        self.assertNotIn("sources", info)

    def test_home_shell_does_not_offer_or_trigger_the_legacy_self_updater(self):
        source = (ROOT / "static" / "index.html").read_text(encoding="utf-8")
        self.assertNotIn('id="update-now-btn"', source)
        self.assertNotIn('id="project-version-badge"', source)
        self.assertNotIn("checkForUpdates();", source)

    def test_workbench_runtime_does_not_embed_github_hosting_urls(self):
        # R4-36: smart-canvas.html / smart-canvas.js retired; canvas.html is
        # the sole Canvas page.
        paths = [
            ROOT / "main.py",
            ROOT / "static" / "index.html",
            ROOT / "static" / "canvas.html",
            ROOT / "static" / "js" / "canvas-list.js",
            ROOT / "static" / "js" / "canvas.js",
            *(ROOT / "static" / "js" / "workbench" / "canvas").rglob("*.js"),
        ]
        for path in paths:
            self.assertNotIn("github.com", path.read_text(encoding="utf-8").lower(), path)

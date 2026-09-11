import tempfile
import unittest
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from workbench.api.projects import create_canonical_projects_router
from workbench.application.project_service import ProjectService
from workbench.repositories.project_repository import SqliteProjectRepository


class CanonicalProjectApiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        repository = SqliteProjectRepository(Path(self.temp.name) / "workbench.sqlite3")
        self.service = ProjectService(
            repository,
            canvas_reassigner=lambda **_: 2,
        )
        self.app = FastAPI()
        self.app.include_router(create_canonical_projects_router(project_service_factory=self._service))
        self.client = TestClient(self.app)

    def tearDown(self):
        self.temp.cleanup()

    def _service(self, *, with_canvas_reassigner=False):
        return self.service

    def test_canonical_project_api_delegates_full_lifecycle_to_service(self):
        listed = self.client.get("/api/v1/projects")
        self.assertEqual((listed.status_code, listed.json()[0]["name"]), (200, "默认项目"))

        created = self.client.post("/api/v1/projects", json={"name": "项目一"})
        self.assertEqual(created.status_code, 201)
        project_id = created.json()["id"]
        self.assertEqual(created.json()["revision"], 1)

        fetched = self.client.get(f"/api/v1/projects/{project_id}")
        self.assertEqual(fetched.json()["name"], "项目一")
        updated = self.client.put(f"/api/v1/projects/{project_id}", json={"name": "项目二", "order": 3})
        self.assertEqual((updated.status_code, updated.json()["name"], updated.json()["revision"]), (200, "项目二", 2))

        archived = self.client.delete(f"/api/v1/projects/{project_id}")
        self.assertEqual(archived.json(), {"ok": True, "project_id": project_id, "moved_canvas_count": 2})
        self.assertEqual(self.client.get(f"/api/v1/projects/{project_id}").status_code, 404)

    def test_canonical_project_api_returns_structured_validation_and_not_found_errors(self):
        invalid = self.client.post("/api/v1/projects", json={"name": "x", "unexpected": True})
        self.assertEqual(invalid.status_code, 422)
        missing = self.client.get("/api/v1/projects/missing")
        self.assertEqual(missing.json()["detail"]["code"], "not_found")
        default_archive = self.client.delete("/api/v1/projects/default")
        self.assertEqual(default_archive.json()["detail"]["code"], "invalid_request")

    def test_canonical_project_router_is_exported_by_the_transport_module(self):
        from workbench.api.projects import create_canonical_projects_router

        paths = {route.path for route in create_canonical_projects_router(project_service_factory=self._service).routes}
        self.assertEqual(paths, {
            "/api/v1/projects", "/api/v1/projects/{project_id}",
        })


if __name__ == "__main__":
    unittest.main()

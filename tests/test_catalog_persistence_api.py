import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from workbench.api.catalogs import create_catalogs_router
from workbench.application.catalog_service import CatalogService, CatalogServiceError
from workbench.domain.project.models import ProjectRecord
from workbench.repositories.catalog_repository import SqliteCatalogRepository
from workbench.repositories.sqlite_project_canvas_repository import SqliteProjectCanvasRepository


class CatalogPersistenceApiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.database = Path(self.temp.name) / "workbench.sqlite3"
        self.clock = datetime(2026, 9, 14, tzinfo=UTC)
        projects = SqliteProjectCanvasRepository(self.database, clock=lambda: self.clock)
        projects.create_project(ProjectRecord(id="project-1", name="Project", workspace_id="workspace-1", created_by="owner", created_at=self.clock, updated_at=self.clock))

    def tearDown(self): self.temp.cleanup()

    def factory(self, actor="owner"):
        return CatalogService(SqliteCatalogRepository(self.database, clock=lambda: self.clock), actor_id=actor, clock=lambda: self.clock)

    def schema(self):
        return {"id": "schema-1", "name": "Products", "attributes": [{"key": "sku", "label": "SKU", "value_type": "text", "required": True}]}

    def test_catalog_and_item_versions_survive_restart(self):
        service = self.factory()
        catalog = service.create(workspace_id="workspace-1", project_id="project-1", scope="project", name="Products", schema=self.schema(), metadata={})
        _, item, first = service.create_item(catalog.id, title="Chair", attributes={"sku": "C-1"}, media_refs=(), metadata={})
        second = service.append_version(catalog.id, item.id, attributes={"sku": "C-2"}, media_refs=(), metadata={"source": "refresh"})
        reopened = CatalogService(SqliteCatalogRepository(self.database, clock=lambda: self.clock), actor_id="owner")
        self.assertEqual(reopened.get(catalog.id).item_ids, (item.id,))
        versions = reopened.list_versions(item.id)
        self.assertEqual([version.ordinal for version in versions], [1, 2])
        self.assertEqual(reopened.get_item(item.id).current_version_id, versions[-1].id)
        self.assertNotEqual(first.id, second.id)

    def test_workspace_scope_is_persisted_and_api_versions_item(self):
        service_factory = lambda actor: self.factory(actor)
        app = FastAPI(); app.include_router(create_catalogs_router(service_factory=service_factory)); client = TestClient(app)
        headers = {"X-User-ID": "owner"}
        created = client.post("/api/v1/catalogs", headers=headers, json={"workspace_id": "workspace-1", "scope": "workspace", "name": "Shared", "schema": self.schema()})
        self.assertEqual((created.status_code, created.json()["scope"]), (201, "workspace"))
        catalog_id = created.json()["id"]
        item = client.post(f"/api/v1/catalogs/{catalog_id}/items", headers=headers, json={"title": "Chair", "attributes": {"sku": "C-1"}})
        self.assertEqual(item.status_code, 201)
        item_id = item.json()["item"]["id"]
        version = client.post(f"/api/v1/catalogs/{catalog_id}/items/{item_id}/versions", headers=headers, json={"attributes": {"sku": "C-2"}})
        self.assertEqual((version.status_code, version.json().get("ordinal")), (201, 2), version.text)
        items = client.get(f"/api/v1/catalogs/{catalog_id}/items", headers=headers)
        self.assertEqual((items.status_code, len(items.json()), items.json()[0]["id"]), (200, 1, item_id), items.text)
        listed = client.get("/api/v1/catalogs?workspace_id=workspace-1", headers=headers)
        self.assertEqual((listed.status_code, len(listed.json())), (200, 1))

    def test_project_catalog_cannot_claim_a_different_workspace(self):
        service = self.factory()
        with self.assertRaises(CatalogServiceError):
            service.create(workspace_id="other-workspace", project_id="project-1", scope="project", name="Invalid", schema=self.schema(), metadata={})


if __name__ == "__main__": unittest.main()

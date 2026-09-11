import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from workbench.api.collections import create_canonical_collections_router
from workbench.application.collection_service import CollectionService
from workbench.domain.collection import Collection, CollectionColumn, CollectionItem, CollectionLiteralCell, CollectionSchema
from workbench.repositories.collection_repository import CollectionNotFoundError, CollectionStaleRevisionError, SqliteCollectionRepository
from workbench.repositories.sqlite_project_canvas_repository import SqliteProjectCanvasRepository
from workbench.domain.project.models import ProjectRecord


class CollectionPersistenceApiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.database = Path(self.temp.name) / "workbench.sqlite3"
        self.clock = datetime(2026, 9, 11, tzinfo=UTC)
        projects = SqliteProjectCanvasRepository(self.database, clock=lambda: self.clock)
        projects.create_project(ProjectRecord(
            id="project-1", name="Project", workspace_id="local", created_by="owner",
            created_at=self.clock, updated_at=self.clock,
        ))
        self.repository = SqliteCollectionRepository(self.database, clock=lambda: self.clock)

    def tearDown(self):
        self.temp.cleanup()

    def collection(self, collection_id="collection-1"):
        return Collection(
            id=collection_id,
            project_id="project-1",
            name="References",
            schema=CollectionSchema(
                id="schema-1", name="Reference schema",
                columns=[CollectionColumn(id="note", key="note", label="Note", value_type="literal")],
            ),
            items=[CollectionItem(id="item-1", order=1, values={"note": CollectionLiteralCell(value="hello")})],
            default_view={"mode": "grid"},
        )

    def test_collection_survives_sqlite_reopen_and_is_loaded_by_id(self):
        created = self.repository.create(self.collection(), actor_id="owner")
        reopened = SqliteCollectionRepository(self.database, clock=lambda: self.clock)

        self.assertEqual(reopened.get(created.id, actor_id="owner"), created)
        self.assertEqual([item.id for item in reopened.list("project-1", actor_id="owner")], ["collection-1"])

    def test_collection_update_uses_revision_and_project_authorization(self):
        created = self.repository.create(self.collection(), actor_id="owner")
        changed = created.model_copy(update={"name": "Changed"})
        updated = self.repository.replace(changed, expected_revision=1, actor_id="owner")
        self.assertEqual((updated.name, updated.revision), ("Changed", 2))

        with self.assertRaises(CollectionStaleRevisionError) as stale:
            self.repository.replace(changed, expected_revision=1, actor_id="owner")
        self.assertEqual(stale.exception.current_revision, 2)
        with self.assertRaises(PermissionError):
            self.repository.get(created.id, actor_id="viewer")
        with self.assertRaises(CollectionNotFoundError):
            self.repository.get("missing", actor_id="owner")

    def test_canonical_collection_api_crud_and_restart_reference(self):
        service_factory = lambda actor_id: CollectionService(
            SqliteCollectionRepository(self.database, clock=lambda: self.clock), actor_id=actor_id,
        )
        app = FastAPI()
        app.include_router(create_canonical_collections_router(service_factory=service_factory))
        client = TestClient(app)
        headers = {"X-User-ID": "owner"}
        schema = {"id": "schema-1", "name": "Schema", "columns": [{"id": "note", "key": "note", "label": "Note", "value_type": "literal"}]}

        created = client.post("/api/v1/collections", headers=headers, json={
            "project_id": "project-1", "name": "API collection", "schema": schema,
            "items": [{"id": "item-1", "order": 1, "values": {"note": {"type": "literal", "value": "api"}}}],
        })
        self.assertEqual((created.status_code, created.json()["revision"]), (201, 1))
        collection_id = created.json()["id"]
        self.assertEqual(client.get(f"/api/v1/collections/{collection_id}", headers=headers).status_code, 200)
        listed = client.get("/api/v1/collections?project_id=project-1", headers=headers)
        self.assertEqual((listed.status_code, len(listed.json()), listed.json()[0]["name"]), (200, 1, "API collection"))
        updated = client.put(f"/api/v1/collections/{collection_id}", headers=headers, json={
            "expected_revision": 1, "name": "Updated collection",
        })
        self.assertEqual((updated.status_code, updated.json()["name"], updated.json()["revision"]), (200, "Updated collection", 2))
        stale = client.put(f"/api/v1/collections/{collection_id}", headers=headers, json={"expected_revision": 1, "name": "stale"})
        self.assertEqual(stale.status_code, 409)
        self.assertEqual(client.delete(f"/api/v1/collections/{collection_id}", headers=headers).status_code, 204)
        self.assertEqual(client.get(f"/api/v1/collections/{collection_id}", headers=headers).status_code, 404)


if __name__ == "__main__":
    unittest.main()

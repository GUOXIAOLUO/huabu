import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from workbench.api.entities import create_entities_router
from workbench.application.authorization import AuthorizationError
from workbench.application.entity_service import EntityService
from workbench.domain.entity import (
    EntityVersionLineage,
    EntityVersionPayload,
    EntityVersionRef,
)
from workbench.domain.project.models import ProjectMember, ProjectRecord
from workbench.repositories.entity_repository import SqliteEntityRepository
from workbench.repositories.entity_repository import EntityConflictError
from workbench.repositories.sqlite_project_canvas_repository import SqliteProjectCanvasRepository


class EntityVersionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.database = Path(self.temp.name) / "workbench.sqlite3"
        self.clock = datetime(2026, 9, 14, tzinfo=UTC)
        projects = SqliteProjectCanvasRepository(self.database, clock=lambda: self.clock)
        projects.create_project(
            ProjectRecord(
                id="project-1", name="Project", workspace_id="workspace-1",
                created_by="owner", created_at=self.clock, updated_at=self.clock,
            ),
            ProjectMember(
                project_id="project-1", actor_id="owner", role="owner",
                created_at=self.clock,
            ),
        )
        self.repo = SqliteEntityRepository(self.database)
        ids = iter(("entity-1", "version-1", "version-2"))
        self.service = EntityService(
            self.repo, actor_id="owner", id_factory=ids.__next__, clock=lambda: self.clock
        )

    def tearDown(self):
        self.temp.cleanup()

    def payload(self, **overrides):
        value = {"properties": {"name": "Initial"}, "state": "draft", "metadata": {}}
        value.update(overrides)
        return EntityVersionPayload(**value)

    def test_version_is_immutable_and_pins_a_complete_snapshot(self):
        entity, version = self.service.create_with_version(
            project_id="project-1", entity_type="fact", definition_id="definition-1",
            payload=self.payload(),
            lineage=EntityVersionLineage(source_refs=("asset-version-1",)),
        )

        self.assertEqual(entity.current_version_id, version.id)
        self.assertEqual(version.author_id, "owner")
        self.assertEqual(version.ordinal, 1)
        self.assertEqual(version.lineage.source_refs, ("asset-version-1",))
        self.assertEqual(version.ref(), EntityVersionRef(entity_id="entity-1", version_id="version-1"))
        with self.assertRaises(ValidationError):
            version.payload.state = "active"

    def test_append_creates_a_new_version_without_overwriting_history(self):
        entity, first = self.service.create_with_version(
            project_id="project-1", entity_type="fact", definition_id="definition-1",
            payload=self.payload(),
        )
        second = self.service.append_version(
            entity_id=entity.id,
            payload=self.payload(properties={"name": "Updated"}, state="active"),
        )

        self.assertEqual(second.ordinal, 2)
        self.assertEqual(second.lineage.parent_version_id, first.id)
        self.assertEqual([v.id for v in self.service.list_versions(entity.id)], [first.id, second.id])
        current = self.service.get(entity.id)
        self.assertEqual(current.current_version_id, second.id)
        self.assertEqual(current.properties["name"], "Updated")

    def test_lineage_parent_must_belong_to_the_entity(self):
        entity, _ = self.service.create_with_version(
            project_id="project-1", entity_type="fact", definition_id="definition-1",
            payload=self.payload(),
        )
        with self.assertRaises(EntityConflictError):
            self.service.append_version(
                entity_id=entity.id,
                payload=self.payload(properties={"name": "Invalid parent"}),
                lineage=EntityVersionLineage(parent_version_id="other-entity-version"),
            )

    def test_repository_requires_project_authorization_and_survives_restart(self):
        entity, version = self.service.create_with_version(
            project_id="project-1", entity_type="fact", definition_id="definition-1",
            payload=self.payload(),
        )
        reopened = EntityService(SqliteEntityRepository(self.database), actor_id="owner")
        self.assertEqual(reopened.get_version(entity.id, version.id), version)
        with self.assertRaises(AuthorizationError):
            EntityService(self.repo, actor_id="stranger").get(entity.id)

    def test_api_exposes_entity_and_version_reads_and_writes(self):
        app = FastAPI()
        api_ids = iter(("entity-api", "version-api"))
        api_service = EntityService(
            self.repo, actor_id="owner", id_factory=api_ids.__next__, clock=lambda: self.clock
        )
        app.include_router(create_entities_router(service_factory=lambda actor: api_service))
        client = TestClient(app)
        headers = {"X-User-ID": "owner"}
        created = client.post(
            "/api/v1/entities", headers=headers,
            json={
                "project_id": "project-1", "entity_type": "fact",
                "definition_id": "definition-1", "properties": {"name": "API"},
            },
        )
        self.assertEqual(created.status_code, 201)
        entity_id = created.json()["id"]
        version = client.post(
            f"/api/v1/entities/{entity_id}/versions", headers=headers,
            json={"payload": {"properties": {"name": "API v2"}, "state": "active"}},
        )
        self.assertEqual(version.status_code, 201)
        self.assertEqual(client.get(f"/api/v1/entities/{entity_id}/versions", headers=headers).status_code, 200)
        self.assertEqual(client.get(f"/api/v1/entities/{entity_id}/versions/{version.json()['id']}", headers=headers).status_code, 200)


if __name__ == "__main__":
    unittest.main()

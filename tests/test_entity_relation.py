import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from workbench.api.entity_relations import create_entity_relations_router
from workbench.application.authorization import AuthorizationError
from workbench.application.entity_relation_service import EntityRelationService
from workbench.domain.entity import EntityRelation, EntityRelationEndpoint
from workbench.domain.project.models import ProjectMember, ProjectRecord
from workbench.repositories.entity_relation_repository import SqliteEntityRelationRepository
from workbench.repositories.sqlite_project_canvas_repository import SqliteProjectCanvasRepository


class EntityRelationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.database = Path(self.temp.name) / "workbench.sqlite3"
        now = datetime(2026, 9, 14, tzinfo=UTC)
        projects = SqliteProjectCanvasRepository(self.database, clock=lambda: now)
        projects.create_project(
            ProjectRecord(
                id="project-1", name="Project", workspace_id="workspace-1",
                created_by="owner", created_at=now, updated_at=now,
            ),
            ProjectMember(project_id="project-1", actor_id="owner", role="owner", created_at=now),
        )
        self.repo = SqliteEntityRelationRepository(self.database)
        ids = iter(("relation-1", "relation-2"))
        self.service = EntityRelationService(self.repo, actor_id="owner", id_factory=ids.__next__)
        self.from_ref = EntityRelationEndpoint(resource_type="entity", resource_id="entity-1", version_id="version-1")
        self.to_ref = EntityRelationEndpoint(resource_type="catalog_item", resource_id="item-1")

    def tearDown(self):
        self.temp.cleanup()

    def test_relation_is_generic_version_aware_and_not_a_canvas_edge(self):
        relation = self.service.create(
            project_id="project-1", relation_type="requires",
            from_endpoint=self.from_ref, to_endpoint=self.to_ref,
            metadata={"source": "brief"},
        )
        self.assertEqual(relation.from_endpoint.version_id, "version-1")
        self.assertEqual(relation.revision, 1)
        self.assertNotIn("canvas", relation.model_dump(mode="json"))
        with self.assertRaises(ValidationError):
            EntityRelation(id="r", project_id="p", relation_type="same", from_endpoint=self.from_ref, to_endpoint=self.from_ref)

    def test_query_service_filters_by_relation_type_and_endpoint(self):
        first = self.service.create(project_id="project-1", relation_type="requires", from_endpoint=self.from_ref, to_endpoint=self.to_ref)
        self.service.create(
            project_id="project-1", relation_type="supports",
            from_endpoint=EntityRelationEndpoint(resource_type="entity", resource_id="entity-2"),
            to_endpoint=self.to_ref,
        )
        self.assertEqual([item.id for item in self.service.query("project-1", relation_type="requires")], [first.id])
        self.assertEqual([item.id for item in self.service.query("project-1", resource_id="entity-1")], [first.id])
        self.assertEqual(len(self.service.list("project-1")), 2)

    def test_query_with_type_and_id_matches_the_same_endpoint(self):
        first = self.service.create(project_id="project-1", relation_type="requires", from_endpoint=self.from_ref, to_endpoint=self.to_ref)
        self.service.create(
            project_id="project-1", relation_type="supports",
            from_endpoint=EntityRelationEndpoint(resource_type="entity", resource_id="entity-2"),
            to_endpoint=EntityRelationEndpoint(resource_type="asset", resource_id="entity-1"),
        )
        self.assertEqual(
            [item.id for item in self.service.query("project-1", resource_type="entity", resource_id="entity-1")],
            [first.id],
        )

    def test_relations_are_project_authorized_and_survive_restart(self):
        relation = self.service.create(project_id="project-1", relation_type="contains", from_endpoint=self.from_ref, to_endpoint=self.to_ref)
        reopened = EntityRelationService(SqliteEntityRelationRepository(self.database), actor_id="owner")
        self.assertEqual(reopened.get(relation.id), relation)
        with self.assertRaises(AuthorizationError):
            EntityRelationService(self.repo, actor_id="stranger").list("project-1")

    def test_api_creates_and_queries_relations_outside_canvas(self):
        app = FastAPI()
        app.include_router(create_entity_relations_router(service_factory=lambda actor: self.service))
        client = TestClient(app)
        response = client.post(
            "/api/v1/entity-relations", headers={"X-User-ID": "owner"},
            json={
                "project_id": "project-1", "relation_type": "requires",
                "from": {"resource_type": "entity", "resource_id": "entity-api", "version_id": "version-api"},
                "to": {"resource_type": "asset", "resource_id": "asset-api"},
            },
        )
        self.assertEqual(response.status_code, 201)
        queried = client.get(
            "/api/v1/entity-relations?project_id=project-1&resource_id=entity-api",
            headers={"X-User-ID": "owner"},
        )
        self.assertEqual(queried.status_code, 200)
        self.assertEqual(queried.json()[0]["from"]["version_id"], "version-api")

        invalid = client.post(
            "/api/v1/entity-relations", headers={"X-User-ID": "owner"},
            json={
                "project_id": "project-1", "relation_type": "requires",
                "from": {"resource_type": "entity", "resource_id": "entity-api"},
                "to": {"resource_type": "asset", "resource_id": "asset-api"},
                "metadata": {"api_key": "must-not-persist"},
            },
        )
        self.assertEqual(invalid.status_code, 400)


if __name__ == "__main__":
    unittest.main()

import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from workbench.api.project_knowledge_context import create_project_knowledge_context_router
from workbench.application.entity_service import EntityService
from workbench.application.knowledge_entry_service import KnowledgeEntryService
from workbench.application.project_knowledge_context_service import ProjectKnowledgeContextService
from workbench.domain.entity import EntityRecord
from workbench.domain.knowledge import KnowledgeSnapshot, ProjectKnowledgeContextPolicy, ProjectKnowledgeContextResource
from workbench.domain.project.models import ProjectMember, ProjectRecord
from workbench.repositories.entity_repository import SqliteEntityRepository
from workbench.repositories.knowledge_entry_repository import SqliteKnowledgeEntryRepository
from workbench.repositories.sqlite_project_canvas_repository import SqliteProjectCanvasRepository


class ProjectKnowledgeContextTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.database = Path(self.temp.name) / "workbench.sqlite3"
        now = datetime(2026, 9, 14, tzinfo=UTC)
        projects = SqliteProjectCanvasRepository(self.database, clock=lambda: now)
        projects.create_project(
            ProjectRecord(id="project-1", name="Project", workspace_id="workspace-1", created_by="owner", created_at=now, updated_at=now),
            ProjectMember(project_id="project-1", actor_id="owner", role="owner", created_at=now),
        )
        self.entity_service = EntityService(SqliteEntityRepository(self.database), actor_id="owner", id_factory=iter(("entity-1",)).__next__)
        self.knowledge_service = KnowledgeEntryService(SqliteKnowledgeEntryRepository(self.database), actor_id="owner", id_factory=iter(("knowledge-1", "knowledge-2")).__next__)

    def tearDown(self):
        self.temp.cleanup()

    def test_build_is_policy_scoped_and_snapshot_refs_preserve_provenance(self):
        entity = self.entity_service.create(project_id="project-1", entity_type="room", definition_id="room-definition", properties={"name": "Study"})
        project_entry = self.knowledge_service.create(project_id="project-1", content="Project constraint", structured_payload=None, source_refs=("source-project",), tags=("constraint",), scope="project", metadata={})
        common_entry = self.knowledge_service.create(project_id="project-1", content="Common guidance", structured_payload=None, source_refs=("source-common",), tags=(), scope="common", metadata={})
        resource = ProjectKnowledgeContextResource(resource_type="asset", resource_id="asset-1", version_id="asset-version-1", scope="project", provenance=("upload-1",))
        workspace_resource = ProjectKnowledgeContextResource(resource_type="catalog", resource_id="catalog-1", scope="workspace")
        service = ProjectKnowledgeContextService(
            entity_service=self.entity_service,
            knowledge_service=self.knowledge_service,
            resource_readers=(lambda project_id: (resource, workspace_resource) if project_id == "project-1" else (),),
            clock=lambda: datetime(2026, 9, 14, 1, tzinfo=UTC),
        )

        default = service.build(project_id="project-1")
        self.assertEqual([item.id for item in default.entities], [entity.id])
        self.assertEqual([item.id for item in default.knowledge], [project_entry.id])
        self.assertEqual([item.resource_id for item in default.resources], ["asset-1"])
        self.assertEqual(default.snapshot_refs[0].version_id, None)
        self.assertEqual(default.snapshot_refs[0].kind, "entity")
        self.assertEqual(default.snapshot_refs[1].provenance, ("source-project",))
        self.assertEqual(default.snapshot_refs[2].version_id, "asset-version-1")
        self.assertEqual(default.generated_at.year, 2026)

        broadened = service.build(project_id="project-1", policy=ProjectKnowledgeContextPolicy(knowledge_scopes=("project", "common"), max_entities=0, max_knowledge=1, max_resources=0))
        self.assertEqual(broadened.entities, ())
        self.assertEqual([item.id for item in broadened.knowledge], [project_entry.id])
        self.assertEqual(broadened.resources, ())
        self.assertEqual(common_entry.scope, "common")
        workspace = service.build(project_id="project-1", policy=ProjectKnowledgeContextPolicy(resource_scopes=("project", "workspace")))
        self.assertEqual([item.resource_id for item in workspace.resources], ["asset-1", "catalog-1"])

        snapshot = service.snapshot(project_id="project-1")
        self.assertIsInstance(snapshot, KnowledgeSnapshot)
        self.assertTrue(snapshot.snapshot_id)
        self.assertEqual(snapshot.captured_at.year, 2026)

    def test_api_returns_inspectable_context_and_requires_project_membership(self):
        context = ProjectKnowledgeContextService(entity_service=self.entity_service, knowledge_service=self.knowledge_service)
        app = FastAPI()
        app.include_router(create_project_knowledge_context_router(service_factory=lambda actor: context))
        client = TestClient(app)
        response = client.get("/api/v1/projects/project-1/knowledge-context", headers={"X-User-ID": "owner"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["project_id"], "project-1")
        self.assertIn("snapshot_refs", response.json())
        self.assertEqual(client.get("/api/v1/projects/project-1/knowledge-context").status_code, 401)


if __name__ == "__main__":
    unittest.main()

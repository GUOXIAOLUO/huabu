import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from workbench.api.knowledge_entries import create_knowledge_entries_router
from workbench.application.knowledge_entry_service import KnowledgeEntryService
from workbench.domain.knowledge import KnowledgeEntry
from workbench.domain.project.models import ProjectMember, ProjectRecord
from workbench.repositories.knowledge_entry_repository import SqliteKnowledgeEntryRepository
from workbench.repositories.sqlite_project_canvas_repository import SqliteProjectCanvasRepository


class KnowledgeEntryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.database = Path(self.temp.name) / "workbench.sqlite3"
        now = datetime(2026, 9, 14, tzinfo=UTC)
        projects = SqliteProjectCanvasRepository(self.database, clock=lambda: now)
        projects.create_project(
            ProjectRecord(id="project-1", name="Project", workspace_id="workspace-1", created_by="owner", created_at=now, updated_at=now),
            ProjectMember(project_id="project-1", actor_id="owner", role="owner", created_at=now),
        )
        self.repository = SqliteKnowledgeEntryRepository(self.database)
        ids = iter(("entry-1", "entry-2"))
        self.service = KnowledgeEntryService(self.repository, actor_id="owner", id_factory=ids.__next__)

    def tearDown(self):
        self.temp.cleanup()

    def test_every_entry_requires_a_unique_source_reference_and_payload(self):
        with self.assertRaises(ValidationError):
            KnowledgeEntry(id="e", project_id="p", source_refs=(), content="fact")
        with self.assertRaises(ValidationError):
            KnowledgeEntry(id="e", project_id="p", source_refs=("source-1", "source-1"), content="fact")
        with self.assertRaises(ValidationError):
            KnowledgeEntry(id="e", project_id="p", source_refs=("source-1",))
        entry = KnowledgeEntry(id="e", project_id="p", source_refs=("source-1",), structured_payload={"fact": True})
        self.assertEqual(entry.source_refs, ("source-1",))

    def test_persists_queries_and_survives_restart_with_project_authorization(self):
        first = self.service.create(project_id="project-1", content="Blue desk", structured_payload=None, source_refs=("source-1",), tags=("furniture",), scope="project", metadata={"room": "office"})
        second = self.service.create(project_id="project-1", content=None, structured_payload={"count": 2}, source_refs=("source-2",), tags=("measure",), scope="project", metadata={})
        self.assertEqual([item.id for item in self.service.list(project_id="project-1", query="blue")], [first.id])
        self.assertEqual([item.id for item in self.service.list(project_id="project-1", tag="measure")], [second.id])
        self.assertEqual([item.id for item in self.service.search(project_id="project-1", query="office")], [first.id])
        self.assertEqual([item.id for item in self.service.search(project_id="project-1", source_ref="source-2")], [second.id])
        reopened = KnowledgeEntryService(SqliteKnowledgeEntryRepository(self.database), actor_id="owner")
        self.assertEqual(reopened.get(first.id), first)
        with self.assertRaises(PermissionError):
            KnowledgeEntryService(self.repository, actor_id="stranger").get(first.id)

    def test_api_exposes_create_get_and_query(self):
        app = FastAPI()
        ids = iter(("api-entry",))
        service = KnowledgeEntryService(self.repository, actor_id="owner", id_factory=ids.__next__)
        app.include_router(create_knowledge_entries_router(service_factory=lambda actor: service))
        client = TestClient(app)
        response = client.post("/api/v1/knowledge-entries", headers={"X-User-ID": "owner"}, json={
            "project_id": "project-1", "content": "Verified note", "source_refs": ["source-1"], "tags": ["verified"],
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(client.get("/api/v1/knowledge-entries", headers={"X-User-ID": "owner"}, params={"project_id": "project-1", "query": "verified"}).status_code, 200)
        search = client.get("/api/v1/knowledge-entries/search", headers={"X-User-ID": "owner"}, params={"project_id": "project-1", "query": "verified", "source_ref": "source-1"})
        self.assertEqual(search.status_code, 200)
        self.assertEqual([item["id"] for item in search.json()], ["api-entry"])
        self.assertEqual(client.get("/api/v1/knowledge-entries/api-entry", headers={"X-User-ID": "owner"}).status_code, 200)
        self.assertEqual(client.post("/api/v1/knowledge-entries", headers={"X-User-ID": "owner"}, json={"project_id": "project-1", "content": "No source"}).status_code, 422)


if __name__ == "__main__":
    unittest.main()

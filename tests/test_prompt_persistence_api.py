import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import Mock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from workbench.api.prompts import create_canonical_prompts_router
from workbench.application.prompt_service import PromptService
from workbench.application.prompt_registry import PromptRegistration, PromptRegistry
from workbench.domain.prompt import PromptRef
from workbench.domain.project.models import ProjectRecord
from workbench.repositories.prompt_repository import SqlitePromptRepository
from workbench.repositories.sqlite_project_canvas_repository import SqliteProjectCanvasRepository


class PromptPersistenceApiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.database = Path(self.temp.name) / "workbench.sqlite3"
        self.clock = datetime(2026, 9, 11, tzinfo=UTC)
        projects = SqliteProjectCanvasRepository(self.database, clock=lambda: self.clock)
        projects.create_project(ProjectRecord(
            id="project-1", name="Project", workspace_id="local", created_by="owner",
            created_at=self.clock, updated_at=self.clock,
        ))

    def tearDown(self):
        self.temp.cleanup()

    def client(self):
        app = FastAPI()
        app.include_router(create_canonical_prompts_router(service_factory=lambda actor: PromptService(
            SqlitePromptRepository(self.database, clock=lambda: self.clock, id_factory=lambda: "prompt-1"), actor_id=actor,
            clock=lambda: self.clock,
        )))
        return TestClient(app)

    def test_prompt_versions_are_immutable_readable_and_resolvable_by_ref(self):
        client = self.client()
        headers = {"X-User-ID": "owner"}
        created = client.post("/api/v1/prompts", headers=headers, json={
            "project_id": "project-1", "name": "Image brief", "content": "first prompt",
        })
        self.assertEqual((created.status_code, created.json()["current_version"]), (201, 1))
        prompt_id = created.json()["id"]
        second = client.post(f"/api/v1/prompts/{prompt_id}/versions", headers=headers, json={"content": "second prompt"})
        self.assertEqual((second.status_code, second.json()["version"]), (201, 2))
        first = client.get(f"/api/v1/prompts/{prompt_id}/versions/1", headers=headers)
        latest = client.get(f"/api/v1/prompts/{prompt_id}/versions/2", headers=headers)
        definition = client.get(f"/api/v1/prompts/{prompt_id}", headers=headers)
        self.assertEqual((first.status_code, first.json()["content"]), (200, "first prompt"))
        self.assertEqual((latest.status_code, latest.json()["content"]), (200, "second prompt"))
        self.assertEqual(definition.json()["current_version"], 2)
        self.assertEqual(client.get(f"/api/v1/prompts/{prompt_id}/versions/3", headers=headers).status_code, 404)

    def test_prompt_api_enforces_project_read_and_edit_authorization(self):
        client = self.client()
        created = client.post("/api/v1/prompts", headers={"X-User-ID": "owner"}, json={
            "project_id": "project-1", "name": "Private", "content": "secret",
        })
        prompt_id = created.json()["id"]
        self.assertEqual(client.get(f"/api/v1/prompts/{prompt_id}", headers={"X-User-ID": "other"}).status_code, 403)
        self.assertEqual(client.post(f"/api/v1/prompts/{prompt_id}/versions", headers={"X-User-ID": "other"}, json={"content": "bad"}).status_code, 403)

    def test_prompt_registry_lists_project_and_explicit_system_package_user_sources(self):
        repository = SqlitePromptRepository(self.database, clock=lambda: self.clock, id_factory=lambda: "prompt-1")
        service = PromptService(repository, actor_id="owner", clock=lambda: self.clock)
        service.create(project_id="project-1", name="Project brief", content="project", metadata={"tags": ["brief"]})
        registrations = [
            PromptRegistration(prompt=PromptRef(prompt_id="system-1", version=1), name="System guide", source="system", tags=("guide",)),
            PromptRegistration(prompt=PromptRef(prompt_id="package-1", version=2), name="Package brief", source="package", source_id="wholehouse"),
            PromptRegistration(prompt=PromptRef(prompt_id="user-1", version=1), name="My private template", source="user", source_id="owner"),
        ]
        registry = PromptRegistry(repository, actor_id="owner", registrations=registrations)
        self.assertEqual([entry.source for entry in registry.discover("project-1", query="BRIEF")], ["package", "project"])
        self.assertEqual([entry.name for entry in registry.discover("project-1", source="system")], ["System guide"])
        self.assertEqual(registry.discover("project-1", query="private")[0].source_id, "owner")
        with self.assertRaises(PermissionError):
            registry_for_other = PromptRegistry(repository, actor_id="other")
            registry_for_other.discover("project-1")
        other_repository = Mock()
        other_repository.list.return_value = []
        self.assertEqual(PromptRegistry(other_repository, actor_id="other", registrations=registrations).discover("project-1", query="private"), [])

    def test_prompt_registry_api_uses_explicit_registration_metadata_and_search(self):
        registration = PromptRegistration(prompt=PromptRef(prompt_id="system-1", version=1), name="System guide", source="system", tags=("guide",))
        app = FastAPI()
        app.include_router(create_canonical_prompts_router(
            service_factory=lambda actor: PromptService(SqlitePromptRepository(self.database, clock=lambda: self.clock, id_factory=lambda: "prompt-api"), actor_id=actor),
            registry_factory=lambda actor: PromptRegistry(SqlitePromptRepository(self.database, clock=lambda: self.clock), actor_id=actor, registrations=[registration]),
        ))
        response = TestClient(app).get("/api/v1/prompts", params={"project_id": "project-1", "q": "guide", "source": "system"}, headers={"X-User-ID": "owner"})
        self.assertEqual((response.status_code, response.json()[0]["prompt"]["prompt_id"]), (200, "system-1"))


if __name__ == "__main__":
    unittest.main()

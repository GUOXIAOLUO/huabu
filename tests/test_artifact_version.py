import tempfile
import unittest
from datetime import UTC, datetime

from workbench.application.artifact_service import ArtifactService
from workbench.application.authorization import AuthorizationError
from workbench.domain.artifact import ArtifactVersionContentRef, ArtifactVersionLineage
from workbench.domain.project.models import ProjectMember, ProjectRecord
from workbench.repositories.artifact_repository import SqliteArtifactRepository
from workbench.repositories.sqlite_project_canvas_repository import SqliteProjectCanvasRepository


class ArtifactVersionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        db = self.temp.name + "/workbench.sqlite3"
        projects = SqliteProjectCanvasRepository(db)
        now = datetime(2026, 1, 1, tzinfo=UTC)
        projects.create_project(ProjectRecord(id="p1", name="Project", workspace_id="w1", created_by="owner", created_at=now, updated_at=now), ProjectMember(project_id="p1", actor_id="owner", role="owner", created_at=now))
        self.repo = SqliteArtifactRepository(db)
        self.service = ArtifactService(self.repo, actor_id="owner", id_factory=iter(("artifact-1", "version-1")).__next__, clock=lambda: now)

    def tearDown(self): self.temp.cleanup()

    def test_version_is_immutable_and_carries_complete_lineage(self):
        artifact = self.service.create(project_id="p1", type="analysis", title="Analysis")
        version = self.service.append_version(
            artifact_id=artifact.id,
            content_ref=ArtifactVersionContentRef(location="artifacts/a.json", checksum="sha256:" + "a" * 64, mime_type="application/json", size_bytes=12),
            lineage=ArtifactVersionLineage(run_id="run-1", attempt_id="attempt-1", input_refs=("input-1",), prompt_version_ref="prompt-v1", model_ref="model-1", skill_version_ref="skill-v1"),
        )
        self.assertEqual(version.lineage.run_id, "run-1")
        self.assertEqual(self.service.list_versions(artifact.id)[0], version)
        with self.assertRaises(Exception): version.content_ref.size_bytes = 13

    def test_versions_append_without_overwriting_prior_version(self):
        artifact = self.service.create(project_id="p1", type="analysis", title="Analysis")
        content = ArtifactVersionContentRef(location="artifacts/a", checksum="sha256:" + "a" * 64, mime_type="text/plain", size_bytes=1)
        first = self.service.append_version(artifact_id=artifact.id, content_ref=content, lineage=ArtifactVersionLineage(run_id="r1", attempt_id="a1"))
        self.service._id_factory = iter(("version-2",)).__next__
        second = self.service.append_version(artifact_id=artifact.id, content_ref=content, lineage=ArtifactVersionLineage(run_id="r2", attempt_id="a2"))
        self.assertEqual([item.id for item in self.service.list_versions(artifact.id)], [first.id, second.id])

    def test_reads_and_writes_require_project_authorization(self):
        artifact = self.service.create(project_id="p1", type="analysis", title="Analysis")
        with self.assertRaises(AuthorizationError):
            ArtifactService(self.repo, actor_id="stranger").get(artifact.id)


if __name__ == "__main__": unittest.main()

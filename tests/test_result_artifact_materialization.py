import unittest
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

from workbench.application.result_artifact_materialization import (
    ResultArtifactMaterializationError,
    ResultArtifactMaterializationService,
)
from workbench.domain.artifact import ArtifactVersionContentRef


ROOT = Path(__file__).resolve().parents[1]


class ResultArtifactMaterializationTests(unittest.TestCase):
    def service(self, selected=True):
        class Artifacts:
            def __init__(self):
                self.calls = []

            def create_with_version(self, **kwargs):
                self.calls.append(kwargs)
                artifact = SimpleNamespace(id='artifact-1', project_id=kwargs['project_id'], version_ids=('version-1',))
                version = SimpleNamespace(id='version-1', artifact_id='artifact-1', lineage=kwargs['lineage'])
                return artifact, version

        artifacts = Artifacts()
        selections = SimpleNamespace(list_for_run=lambda run_id: [SimpleNamespace(
            attempt_id='attempt-1', output_name='analysis.json', ordinal=0, selected=selected,
        )])
        runs = SimpleNamespace(get=lambda run_id: SimpleNamespace(project_id='project-1', task_id='task-1'))
        attempts = SimpleNamespace(get=lambda attempt_id: SimpleNamespace(run_id='run-1'))
        service = ResultArtifactMaterializationService(
            artifacts, selections, runs, attempts, actor_id='owner',
            id_factory=iter(['artifact-1', 'version-1']).__next__,
            clock=lambda: datetime(2026, 9, 14, tzinfo=UTC),
        )
        return service, artifacts

    def content(self):
        return ArtifactVersionContentRef(
            location='/output/analysis.json', checksum='sha256:' + 'a' * 64,
            mime_type='application/json', size_bytes=12,
        )

    def test_selected_result_creates_traceable_artifact_version(self):
        service, artifacts = self.service()
        artifact, version = service.materialize(
            project_id='project-1', run_id='run-1', attempt_id='attempt-1',
            output_name='analysis.json', ordinal=0, title='Analysis', type='analysis',
            content_ref=self.content(), input_refs=('asset-version-1',),
            prompt_version_ref='prompt-v1', model_ref='model-1', skill_version_ref='skill-v1',
        )
        self.assertEqual(artifact.version_ids, ('version-1',))
        self.assertEqual(version.lineage.task_id, 'task-1')
        self.assertEqual(version.lineage.run_id, 'run-1')
        self.assertEqual(version.lineage.attempt_id, 'attempt-1')
        self.assertEqual(version.lineage.input_refs, ('asset-version-1',))
        self.assertEqual(artifacts.calls[0]['version_metadata']['result']['task_id'], 'task-1')
        self.assertEqual(artifacts.calls[0]['title'], 'Analysis')

    def test_unselected_result_is_not_promoted(self):
        service, artifacts = self.service(selected=False)
        with self.assertRaises(ResultArtifactMaterializationError) as context:
            service.materialize(
                project_id='project-1', run_id='run-1', attempt_id='attempt-1',
                output_name='analysis.json', ordinal=0, title='Analysis', type='analysis',
                content_ref=self.content(),
            )
        self.assertEqual(context.exception.code, 'result_not_selected')
        self.assertEqual(artifacts.calls, [])

    def test_cross_run_result_is_rejected_before_write(self):
        service, artifacts = self.service()
        service._attempts = SimpleNamespace(get=lambda attempt_id: SimpleNamespace(run_id='other-run'))
        with self.assertRaises(ResultArtifactMaterializationError) as context:
            service.materialize(
                project_id='project-1', run_id='run-1', attempt_id='attempt-1',
                output_name='analysis.json', ordinal=0, title='Analysis', type='analysis',
                content_ref=self.content(),
            )
        self.assertEqual(context.exception.code, 'cross_project')
        self.assertEqual(artifacts.calls, [])

    def test_api_and_composition_register_explicit_route(self):
        api = (ROOT / 'workbench/api/result_artifact_materializations.py').read_text(encoding='utf-8')
        main = (ROOT / 'main.py').read_text(encoding='utf-8')
        self.assertIn("@router.post('/artifacts'", api)
        self.assertIn('create_result_artifact_materializations_router', main)


if __name__ == '__main__':
    unittest.main()

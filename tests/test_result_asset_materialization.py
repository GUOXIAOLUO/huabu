import unittest
from datetime import UTC, datetime
from types import SimpleNamespace

from workbench.application.result_asset_materialization import (
    ResultAssetMaterializationError,
    ResultAssetMaterializationService,
)
from workbench.domain.asset import AssetVersionContent
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ResultAssetMaterializationTests(unittest.TestCase):
    def test_api_contract_and_composition_register_explicit_route(self):
        api = (ROOT / "workbench/api/result_asset_materializations.py").read_text(encoding="utf-8")
        main = (ROOT / "main.py").read_text(encoding="utf-8")
        self.assertIn("/api/v1/execution-runs/{run_id}", api)
        self.assertIn("@router.post('/assets'", api)
        self.assertIn("create_result_asset_materializations_router", main)
        self.assertIn("create_result_asset_materializations_router(service_factory=result_asset_materialization_service)", main)

    def service(self, selected=True):
        class Assets:
            def __init__(self):
                self.created = []
                self.versions = []

            def create(self, asset, *, actor_id):
                self.created.append(asset)
                return asset

            def create_version(self, version, *, actor_id):
                self.versions.append(version)
                return version

            def create_with_version(self, asset, version, *, actor_id):
                self.created.append(asset)
                self.versions.append(version)
                return asset, version

            def get(self, asset_id, *, actor_id):
                asset = self.created[0]
                return asset.model_copy(update={"version_ids": (self.versions[0].id,)})

        assets = Assets()
        selections = SimpleNamespace(list_for_run=lambda run_id: [SimpleNamespace(
            attempt_id="attempt-1", output_name="poster.png", ordinal=0, selected=selected,
        )])
        runs = SimpleNamespace(get=lambda run_id: SimpleNamespace(project_id="project-1"))
        attempts = SimpleNamespace(get=lambda attempt_id: SimpleNamespace(run_id="run-1"))
        service = ResultAssetMaterializationService(
            assets, selections, runs, attempts, actor_id="owner",
            id_factory=iter(["asset-1", "version-1"]).__next__,
            clock=lambda: datetime(2026, 9, 14, tzinfo=UTC),
        )
        return service, assets

    def content(self):
        return AssetVersionContent(
            location="/output/poster.png", checksum="sha256:" + "a" * 64,
            mime_type="image/png", size_bytes=12,
        )

    def test_selected_result_becomes_asset_with_provenance_and_stable_ref(self):
        service, assets = self.service()
        asset, version = service.materialize(
            project_id="project-1", run_id="run-1", attempt_id="attempt-1",
            output_name="poster.png", ordinal=0, title="Poster", type="image",
            content=self.content(),
        )
        self.assertEqual(asset.source, "execution")
        self.assertEqual(asset.metadata["title"], "Poster")
        self.assertEqual(asset.version_ids, ("version-1",))
        self.assertEqual(version.asset_id, asset.id)
        self.assertEqual(version.provenance.source_ref, "run-1/attempt-1/poster.png#0")
        self.assertEqual(version.ref().model_dump(), {"asset_id": "asset-1", "version_id": "version-1"})
        self.assertEqual(len(assets.created), 1)
        self.assertEqual(len(assets.versions), 1)

    def test_unselected_result_is_not_saved(self):
        service, assets = self.service(selected=False)
        with self.assertRaises(ResultAssetMaterializationError) as context:
            service.materialize(
                project_id="project-1", run_id="run-1", attempt_id="attempt-1",
                output_name="poster.png", ordinal=0, title="Poster", type="image",
                content=self.content(),
            )
        self.assertEqual(context.exception.code, "result_not_selected")
        self.assertEqual(assets.created, [])

    def test_result_from_another_run_is_rejected_before_asset_write(self):
        service, assets = self.service()
        service._attempts = SimpleNamespace(get=lambda attempt_id: SimpleNamespace(run_id="other-run"))
        with self.assertRaises(ResultAssetMaterializationError) as context:
            service.materialize(
                project_id="project-1", run_id="run-1", attempt_id="attempt-1",
                output_name="poster.png", ordinal=0, title="Poster", type="image",
                content=self.content(),
            )
        self.assertEqual(context.exception.code, "cross_project")
        self.assertEqual(assets.created, [])


if __name__ == "__main__":
    unittest.main()

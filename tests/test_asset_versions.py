import tempfile
import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from workbench.api.assets import create_canonical_assets_router
from workbench.application.asset_service import AssetService
from workbench.application.asset_versions import (
    AssetVersionHistory,
    AssetVersionHistoryError,
)
from workbench.application.authorization import Action, AuthorizationError
from workbench.domain.asset import (
    Asset,
    AssetVersion,
    AssetVersionContent,
    AssetVersionProvenance,
)
from workbench.repositories.asset_repository import (
    AssetRepositoryNotFoundError,
    SqliteAssetRepository,
)


def make_asset(**overrides):
    payload = {"id": "asset-1", "project_id": "project-1", "source": "upload", "type": "image"}
    payload.update(overrides)
    return Asset(**payload)


def make_version(version_id, ordinal, *, asset_id="asset-1", **overrides):
    payload = {
        "id": version_id,
        "asset_id": asset_id,
        "ordinal": ordinal,
        "content": AssetVersionContent(
            location=overrides.pop("location", "https://cdn.example.com/hero.png"),
            checksum=overrides.pop("checksum", "sha256:" + "a" * 64),
            mime_type=overrides.pop("mime_type", "image/png"),
            size_bytes=overrides.pop("size_bytes", 2048),
        ),
        "provenance": AssetVersionProvenance(
            source=overrides.pop("source", "upload"),
            source_ref=overrides.pop("source_ref", "inbox/hero.png"),
            actor_id=overrides.pop("actor_id", "owner"),
        ),
        "created_at": overrides.pop("created_at", "2026-09-13T10:00:00+08:00"),
        "metadata": overrides.pop("metadata", {"note": version_id}),
    }
    payload.update(overrides)
    return AssetVersion(**payload)


class RecordingAuthorization:
    """Authorization double that records the project each read was scoped to."""

    def __init__(self, allowed=("project-1",)):
        self.allowed = set(allowed)
        self.calls = []

    def require(self, actor_id, action, project_id):
        self.calls.append((actor_id, action, project_id))
        if project_id not in self.allowed:
            raise AuthorizationError(f"actor {actor_id} may not read {project_id}")


class AssetVersionHistoryContractTests(unittest.TestCase):
    def test_history_orders_by_ordinal_and_names_the_end_as_current(self):
        # Ordering is *derived*, never trusted from the caller: a repository that
        # returns rows in any order still produces the one correct history.
        history = AssetVersionHistory(
            asset_id="asset-1",
            versions=(make_version("v2", 2), make_version("v1", 1), make_version("v3", 3)),
        )

        self.assertEqual([version.id for version in history.versions], ["v1", "v2", "v3"])
        self.assertEqual(history.current_version_id, "v3")
        self.assertEqual(history.current.id, "v3")
        self.assertEqual(len(history), 3)

    def test_empty_history_has_no_current_version(self):
        # An asset is created before anything is stored in it, so "no versions"
        # is a real state and must not be answered with a version.
        history = AssetVersionHistory(asset_id="asset-1")

        self.assertEqual(history.versions, ())
        self.assertIsNone(history.current)
        self.assertIsNone(history.current_version_id)
        self.assertEqual(len(history), 0)

    def test_history_looks_a_version_up_by_id(self):
        history = AssetVersionHistory(
            asset_id="asset-1", versions=(make_version("v1", 1), make_version("v2", 2))
        )

        self.assertEqual(history.version("v2").ordinal, 2)
        self.assertIsNone(history.version("v9"))
        self.assertIsNone(history.version(""))

    def test_history_rejects_a_version_that_belongs_to_another_asset(self):
        # One asset's history that contains another asset's version would make
        # the history a second owner of the other asset's content.
        with self.assertRaises(AssetVersionHistoryError) as caught:
            AssetVersionHistory(
                asset_id="asset-1", versions=(make_version("v1", 1, asset_id="asset-2"),)
            )
        self.assertIn("belongs to asset asset-2", str(caught.exception))

    def test_history_rejects_duplicate_and_gapped_ordinals(self):
        # `create_version` rejects any ordinal that is not `count + 1`, so a
        # stored sequence is gap-free from 1. Asserting it here is what makes the
        # sequence a testable claim instead of a comment about the repository.
        with self.assertRaises(AssetVersionHistoryError) as duplicate:
            AssetVersionHistory(
                asset_id="asset-1", versions=(make_version("v1", 1), make_version("v1b", 1))
            )
        self.assertIn("ordinals must be unique", str(duplicate.exception))

        with self.assertRaises(AssetVersionHistoryError) as gapped:
            AssetVersionHistory(
                asset_id="asset-1", versions=(make_version("v2", 2), make_version("v3", 3))
            )
        self.assertIn("gap-free sequence from 1", str(gapped.exception))

    def test_history_requires_an_asset_id_and_version_records(self):
        with self.assertRaises(AssetVersionHistoryError) as blank:
            AssetVersionHistory(asset_id="   ")
        self.assertIn("requires an asset id", str(blank.exception))

        with self.assertRaises(AssetVersionHistoryError) as wrong:
            AssetVersionHistory(asset_id="asset-1", versions=({"id": "v1"},))
        self.assertIn("takes AssetVersion records", str(wrong.exception))

    def test_history_records_are_frozen(self):
        # The transport reads the record more than once (the response body and
        # the current-version id); a record able to change between those reads
        # would describe two different histories.
        history = AssetVersionHistory(asset_id="asset-1", versions=(make_version("v1", 1),))
        with self.assertRaises(FrozenInstanceError):
            history.asset_id = "asset-2"
        with self.assertRaises(FrozenInstanceError):
            history.versions = ()


class AssetVersionRepositoryTests(unittest.TestCase):
    def seed(self, root):
        repository = SqliteAssetRepository(Path(root) / "workbench.sqlite3")
        repository.create_asset(make_asset())
        repository.create_version(make_version("v1", 1))
        repository.create_version(make_version(
            "v2", 2, location="https://cdn.example.com/hero-v2.mp4", mime_type="video/mp4",
            size_bytes=10485760, checksum="sha256:" + "b" * 64, source="import",
            source_ref=None, actor_id=None, created_at="2026-09-13T11:30:00+08:00",
            metadata={"note": "second"},
        ))
        repository.create_asset(make_asset(id="empty-1", type="document"))
        return repository

    def test_list_versions_returns_the_sequence_in_ordinal_order(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = self.seed(directory)

            versions = repository.list_versions("asset-1")

            self.assertEqual([version.id for version in versions], ["v1", "v2"])
            self.assertEqual([version.ordinal for version in versions], [1, 2])

    def test_list_versions_of_an_asset_without_versions_is_empty_not_an_error(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = self.seed(directory)

            self.assertEqual(repository.list_versions("empty-1"), [])

    def test_list_versions_of_a_missing_asset_is_not_found(self):
        # A typo must not look like an asset with no versions.
        with tempfile.TemporaryDirectory() as directory:
            repository = self.seed(directory)

            with self.assertRaises(AssetRepositoryNotFoundError):
                repository.list_versions("nope")

    def test_list_versions_round_trips_every_content_and_provenance_field(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = self.seed(directory)

            version = repository.list_versions("asset-1")[1]

            self.assertEqual(version.content.location, "https://cdn.example.com/hero-v2.mp4")
            self.assertEqual(version.content.mime_type, "video/mp4")
            self.assertEqual(version.content.size_bytes, 10485760)
            self.assertEqual(version.content.checksum, "sha256:" + "b" * 64)
            self.assertEqual(version.provenance.source, "import")
            self.assertIsNone(version.provenance.source_ref)
            self.assertIsNone(version.provenance.actor_id)
            self.assertEqual(version.created_at.isoformat(), "2026-09-13T11:30:00+08:00")
            self.assertEqual(version.metadata["note"], "second")

    def test_list_versions_agrees_with_the_assets_own_version_ids(self):
        # R9-02 asked R9-03 to keep `asset.version_ids == [v.id for v in
        # versions]`. The agreement is *structural* here: `load_asset` hydrates
        # `version_ids` from `asset_versions` in ordinal order and `list_versions`
        # reads the same rows in the same order, so the two cannot disagree —
        # which is a stronger statement than a runtime cross-check that could
        # never fire. This pins the agreement so a future change to either read
        # has to keep it.
        with tempfile.TemporaryDirectory() as directory:
            repository = self.seed(directory)

            asset = repository.load_asset("asset-1")
            versions = repository.list_versions("asset-1")

            self.assertEqual(
                tuple(asset.version_ids), tuple(version.id for version in versions)
            )


class AssetVersionServiceTests(unittest.TestCase):
    def test_service_authorizes_the_assets_own_project(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = SqliteAssetRepository(Path(directory) / "workbench.sqlite3")
            repository.create_asset(make_asset())
            repository.create_version(make_version("v1", 1))
            authorization = RecordingAuthorization(allowed=("project-1",))

            history = AssetService(repository, authorization).history("asset-1", actor_id="owner")

            self.assertEqual(history.asset_id, "asset-1")
            self.assertEqual(history.current_version_id, "v1")
            # The decision is the *asset's* project, taken from the asset and not
            # from the caller: the caller never names a project at all, so it
            # cannot widen a read to one it may not see.
            self.assertEqual(authorization.calls, [("owner", Action.PROJECT_READ, "project-1")])

    def test_service_denies_a_history_read_for_a_project_the_actor_may_not_read(self):
        # The denial has to be driven by the asset's project, which is why this
        # asset lives in a project the actor is not a member of. A double that
        # denied by actor instead would pass whether or not the service scoped
        # the check to the asset.
        with tempfile.TemporaryDirectory() as directory:
            repository = SqliteAssetRepository(Path(directory) / "workbench.sqlite3")
            repository.create_asset(make_asset(id="other-1", project_id="project-2"))
            repository.create_version(make_version("v1", 1, asset_id="other-1"))
            authorization = RecordingAuthorization(allowed=("project-1",))

            with self.assertRaises(AuthorizationError):
                AssetService(repository, authorization).history("other-1", actor_id="stranger")

            self.assertEqual(authorization.calls, [("stranger", Action.PROJECT_READ, "project-2")])

    def test_service_history_of_a_missing_asset_is_not_found(self):
        # An unknown id must be a failure, not an empty history: an empty history
        # reads as "this asset has no versions", which is a different fact.
        with tempfile.TemporaryDirectory() as directory:
            repository = SqliteAssetRepository(Path(directory) / "workbench.sqlite3")
            service = AssetService(repository, RecordingAuthorization())

            with self.assertRaises(AssetRepositoryNotFoundError):
                service.history("nope", actor_id="owner")


class AssetVersionApiTests(unittest.TestCase):
    def application(self, service_factory):
        application = FastAPI()
        application.include_router(create_canonical_assets_router(service_factory=service_factory))
        return application

    def test_canonical_version_history_api_projects_the_history_and_maps_auth(self):
        class Service:
            def __init__(self, actor_id):
                self.actor_id = actor_id

            def list(self, *, project_id, actor_id):
                raise AuthorizationError("denied")

            def get(self, asset_id, *, actor_id):
                raise AuthorizationError("denied")

            def get_version(self, asset_id, version_id, *, actor_id):
                raise AuthorizationError("denied")

            def query(self, query, *, actor_id):
                raise AuthorizationError("denied")

            def history(self, asset_id, *, actor_id):
                if actor_id != "owner":
                    raise AuthorizationError("denied")
                if asset_id == "missing":
                    raise AssetRepositoryNotFoundError(f"asset not found: {asset_id}")
                return AssetVersionHistory(
                    asset_id=asset_id,
                    versions=(make_version("v1", 1), make_version("v2", 2, mime_type="video/mp4")),
                )

        with TestClient(self.application(Service)) as client:
            self.assertEqual(
                client.get("/api/v1/assets/asset-1/versions").status_code, 401
            )
            self.assertEqual(
                client.get(
                    "/api/v1/assets/asset-1/versions", headers={"X-User-ID": "stranger"}
                ).status_code,
                403,
            )
            self.assertEqual(
                client.get(
                    "/api/v1/assets/missing/versions", headers={"X-User-ID": "owner"}
                ).status_code,
                404,
            )

            response = client.get(
                "/api/v1/assets/asset-1/versions", headers={"X-User-ID": "owner"}
            )
            self.assertEqual(response.status_code, 200)
            payload = response.json()
            # The shape is pinned, not just the status: a client reads
            # `current_version_id` rather than re-deriving "the highest ordinal",
            # so a reply that stopped naming it must fail here.
            self.assertEqual(set(payload), {"asset_id", "current_version_id", "versions"})
            self.assertEqual(payload["asset_id"], "asset-1")
            self.assertEqual(payload["current_version_id"], "v2")
            self.assertEqual([item["id"] for item in payload["versions"]], ["v1", "v2"])
            self.assertEqual(payload["versions"][0]["ordinal"], 1)
            self.assertEqual(payload["versions"][1]["content"]["mime_type"], "video/mp4")
            self.assertEqual(payload["versions"][0]["provenance"]["source"], "upload")

    def test_version_history_and_single_version_reads_are_distinct_routes(self):
        # `/versions` must be its own transport, not folded into the
        # `/{asset_id}/versions/{version_id}` read or the `/{asset_id}` read.
        class Service:
            def __init__(self, actor_id):
                self.actor_id = actor_id

            def history(self, asset_id, *, actor_id):
                return AssetVersionHistory(asset_id=asset_id)

            def get_version(self, asset_id, version_id, *, actor_id):
                return make_version(version_id, 1)

            def __getattr__(self, name):
                def denied(*args, **kwargs):
                    raise AuthorizationError("denied")
                return denied

        with TestClient(self.application(Service)) as client:
            history = client.get(
                "/api/v1/assets/asset-1/versions", headers={"X-User-ID": "owner"}
            )
            self.assertEqual(history.status_code, 200)
            self.assertEqual(set(history.json()), {"asset_id", "current_version_id", "versions"})

            single = client.get(
                "/api/v1/assets/asset-1/versions/v1", headers={"X-User-ID": "owner"}
            )
            self.assertEqual(single.status_code, 200)
            self.assertEqual(set(single.json()), {
                "id", "asset_id", "ordinal", "content", "provenance", "created_at", "metadata",
            })


class AssetVersionCompositionRootTests(unittest.TestCase):
    def test_composition_root_registers_the_version_history_route(self):
        # Every other test in this file builds its own app, so this is the only
        # place the real wiring is checked: deleting the `include_router` line
        # would otherwise leave the card's version-history transport unreachable
        # in the shipped app with the whole suite still green. The sibling guard
        # for `/query` was added by R9-05's review for exactly this reason.
        import main

        if not main.canonical_api_is_enabled_for_host(main.WORKBENCH_HOST):
            self.skipTest("the canonical product API is disabled for this host")
        paths = main.app.openapi()["paths"]
        self.assertIn("/api/v1/assets/{asset_id}/versions", paths)
        self.assertIn("get", paths["/api/v1/assets/{asset_id}/versions"])
        # ...and it stays a distinct path from the single-version read.
        self.assertIn("/api/v1/assets/{asset_id}/versions/{version_id}", paths)
        self.assertIn("get", paths["/api/v1/assets/{asset_id}/versions/{version_id}"])


if __name__ == "__main__":
    unittest.main()

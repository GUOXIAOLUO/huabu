import json
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from workbench.application.asset_migration import AssetLibraryMigrationService
from workbench.application.authorization import AuthorizationError
from workbench.api.assets import create_canonical_assets_router
from workbench.domain.asset import (
    Asset,
    AssetVersion,
    AssetVersionContent,
    AssetVersionProvenance,
)
from workbench.repositories.asset_repository import (
    AssetRepositoryConflictError,
    SqliteAssetRepository,
)


CHECKSUM = "sha256:ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
CREATED_AT = datetime(2026, 1, 1, tzinfo=UTC)


def make_asset(**overrides):
    payload = {
        "id": "asset-1",
        "project_id": "project-1",
        "source": "upload",
        "type": "image",
    }
    payload.update(overrides)
    return Asset(**payload)


def make_version(**overrides):
    payload = {
        "id": "version-1",
        "asset_id": "asset-1",
        "ordinal": 1,
        "content": AssetVersionContent(
            location="assets/library/board.png",
            checksum=CHECKSUM,
            mime_type="image/png",
            size_bytes=3,
        ),
        "provenance": AssetVersionProvenance(source="upload"),
        "created_at": CREATED_AT,
    }
    payload.update(overrides)
    return AssetVersion(**payload)


class AssetRepositoryMigrationTests(unittest.TestCase):
    def test_canonical_api_projects_asset_and_version_ref_without_file_bytes(self):
        application = FastAPI()

        class Service:
            def __init__(self, actor_id):
                self.actor_id = actor_id

            def list(self, *, project_id, actor_id):
                if actor_id != "owner":
                    raise AuthorizationError("denied")
                return [make_asset(version_ids=("version-1",))]

            def get(self, asset_id, *, actor_id):
                if actor_id != "owner":
                    raise AuthorizationError("denied")
                return make_asset(version_ids=("version-1",))

            def get_version(self, asset_id, version_id, *, actor_id):
                if actor_id != "owner":
                    raise AuthorizationError("denied")
                return make_version()

        application.include_router(create_canonical_assets_router(service_factory=Service))

        with TestClient(application) as client:
            self.assertEqual(client.get("/api/v1/assets?project_id=project-1").status_code, 401)
            self.assertEqual(
                client.get("/api/v1/assets?project_id=project-1", headers={"X-User-ID": "stranger"}).status_code,
                403,
            )
            response = client.get("/api/v1/assets?project_id=project-1", headers={"X-User-ID": "owner"})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()[0]["version_ids"], ["version-1"])
            version_response = client.get(
                "/api/v1/assets/asset-1/versions/version-1", headers={"X-User-ID": "owner"}
            )
            self.assertEqual(version_response.status_code, 200)
            self.assertNotIn("bytes", version_response.json()["content"])
            self.assertEqual(
                client.get("/api/v1/assets/asset-1", headers={"X-User-ID": "stranger"}).status_code,
                403,
            )
            self.assertEqual(
                client.get(
                    "/api/v1/assets/asset-1/versions/version-1",
                    headers={"X-User-ID": "stranger"},
                ).status_code,
                403,
            )

    def test_repository_enforces_version_sequence_and_ref_lookup(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = SqliteAssetRepository(Path(directory) / "workbench.sqlite3")
            repository.create_asset(make_asset())
            repository.create_version(make_version())

            self.assertEqual(repository.load_version("asset-1", "version-1").ref().model_dump(), {
                "asset_id": "asset-1",
                "version_id": "version-1",
            })
            self.assertEqual(repository.load_asset("asset-1").version_ids, ("version-1",))

            with self.assertRaises(AssetRepositoryConflictError):
                repository.create_version(make_version(id="version-2", ordinal=3))
            with self.assertRaises(AssetRepositoryConflictError):
                repository.create_version(make_version(id="version-1", ordinal=2))

    def test_migration_preserves_legacy_bytes_and_records_checksum(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            library_root = root / "library"
            library_root.mkdir()
            source = library_root / "board.png"
            source.write_bytes(b"abc")
            legacy_path = root / "asset_library.json"
            legacy_path.write_text(json.dumps({
                "libraries": [{
                    "id": "default",
                    "name": "默认资产库",
                    "categories": [{
                        "id": "characters",
                        "name": "角色",
                        "type": "image",
                        "items": [{
                            "id": "legacy-item-1",
                            "name": "board",
                            "url": "/assets/library/board.png",
                            "kind": "image",
                        }],
                    }],
                }],
            }), encoding="utf-8")
            repository = SqliteAssetRepository(root / "workbench.sqlite3")

            report = AssetLibraryMigrationService(repository, library_root=library_root).migrate(
                legacy_path, project_id="project-1"
            )

            self.assertEqual(report.imported_items, ("legacy-item-1",))
            version = repository.load_version("legacy-item-1", "legacy-item-1-v1")
            self.assertEqual(version.content.location, "board.png")
            self.assertEqual(version.content.checksum, CHECKSUM)
            self.assertEqual(version.content.size_bytes, 3)
            self.assertEqual(source.read_bytes(), b"abc")

    def test_migration_skips_paths_outside_library_root(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            library_root = root / "library"
            library_root.mkdir()
            outside = root / "outside.png"
            outside.write_bytes(b"secret")
            legacy_path = root / "asset_library.json"
            legacy_path.write_text(json.dumps({
                "libraries": [{"categories": [{"items": [{
                    "id": "unsafe", "url": "/assets/library/../outside.png", "kind": "image"
                }]}]}]
            }), encoding="utf-8")
            repository = SqliteAssetRepository(root / "workbench.sqlite3")

            report = AssetLibraryMigrationService(repository, library_root=library_root).migrate(
                legacy_path, project_id="project-1"
            )

            self.assertEqual(report.imported_items, ())
            self.assertEqual(report.skipped_items, ("unsafe",))
            self.assertEqual(outside.read_bytes(), b"secret")

    def test_migration_rejects_existing_identity_or_version_conflicts(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            library_root = root / "library"
            library_root.mkdir()
            source = library_root / "board.png"
            source.write_bytes(b"abc")
            legacy_path = root / "asset_library.json"
            legacy_path.write_text(json.dumps({
                "libraries": [{"categories": [{"items": [{
                    "id": "legacy-item-1",
                    "url": "/assets/library/board.png",
                    "kind": "image",
                }]}]}]
            }), encoding="utf-8")
            repository = SqliteAssetRepository(root / "workbench.sqlite3")
            repository.create_asset(make_asset(id="legacy-item-1", project_id="other-project"))

            with self.assertRaises(AssetRepositoryConflictError):
                AssetLibraryMigrationService(repository, library_root=library_root).migrate(
                    legacy_path, project_id="project-1"
                )

            repository = SqliteAssetRepository(root / "version-conflict.sqlite3")
            repository.create_asset(make_asset(id="legacy-item-1", project_id="project-1"))
            repository.create_version(make_version(
                id="legacy-item-1-v1",
                asset_id="legacy-item-1",
                content=AssetVersionContent(
                    location="board.png",
                    checksum="sha256:" + "c" * 64,
                    mime_type="image/png",
                    size_bytes=3,
                ),
            ))

            with self.assertRaises(AssetRepositoryConflictError):
                AssetLibraryMigrationService(repository, library_root=library_root).migrate(
                    legacy_path, project_id="project-1"
                )


if __name__ == "__main__":
    unittest.main()

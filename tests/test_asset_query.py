import asyncio
import json
import tempfile
import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient

from workbench.api.assets import create_canonical_assets_router
from workbench.application.asset_query import AssetQuery, AssetQueryError, AssetQueryPage
from workbench.application.asset_service import AssetService
from workbench.application.authorization import Action, AuthorizationError
from workbench.domain.asset import Asset
from workbench.repositories.asset_repository import SqliteAssetRepository


def make_asset(**overrides):
    payload = {"id": "asset-1", "project_id": "project-1", "source": "upload", "type": "image"}
    payload.update(overrides)
    return Asset(**payload)


class RecordingAuthorization:
    """Authorization double that records the project each query was scoped to."""

    def __init__(self, allowed=("project-1",)):
        self.allowed = set(allowed)
        self.calls = []

    def require(self, actor_id, action, project_id):
        self.calls.append((actor_id, action, project_id))
        if project_id not in self.allowed:
            raise AuthorizationError(f"actor {actor_id} may not read {project_id}")


class AssetQueryRepositoryTests(unittest.TestCase):
    def seed(self, root):
        repository = SqliteAssetRepository(Path(root) / "workbench.sqlite3")
        repository.create_asset(make_asset(
            id="hero-board", project_id="project-1", source="upload", type="image",
            status="ready", metadata={"name": "Hero board", "tags": ["Hero", "board"]},
        ))
        repository.create_asset(make_asset(
            id="clip-01", project_id="project-1", source="import", type="video",
            metadata={"tags": ["board"]},
        ))
        repository.create_asset(make_asset(
            id="doc-01", project_id="project-1", source="url", type="document",
            status="archived", metadata={"tags": ["spec"]},
        ))
        repository.create_asset(make_asset(
            id="other-project", project_id="project-2", source="upload", type="image",
            metadata={"tags": ["hero"]},
        ))
        return repository

    def test_query_scopes_to_one_project_and_filters_the_domain_columns(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = self.seed(directory)

            page, total = repository.query_assets(AssetQuery(project_id="project-1"))
            self.assertEqual([asset.id for asset in page], ["clip-01", "doc-01", "hero-board"])
            self.assertEqual(total, 3)

            page, total = repository.query_assets(AssetQuery(project_id="project-1", types=("image",)))
            self.assertEqual([asset.id for asset in page], ["hero-board"])
            self.assertEqual(total, 1)

            page, total = repository.query_assets(AssetQuery(project_id="project-1", sources=("import", "url")))
            self.assertEqual([asset.id for asset in page], ["clip-01", "doc-01"])

            page, total = repository.query_assets(AssetQuery(project_id="project-1", statuses=("archived",)))
            self.assertEqual([asset.id for asset in page], ["doc-01"])

            page, total = repository.query_assets(AssetQuery(
                project_id="project-1", types=("image",), sources=("upload",), statuses=("ready",)
            ))
            self.assertEqual([asset.id for asset in page], ["hero-board"])
            self.assertEqual(total, 1)

    def test_query_never_returns_another_projects_assets(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = self.seed(directory)

            for query in (
                AssetQuery(project_id="project-2"),
                AssetQuery(project_id="project-2", tags=("hero",)),
                AssetQuery(project_id="project-2", text="hero"),
            ):
                page, total = repository.query_assets(query)
                self.assertEqual([asset.id for asset in page], ["other-project"])
                self.assertEqual(total, 1)

    def test_tag_filter_intersects_and_is_answered_by_the_tag_index(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = self.seed(directory)

            page, total = repository.query_assets(AssetQuery(project_id="project-1", tags=("BOARD",)))
            self.assertEqual([asset.id for asset in page], ["clip-01", "hero-board"])
            self.assertEqual(total, 2)

            # Two tags mean "carries both", not "carries either": adding a
            # filter must narrow a result set, never widen it.
            page, total = repository.query_assets(AssetQuery(project_id="project-1", tags=("board", "hero")))
            self.assertEqual([asset.id for asset in page], ["hero-board"])
            self.assertEqual(total, 1)

            # The metadata declaration is the source of truth; the index is the
            # projection that makes the filter a seek instead of a JSON scan.
            import sqlite3

            connection = sqlite3.connect(Path(directory) / "workbench.sqlite3")
            tags = connection.execute(
                "SELECT asset_id, tag FROM asset_tags ORDER BY asset_id, tag"
            ).fetchall()
            self.assertEqual(tags, [
                ("clip-01", "board"), ("doc-01", "spec"), ("hero-board", "board"),
                ("hero-board", "hero"), ("other-project", "hero"),
            ])
            indexes = {row[0] for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='index'"
            ).fetchall()}
            self.assertLessEqual(
                {"idx_assets_project_type", "idx_assets_project_source",
                 "idx_assets_project_status", "idx_asset_tags_tag"},
                indexes,
            )
            plan = " ".join(
                str(row) for row in connection.execute(
                    "EXPLAIN QUERY PLAN SELECT assets.* FROM assets WHERE assets.project_id = ?"
                    " AND EXISTS (SELECT 1 FROM asset_tags WHERE asset_tags.asset_id = assets.id"
                    " AND asset_tags.tag = ?) ORDER BY assets.id LIMIT ? OFFSET ?",
                    ("project-1", "hero", 24, 0),
                ).fetchall()
            )
            self.assertIn("asset_tags", plan)
            self.assertIn("INDEX", plan.upper())

    def test_query_text_matches_the_id_and_the_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = self.seed(directory)

            page, _ = repository.query_assets(AssetQuery(project_id="project-1", text="CLIP"))
            self.assertEqual([asset.id for asset in page], ["clip-01"])

            page, _ = repository.query_assets(AssetQuery(project_id="project-1", text="hero board"))
            self.assertEqual([asset.id for asset in page], ["hero-board"])

            page, total = repository.query_assets(AssetQuery(project_id="project-1", text="nothing-here"))
            self.assertEqual(page, [])
            self.assertEqual(total, 0)

    def test_query_paginates_and_reports_the_unpaged_total(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = self.seed(directory)

            first, total = repository.query_assets(AssetQuery(project_id="project-1", limit=2, offset=0))
            second, same_total = repository.query_assets(AssetQuery(project_id="project-1", limit=2, offset=2))
            beyond, _ = repository.query_assets(AssetQuery(project_id="project-1", limit=2, offset=4))

            self.assertEqual([asset.id for asset in first], ["clip-01", "doc-01"])
            self.assertEqual([asset.id for asset in second], ["hero-board"])
            self.assertEqual(beyond, [])
            self.assertEqual((total, same_total), (3, 3))

    def test_query_rejects_vocabulary_outside_the_domain_closed_sets(self):
        for payload, expected in (
            ({"project_id": ""}, "requires a project id"),
            ({"project_id": "project-1", "types": ("nope",)}, "unknown asset type: nope"),
            ({"project_id": "project-1", "sources": ("nope",)}, "unknown asset source: nope"),
            ({"project_id": "project-1", "statuses": ("nope",)}, "unknown asset status: nope"),
            ({"project_id": "project-1", "limit": 0}, "limit must be between 1 and 200"),
            ({"project_id": "project-1", "limit": 201}, "limit must be between 1 and 200"),
            ({"project_id": "project-1", "offset": -1}, "offset must not be negative"),
            ({"project_id": "project-1", "tags": ("  ",)}, "tag cannot be empty"),
        ):
            with self.subTest(payload=payload):
                with self.assertRaises(AssetQueryError) as caught:
                    AssetQuery(**payload)
                self.assertIn(expected, str(caught.exception))

    def test_query_normalizes_duplicates_and_reports_whether_it_is_filtered(self):
        query = AssetQuery(
            project_id="  project-1  ", text="  board  ", types=("image", "image"),
            tags=("Hero", "hero"), limit=48, offset=96,
        )

        self.assertEqual(query.project_id, "project-1")
        self.assertEqual(query.text, "board")
        self.assertEqual(query.types, ("image",))
        self.assertEqual(query.tags, ("hero",))
        self.assertEqual(query.limit, 48)
        self.assertEqual(query.offset, 96)
        self.assertTrue(query.is_filtered())
        self.assertFalse(AssetQuery(project_id="project-1").is_filtered())

    def test_page_reports_more_only_while_rows_remain(self):
        asset = make_asset()
        self.assertTrue(AssetQueryPage(items=(asset,), total=3, limit=1, offset=0).has_more)
        self.assertFalse(AssetQueryPage(items=(asset,), total=3, limit=1, offset=2).has_more)
        self.assertFalse(AssetQueryPage(items=(), total=0, limit=24, offset=0).has_more)

    def test_query_and_page_records_are_frozen(self):
        # `AssetService.query` reads `query.limit` / `query.offset` *after* the
        # repository call to build the page, so a repository able to mutate the
        # query it was handed could return a window that does not describe what
        # was actually queried. Frozenness is that invariant, not decoration.
        query = AssetQuery(project_id="project-1", limit=48, offset=96)
        with self.assertRaises(FrozenInstanceError):
            query.limit = 24
        with self.assertRaises(FrozenInstanceError):
            query.project_id = "project-2"

        page = AssetQueryPage(items=(), total=3, limit=24, offset=0)
        with self.assertRaises(FrozenInstanceError):
            page.total = 0
        with self.assertRaises(FrozenInstanceError):
            page.offset = 24


class AssetQueryServiceTests(unittest.TestCase):
    def test_service_authorizes_the_querys_own_project(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = SqliteAssetRepository(Path(directory) / "workbench.sqlite3")
            repository.create_asset(make_asset(id="hero-board", metadata={"tags": ["hero"]}))
            authorization = RecordingAuthorization(allowed=("project-1",))

            page = AssetService(repository, authorization).query(
                AssetQuery(project_id="project-1", tags=("hero",)), actor_id="owner"
            )

            self.assertIsInstance(page, AssetQueryPage)
            self.assertEqual([asset.id for asset in page.items], ["hero-board"])
            self.assertEqual(page.total, 1)
            self.assertEqual(authorization.calls, [("owner", Action.PROJECT_READ, "project-1")])

            with self.assertRaises(AuthorizationError):
                AssetService(repository, authorization).query(
                    AssetQuery(project_id="project-2"), actor_id="stranger"
                )

    def test_service_rejects_a_query_that_is_not_the_query_contract(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = SqliteAssetRepository(Path(directory) / "workbench.sqlite3")
            service = AssetService(repository, RecordingAuthorization())

            with self.assertRaises(TypeError):
                service.query({"project_id": "project-1"}, actor_id="owner")


class AssetQueryApiTests(unittest.TestCase):
    def application(self, service_factory):
        application = FastAPI()
        application.include_router(create_canonical_assets_router(service_factory=service_factory))
        return application

    def test_canonical_query_api_projects_a_page_and_maps_auth_and_validation(self):
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
                if actor_id != "owner":
                    raise AuthorizationError("denied")
                if query.types and query.types != ("image",):
                    raise AssetQueryError("unknown asset type")
                asset = make_asset(project_id=query.project_id, version_ids=("version-1",))
                return AssetQueryPage(
                    items=(asset,), total=3, limit=query.limit, offset=query.offset
                )

        with TestClient(self.application(Service)) as client:
            self.assertEqual(client.get("/api/v1/assets/query?project_id=project-1").status_code, 401)
            self.assertEqual(
                client.get(
                    "/api/v1/assets/query?project_id=project-1", headers={"X-User-ID": "stranger"}
                ).status_code,
                403,
            )
            # `/query` must be routed as its own transport, not swallowed by the
            # `/{asset_id}` read (which this service answers with 403).
            response = client.get(
                "/api/v1/assets/query?project_id=project-1&type=image&tag=hero&limit=1&offset=0",
                headers={"X-User-ID": "owner"},
            )
            self.assertEqual(response.status_code, 200)
            payload = response.json()
            self.assertEqual(payload["total"], 3)
            self.assertEqual(payload["limit"], 1)
            self.assertEqual(payload["offset"], 0)
            self.assertTrue(payload["has_more"])
            self.assertEqual(payload["items"][0]["id"], "asset-1")
            self.assertEqual(payload["items"][0]["version_ids"], ["version-1"])

            # A 422 this seam raises and a 422 the framework raises are different
            # failures, so pin the shape that tells them apart: the seam answers
            # with its own coded string, the framework's own validation answers
            # with the pydantic detail list. Pinning the status alone would let
            # one silently become the other.
            refused = client.get(
                "/api/v1/assets/query?project_id=project-1&type=nope",
                headers={"X-User-ID": "owner"},
            )
            self.assertEqual(refused.status_code, 422)
            self.assertIsInstance(refused.json()["detail"], str)
            self.assertIn("unknown asset type", refused.json()["detail"])

            invalid = client.get(
                "/api/v1/assets/query?limit=1", headers={"X-User-ID": "owner"}
            )
            self.assertEqual(invalid.status_code, 422)
            self.assertIsInstance(invalid.json()["detail"], list)

    def test_shipped_app_marks_framework_validation_errors_so_the_two_422_sources_stay_apart(self):
        # The shipped application rewrites `RequestValidationError` into
        # `{"detail": <localized string>, "errors": [...]}` (main.py), so in the
        # real app the discriminator is the presence of `errors`, not the type of
        # `detail` — which is a string on both sides there. Pin the handler's
        # contract directly rather than driving `main.app` through its lifespan:
        # the startup hook runs real asset-library migrations against real data.
        import main

        handler = main.app.exception_handlers.get(RequestValidationError)
        self.assertIsNotNone(handler, "the application must keep a validation handler")
        response = asyncio.run(handler(None, RequestValidationError([
            {"type": "missing", "loc": ["query", "project_id"], "msg": "Field required", "input": None},
        ])))
        self.assertEqual(response.status_code, 422)
        payload = json.loads(response.body)
        self.assertIsInstance(payload["detail"], str)
        self.assertIsInstance(payload["errors"], list)
        self.assertTrue(payload["errors"], "the framework error list must survive the rewrite")


class AssetQueryCompositionRootTests(unittest.TestCase):
    def test_composition_root_registers_the_canonical_query_route(self):
        # Every other test in this file builds its own app, so this is the only
        # place the real wiring is checked: deleting the `include_router` line
        # would otherwise leave the card's canonical transport unreachable in
        # the shipped app, with the whole suite still green.
        import main

        if not main.canonical_api_is_enabled_for_host(main.WORKBENCH_HOST):
            self.skipTest("the canonical product API is disabled for this host")
        paths = main.app.openapi()["paths"]
        self.assertIn("/api/v1/assets/query", paths)
        self.assertIn("get", paths["/api/v1/assets/query"])
        # `/query` is its own path: it must not be folded into, or shadowed by,
        # the `/{asset_id}` read declared after it.
        self.assertIn("/api/v1/assets/{asset_id}", paths)
        self.assertIn("get", paths["/api/v1/assets/{asset_id}"])


if __name__ == "__main__":
    unittest.main()

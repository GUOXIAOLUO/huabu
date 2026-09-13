"""AssetVersion: immutable content records and the rules that address them.

The card's DoD is that version refs are stable and immutable. "Stable" is proven
against the thing most likely to move — the content — and "immutable" is proven
against the record and everything nested in it. Persistence is R9-03's, so the
record is proven here through itself and through a JSON round-trip only.
"""

import json
import unittest
from datetime import datetime, timezone
from typing import get_args

from pydantic import ValidationError

from workbench.domain.asset import (
    Asset,
    AssetSource,
    AssetVersion,
    AssetVersionContent,
    AssetVersionProvenance,
    AssetVersionRef,
)

CREATED_AT = datetime(2026, 9, 13, 8, 0, tzinfo=timezone.utc)
CHECKSUM = "sha256:" + "a" * 64


def make_content(**overrides):
    payload = {
        "location": "/assets/library/lib_board.png",
        "checksum": CHECKSUM,
        "mime_type": "image/png",
        "size_bytes": 4096,
    }
    payload.update(overrides)
    return AssetVersionContent(**payload)


def make_version(**overrides):
    payload = {
        "id": "version-1",
        "asset_id": "asset-1",
        "ordinal": 1,
        "content": make_content(),
        "provenance": AssetVersionProvenance(source="upload"),
        "created_at": CREATED_AT,
    }
    payload.update(overrides)
    return AssetVersion(**payload)


class AssetVersionTests(unittest.TestCase):
    # ---------------------------------------------------------------- DoD
    def test_version_ref_is_stable_when_the_content_changes(self):
        version = make_version()

        moved = make_version(
            content=make_content(
                location="/assets/library/moved.png",
                checksum="sha256:" + "b" * 64,
                mime_type="image/webp",
                size_bytes=8192,
            )
        )

        self.assertEqual(moved.ref(), version.ref())
        self.assertEqual(version.ref(), AssetVersionRef(asset_id="asset-1", version_id="version-1"))

    def test_version_ref_survives_a_json_round_trip(self):
        version = make_version()

        restored = AssetVersion.model_validate(version.model_dump(mode="json"))

        self.assertEqual(restored.ref(), version.ref())
        self.assertEqual(restored.content.checksum, version.content.checksum)

    def test_ref_carries_identity_only(self):
        # Stability by construction: a ref that named content, size or time
        # would move whenever any of those did.
        self.assertEqual(set(AssetVersionRef.model_fields), {"asset_id", "version_id"})

    def test_two_versions_of_one_asset_have_different_refs(self):
        first = make_version(id="version-1")
        second = make_version(id="version-2")

        self.assertNotEqual(first.ref(), second.ref())
        self.assertEqual(first.ref().asset_id, second.ref().asset_id)

    def test_ref_addresses_one_of_the_versions_the_asset_names(self):
        asset = Asset(id="asset-1", project_id="project-1", source="upload", type="image")
        asset = asset.with_version("version-1").with_version("version-2")

        version = make_version(id="version-2", ordinal=2)

        self.assertIn(version.ref().version_id, asset.version_ids)

    # ---------------------------------------------------------- immutability
    def test_version_is_frozen_inside_and_out(self):
        version = make_version()

        with self.assertRaises(ValidationError):
            version.ordinal = 2
        with self.assertRaises(ValidationError):
            version.content.checksum = "sha256:" + "c" * 64
        with self.assertRaises(ValidationError):
            version.provenance.source = "url"

        self.assertEqual(version.ordinal, 1)

    def test_metadata_cannot_be_changed_in_place(self):
        version = make_version(metadata={"name": "board"})

        with self.assertRaises(TypeError):
            version.metadata["name"] = "other"

    def test_nested_metadata_is_frozen_too(self):
        # Freezing only the top level would leave a mutable dict one step down —
        # the same hole the record claims to close.
        version = make_version(metadata={"origin": {"library": "default"}})

        with self.assertRaises(TypeError):
            version.metadata["origin"]["library"] = "other"

        self.assertEqual(version.metadata["origin"]["library"], "default")

    def test_version_shape_is_pinned(self):
        # The DoD is about what a version *is*; a record that silently gains a
        # field changes that without any test noticing.
        self.assertEqual(
            set(AssetVersion.model_fields),
            {
                "schema_version",
                "id",
                "asset_id",
                "ordinal",
                "content",
                "provenance",
                "created_at",
                "metadata",
            },
        )
        self.assertEqual(set(AssetVersionProvenance.model_fields), {"source", "source_ref", "actor_id"})

    # ------------------------------------------------------------ content contract
    def test_content_shape_is_pinned(self):
        self.assertEqual(
            set(AssetVersionContent.model_fields),
            {"location", "checksum", "mime_type", "size_bytes"},
        )

    def test_content_fields_are_required(self):
        payload = {
            "location": "/assets/library/lib_board.png",
            "checksum": CHECKSUM,
            "mime_type": "image/png",
            "size_bytes": 4096,
        }
        for field in sorted(payload):
            with self.subTest(field=field):
                partial = dict(payload)
                partial.pop(field)
                with self.assertRaises(ValidationError):
                    AssetVersionContent(**partial)

    def test_checksum_is_algorithm_and_hex_digest(self):
        self.assertEqual(make_content(checksum="md5:" + "0" * 32).checksum, "md5:" + "0" * 32)

        for bad in ("deadbeef", "sha256:", "sha256:" + "A" * 64, "sha256:abc", "sha256" + "a" * 64):
            with self.subTest(checksum=bad):
                with self.assertRaises(ValidationError):
                    make_content(checksum=bad)

    def test_size_location_and_mime_bounds(self):
        with self.assertRaises(ValidationError):
            make_content(size_bytes=-1)
        with self.assertRaises(ValidationError):
            make_content(location="")
        with self.assertRaises(ValidationError):
            make_content(mime_type="")

        self.assertEqual(make_content(size_bytes=0).size_bytes, 0)

    def test_a_version_never_carries_file_bytes(self):
        # The out-of-scope clause is "do not duplicate file bytes": everything a
        # version carries has to survive JSON, so bytes have nowhere to hide.
        dumped = make_version().model_dump(mode="json")

        self.assertEqual(json.loads(json.dumps(dumped))["content"]["size_bytes"], 4096)

    # --------------------------------------------------------- provenance contract
    def test_provenance_speaks_the_asset_source_vocabulary(self):
        self.assertIs(AssetVersionProvenance.model_fields["source"].annotation, AssetSource)

        for source in get_args(AssetSource):
            with self.subTest(source=source):
                self.assertEqual(AssetVersionProvenance(source=source).source, source)

        with self.assertRaises(ValidationError):
            AssetVersionProvenance(source="wholehouse")

    def test_provenance_optional_fields_default_to_none(self):
        provenance = AssetVersionProvenance(source="url")

        self.assertIsNone(provenance.source_ref)
        self.assertIsNone(provenance.actor_id)

    def test_provenance_optional_field_bounds(self):
        # Optional is not "anything goes": an empty actor id is no actor, and an
        # unbounded source reference is a field with no stated limit.
        with self.assertRaises(ValidationError):
            AssetVersionProvenance(source="url", actor_id="")
        with self.assertRaises(ValidationError):
            AssetVersionProvenance(source="url", source_ref="u" * 2049)

        self.assertEqual(AssetVersionProvenance(source="url", source_ref="u" * 2048).source_ref, "u" * 2048)

    # -------------------------------------------------------------- record contract
    def test_schema_version_is_the_stored_literal(self):
        self.assertEqual(make_version().schema_version, "workbench.asset-version/1")

        with self.assertRaises(ValidationError):
            make_version(schema_version="workbench.asset-version/2")

    def test_ordinal_starts_at_one(self):
        with self.assertRaises(ValidationError):
            make_version(ordinal=0)

        self.assertEqual(make_version(ordinal=1).ordinal, 1)

    def test_identity_fields_are_required(self):
        for field in ("id", "asset_id", "ordinal", "content", "provenance", "created_at"):
            with self.subTest(field=field):
                payload = {
                    "id": "version-1",
                    "asset_id": "asset-1",
                    "ordinal": 1,
                    "content": make_content(),
                    "provenance": AssetVersionProvenance(source="upload"),
                    "created_at": CREATED_AT,
                }
                payload.pop(field)
                with self.assertRaises(ValidationError):
                    AssetVersion(**payload)

    def test_unknown_fields_are_rejected_everywhere(self):
        with self.assertRaises(ValidationError):
            make_version(name="board")
        with self.assertRaises(ValidationError):
            make_content(bytes=b"raw")
        with self.assertRaises(ValidationError):
            AssetVersionProvenance(source="upload", wholehouse_kind="floorplan")
        with self.assertRaises(ValidationError):
            AssetVersionRef(asset_id="asset-1", version_id="version-1", ordinal=1)

    def test_identity_bounds_are_enforced(self):
        with self.assertRaises(ValidationError):
            make_version(id="")
        with self.assertRaises(ValidationError):
            make_version(asset_id="")
        with self.assertRaises(ValidationError):
            make_version(id="v" * 256)

    def test_created_at_is_kept_through_a_round_trip(self):
        version = make_version()

        restored = AssetVersion.model_validate(version.model_dump(mode="json"))

        self.assertEqual(restored.created_at, CREATED_AT)

    def test_metadata_rejects_credentials(self):
        with self.assertRaises(ValidationError):
            make_version(metadata={"api_key": "secret"})

        self.assertEqual(make_version(metadata={"name": "board"}).metadata["name"], "board")


if __name__ == "__main__":
    unittest.main()

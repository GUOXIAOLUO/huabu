"""Asset domain: one stable identity that references immutable versions.

These tests are the card's DoD and its contract pins. They deliberately do not
touch storage: R9-03 owns the repository, the service and the migration, so the
record is proven here only through the record itself and through a JSON
round-trip.
"""

import unittest
from typing import get_args

from pydantic import ValidationError

from workbench.domain.asset import Asset, AssetSource, AssetStatus, AssetType


def make_asset(**overrides):
    payload = {
        "id": "asset-1",
        "project_id": "project-1",
        "source": "upload",
        "type": "image",
    }
    payload.update(overrides)
    return Asset(**payload)


class AssetDomainTests(unittest.TestCase):
    # ---------------------------------------------------------------- DoD
    def test_asset_can_reference_multiple_versions(self):
        asset = make_asset()

        first = asset.with_version("version-1")
        second = first.with_version("version-2")

        self.assertEqual(second.version_ids, ("version-1", "version-2"))

    def test_referencing_versions_never_changes_identity(self):
        asset = make_asset()

        grown = asset.with_version("version-1").with_version("version-2")

        self.assertEqual(grown.id, asset.id)
        self.assertEqual(grown.project_id, asset.project_id)
        self.assertEqual(grown.source, asset.source)
        self.assertEqual(grown.type, asset.type)
        self.assertEqual(grown.status, asset.status)
        self.assertEqual(grown.metadata, asset.metadata)

    def test_versions_are_append_only(self):
        asset = make_asset().with_version("version-1")

        with self.assertRaises(TypeError):
            asset.version_ids[0] = "version-other"

        self.assertEqual(asset.version_ids, ("version-1",))

    def test_referencing_the_same_version_twice_is_refused(self):
        asset = make_asset().with_version("version-1")

        # The refusal has to come from the domain seam itself and say so. A
        # pydantic ValidationError is also a ValueError, so asserting only the
        # base class would let a record-level uniqueness check stand in for this
        # guard and hide it.
        with self.assertRaises(ValueError) as caught:
            asset.with_version("version-1")

        self.assertNotIsInstance(caught.exception, ValidationError)
        self.assertIn("already references version", str(caught.exception))
        self.assertEqual(asset.version_ids, ("version-1",))

    def test_asset_carries_no_version_content(self):
        # Separation of identity from versions is a shape claim: the identity
        # record names versions but holds nothing a version owns.
        self.assertEqual(
            set(Asset.model_fields),
            {"schema_version", "id", "project_id", "source", "type", "status", "version_ids", "metadata"},
        )

    def test_asset_without_versions_is_still_an_asset(self):
        asset = make_asset()

        self.assertEqual(asset.version_ids, ())
        self.assertEqual(asset.status, "draft")

    def test_version_reference_bounds_are_enforced(self):
        with self.assertRaises(ValidationError):
            make_asset(version_ids=("version-1", ""))

        with self.assertRaises(ValidationError):
            make_asset().with_version("")

    def test_duplicate_version_ids_are_rejected(self):
        with self.assertRaises(ValidationError):
            make_asset(version_ids=("version-1", "version-1"))

    # ------------------------------------------------------- closed sets
    def test_closed_sets_are_pinned(self):
        self.assertEqual(get_args(AssetSource), ("upload", "url", "local_path", "provider", "import"))
        self.assertEqual(get_args(AssetType), ("image", "video", "audio", "document", "model", "workflow", "other"))
        self.assertEqual(get_args(AssetStatus), ("draft", "ready", "archived"))

    def test_unknown_source_type_and_status_are_rejected(self):
        with self.assertRaises(ValidationError):
            make_asset(source="wholehouse")
        with self.assertRaises(ValidationError):
            make_asset(type="floorplan")
        with self.assertRaises(ValidationError):
            make_asset(status="converted")

    # ------------------------------------------------------ record contract
    def test_schema_version_is_the_stored_literal(self):
        self.assertEqual(make_asset().schema_version, "workbench.asset/1")

        with self.assertRaises(ValidationError):
            make_asset(schema_version="workbench.asset/2")

    def test_asset_is_frozen(self):
        asset = make_asset()

        with self.assertRaises(ValidationError):
            asset.id = "asset-2"

        self.assertIsNot(asset.with_version("version-1"), asset)

    def test_unknown_fields_are_rejected(self):
        with self.assertRaises(ValidationError):
            make_asset(name="board.png")

    def test_identity_bounds_are_enforced(self):
        with self.assertRaises(ValidationError):
            make_asset(id="")
        with self.assertRaises(ValidationError):
            make_asset(project_id="")

        self.assertEqual(make_asset(id="a" * 255).id, "a" * 255)
        with self.assertRaises(ValidationError):
            make_asset(id="a" * 256)

    def test_metadata_defaults_to_an_independent_empty_mapping(self):
        first = make_asset()
        second = make_asset()

        self.assertEqual(first.metadata, {})
        self.assertIsNot(first.metadata, second.metadata)

        # Metadata is `dict[str, Any]`: it has to carry nested JSON shapes, not
        # just flat strings, or callers will smuggle structure into string keys.
        carrying = make_asset(metadata={"name": "board", "tags": ["mood"], "origin": {"library": "default"}})
        self.assertEqual(carrying.metadata["name"], "board")
        self.assertEqual(list(carrying.metadata["tags"]), ["mood"])
        self.assertEqual(carrying.metadata["origin"]["library"], "default")

    def test_metadata_is_immutable_and_rejects_credentials(self):
        # A frozen record with a mutable interior is not frozen, and metadata is
        # persisted and logged, so it must not be able to carry a credential.
        asset = make_asset(metadata={"name": "board"})

        with self.assertRaises(TypeError):
            asset.metadata["name"] = "other"

        self.assertEqual(asset.metadata["name"], "board")

        with self.assertRaises(ValidationError):
            make_asset(metadata={"api_key": "secret"})

    def test_every_identity_field_is_required(self):
        # An Asset without one of these is not an identity. Defaults here would
        # let a record exist while silently answering "which asset is this?"
        # with a placeholder.
        payload = {"id": "asset-1", "project_id": "project-1", "source": "upload", "type": "image"}

        for field in sorted(payload):
            with self.subTest(field=field):
                partial = dict(payload)
                partial.pop(field)
                with self.assertRaises(ValidationError):
                    Asset(**partial)

    def test_a_grown_asset_carries_its_own_metadata(self):
        asset = make_asset(metadata={"name": "board"})

        grown = asset.with_version("version-1")

        self.assertIsNot(grown.metadata, asset.metadata)
        self.assertEqual(grown.metadata, asset.metadata)

    def test_project_ownership_is_part_of_the_record(self):
        self.assertNotEqual(make_asset(project_id="project-1"), make_asset(project_id="project-2"))

    # ------------------------------------------------------------ persisted shape
    def test_json_round_trip_preserves_identity_and_version_order(self):
        asset = make_asset(version_ids=("version-2", "version-1"))

        dumped = asset.model_dump(mode="json")
        restored = Asset.model_validate(dumped)

        self.assertEqual(restored, asset)
        self.assertEqual(dumped["version_ids"], ["version-2", "version-1"])
        self.assertEqual(dumped["schema_version"], "workbench.asset/1")


if __name__ == "__main__":
    unittest.main()

"""Artifact domain: one identity for a produced output, independent of Canvas.

These tests are the card's DoD and its contract pins. They deliberately do not
touch storage or the Canvas: the version record and its repository belong to
R9-09, and the Artifact is proven here through the record itself, a JSON
round-trip, and the absence of any Canvas dependency in the module that defines
it.
"""

import ast
import json
import tempfile
import unittest
from pathlib import Path
from typing import get_args

from pydantic import ValidationError

from workbench.domain.artifact import Artifact, ArtifactState, ArtifactType

ROOT = Path(__file__).resolve().parents[1]


def make_artifact(**overrides):
    payload = {
        "id": "artifact-1",
        "project_id": "project-1",
        "type": "analysis",
        "title": "Floor plan analysis",
    }
    payload.update(overrides)
    return Artifact(**payload)


class ArtifactDomainTests(unittest.TestCase):
    # ---------------------------------------------------------------- DoD
    def test_artifact_is_defined_without_any_canvas(self):
        # The DoD: an Artifact exists independently from a Canvas node. It is a
        # shape claim first — nothing in the identity names a canvas, a node, a
        # position or a renderer, so no Canvas has to exist for it to validate.
        artifact = make_artifact()

        self.assertEqual(artifact.id, "artifact-1")
        self.assertEqual(set(Artifact.model_fields) & {"canvas_id", "canvas", "node_id", "node", "position", "renderer"}, set())

        dumped = artifact.model_dump(mode="json")
        self.assertEqual([key for key in dumped if "canvas" in key or "node" in key], [])

    def test_the_artifact_module_imports_nothing_from_the_canvas_domain(self):
        # The stronger half of the DoD: independence is not only the absence of
        # a field, it is the absence of a dependency. A Canvas import would let
        # node concerns reach into the identity even with no canvas field.
        violations = []
        for path in sorted((ROOT / "workbench" / "domain" / "artifact").glob("*.py")):
            for module in _imported_modules(path):
                if module == "workbench.domain.canvas" or module.startswith("workbench.domain.canvas."):
                    violations.append(f"{path.relative_to(ROOT)} -> {module}")
        self.assertEqual(violations, [])

    def test_an_artifact_survives_a_round_trip_through_stored_bytes(self):
        artifact = make_artifact(version_ids=("version-2", "version-1"), metadata={"summary": "3 rooms"})

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "artifact.json"
            path.write_text(artifact.model_dump_json(), encoding="utf-8")
            restored = Artifact.model_validate(json.loads(path.read_text(encoding="utf-8")))

        self.assertEqual(restored, artifact)
        self.assertEqual(restored.schema_version, "workbench.artifact/1")
        self.assertEqual(restored.version_ids, ("version-2", "version-1"))

    # ------------------------------------------------- versions are separate
    def test_artifact_can_reference_multiple_versions(self):
        artifact = make_artifact()

        first = artifact.with_version("version-1")
        second = first.with_version("version-2")

        self.assertEqual(second.version_ids, ("version-1", "version-2"))

    def test_append_order_is_the_append_order_not_the_lexicographic_one(self):
        # Version ids are opaque — the existing materialization service mints
        # them with `uuid4().hex` — so append order and lexicographic order
        # disagree in ordinary use. The order has to be the order they were
        # appended in: a version history that gets sorted on the way in is a
        # different history, and nothing in the record says a later version came
        # first. The ids below sort the other way round on purpose.
        artifact = make_artifact()

        grown = artifact.with_version("version-2").with_version("version-1")

        self.assertEqual(grown.version_ids, ("version-2", "version-1"))

    def test_referencing_versions_never_changes_identity(self):
        artifact = make_artifact()

        grown = artifact.with_version("version-1").with_version("version-2")

        self.assertEqual(grown.id, artifact.id)
        self.assertEqual(grown.project_id, artifact.project_id)
        self.assertEqual(grown.type, artifact.type)
        self.assertEqual(grown.title, artifact.title)
        self.assertEqual(grown.state, artifact.state)
        self.assertEqual(grown.metadata, artifact.metadata)

    def test_versions_are_append_only(self):
        artifact = make_artifact().with_version("version-1")

        with self.assertRaises(TypeError):
            artifact.version_ids[0] = "version-other"

        self.assertEqual(artifact.version_ids, ("version-1",))

    def test_referencing_the_same_version_twice_is_refused(self):
        artifact = make_artifact().with_version("version-1")

        # The refusal has to come from the domain seam itself and say so. A
        # pydantic ValidationError is also a ValueError, so asserting only the
        # base class would let a record-level uniqueness check stand in for this
        # guard and hide it.
        with self.assertRaises(ValueError) as caught:
            artifact.with_version("version-1")

        self.assertNotIsInstance(caught.exception, ValidationError)
        self.assertIn("already references version", str(caught.exception))
        self.assertEqual(artifact.version_ids, ("version-1",))

    def test_artifact_carries_no_version_content(self):
        # Separation of identity from versions is a shape claim: the identity
        # record names versions but holds nothing a version owns.
        self.assertEqual(
            set(Artifact.model_fields),
            {"schema_version", "id", "project_id", "type", "title", "state", "version_ids", "metadata"},
        )

    def test_artifact_without_versions_is_still_an_artifact(self):
        artifact = make_artifact()

        self.assertEqual(artifact.version_ids, ())
        self.assertEqual(artifact.state, "draft")

    def test_version_reference_bounds_are_enforced(self):
        with self.assertRaises(ValidationError):
            make_artifact(version_ids=("version-1", ""))

        with self.assertRaises(ValidationError):
            make_artifact().with_version("")

    def test_duplicate_version_ids_are_rejected(self):
        with self.assertRaises(ValidationError):
            make_artifact(version_ids=("version-1", "version-1"))

    # ------------------------------------------------------- closed sets
    def test_closed_sets_are_pinned(self):
        self.assertEqual(
            get_args(ArtifactType),
            ("text", "analysis", "image", "video", "table", "comparison", "review", "handoff", "other"),
        )
        self.assertEqual(get_args(ArtifactState), ("draft", "ready", "archived"))

    def test_unknown_type_and_state_are_rejected(self):
        with self.assertRaises(ValidationError):
            make_artifact(type="floorplan")
        with self.assertRaises(ValidationError):
            make_artifact(state="approved")

    def test_no_approval_or_frozen_state_is_modelled(self):
        # Out of scope on this card: `state` is a placeholder, so the vocabulary
        # has no approved/frozen member and the record exposes no lifecycle
        # member that could grow into one silently.
        self.assertEqual(set(get_args(ArtifactState)) & {"approved", "frozen", "rejected"}, set())
        # `freeze_metadata` is excluded by name: it freezes the metadata mapping,
        # it is not a state the Artifact can be moved into.
        lifecycle_members = [
            name
            for name in dir(Artifact)
            if not name.startswith("_")
            and name != "freeze_metadata"
            and any(marker in name for marker in ("approve", "freeze", "reject", "transition", "submit"))
        ]
        self.assertEqual(lifecycle_members, [])

    # ------------------------------------------------------ record contract
    def test_schema_version_is_the_stored_literal(self):
        self.assertEqual(make_artifact().schema_version, "workbench.artifact/1")

        with self.assertRaises(ValidationError):
            make_artifact(schema_version="workbench.artifact/2")

    def test_the_artifact_marker_is_not_the_asset_marker(self):
        # A produced output and an imported resource are different records; a
        # shared marker would make one replaceable by the other on reload.
        self.assertEqual(make_artifact().schema_version, "workbench.artifact/1")
        self.assertNotEqual(make_artifact().schema_version, "workbench.asset/1")

    def test_artifact_is_frozen(self):
        artifact = make_artifact()

        with self.assertRaises(ValidationError):
            artifact.title = "other"

        self.assertIsNot(artifact.with_version("version-1"), artifact)

    def test_unknown_fields_are_rejected(self):
        with self.assertRaises(ValidationError):
            make_artifact(canvas_id="canvas-1")

    def test_identity_bounds_are_enforced(self):
        # Every opaque id the record carries gets the same 255/256 pin, not just
        # `id`. Only `id` was pinned at first, and widening `project_id` or the
        # version-id element to 5000 characters left the whole suite green: the
        # record was still correct, but the identity contract it claims had no
        # guard, so a future edit could widen one field silently.
        with self.assertRaises(ValidationError):
            make_artifact(id="")
        with self.assertRaises(ValidationError):
            make_artifact(project_id="")

        for field in ("id", "project_id"):
            with self.subTest(field=field):
                self.assertEqual(getattr(make_artifact(**{field: "a" * 255}), field), "a" * 255)
                with self.assertRaises(ValidationError):
                    make_artifact(**{field: "a" * 256})

        self.assertEqual(make_artifact(version_ids=("v" * 255,)).version_ids, ("v" * 255,))
        with self.assertRaises(ValidationError):
            make_artifact(version_ids=("v" * 256,))

    def test_a_version_reference_is_bounded_through_the_append_seam(self):
        # `with_version` re-validates the whole record, so the bound has to hold
        # there too — a widened bound that only the constructor rejected would
        # still let an unbounded id in through the append seam.
        artifact = make_artifact()

        self.assertEqual(artifact.with_version("v" * 255).version_ids, ("v" * 255,))
        with self.assertRaises(ValidationError):
            artifact.with_version("v" * 256)

    def test_title_is_required_and_bounded(self):
        # An unnamed output cannot be listed, compared or reviewed, so the title
        # is part of the identity rather than display metadata.
        with self.assertRaises(ValidationError):
            make_artifact(title="")

        self.assertEqual(make_artifact(title="a" * 500).title, "a" * 500)
        with self.assertRaises(ValidationError):
            make_artifact(title="a" * 501)

    def test_metadata_defaults_to_an_independent_empty_mapping(self):
        first = make_artifact()
        second = make_artifact()

        self.assertEqual(first.metadata, {})
        self.assertIsNot(first.metadata, second.metadata)

        # Metadata is `dict[str, Any]`: it has to carry nested JSON shapes, not
        # just flat strings, or callers will smuggle structure into string keys.
        carrying = make_artifact(metadata={"prompt": "summarize", "tags": ["final"], "origin": {"run": "run-1"}})
        self.assertEqual(carrying.metadata["prompt"], "summarize")
        self.assertEqual(list(carrying.metadata["tags"]), ["final"])
        self.assertEqual(carrying.metadata["origin"]["run"], "run-1")

    def test_metadata_is_immutable_and_rejects_credentials(self):
        # A frozen record with a mutable interior is not frozen, and metadata is
        # persisted and logged, so it must not be able to carry a credential.
        artifact = make_artifact(metadata={"prompt": "summarize"})

        with self.assertRaises(TypeError):
            artifact.metadata["prompt"] = "other"

        self.assertEqual(artifact.metadata["prompt"], "summarize")

        with self.assertRaises(ValidationError):
            make_artifact(metadata={"api_key": "secret"})

    def test_every_identity_field_is_required(self):
        # An Artifact without one of these is not an identity. Defaults here
        # would let a record exist while silently answering "which output is
        # this?" with a placeholder.
        payload = {"id": "artifact-1", "project_id": "project-1", "type": "analysis", "title": "Analysis"}

        for field in sorted(payload):
            with self.subTest(field=field):
                partial = dict(payload)
                partial.pop(field)
                with self.assertRaises(ValidationError):
                    Artifact(**partial)

    def test_a_grown_artifact_carries_its_own_metadata(self):
        artifact = make_artifact(metadata={"prompt": "summarize"})

        grown = artifact.with_version("version-1")

        self.assertIsNot(grown.metadata, artifact.metadata)
        self.assertEqual(grown.metadata, artifact.metadata)

    def test_project_ownership_is_part_of_the_record(self):
        self.assertNotEqual(
            make_artifact(project_id="project-1"),
            make_artifact(project_id="project-2"),
        )

    # ------------------------------------------------------------ persisted shape
    def test_json_round_trip_preserves_identity_and_version_order(self):
        artifact = make_artifact(version_ids=("version-2", "version-1"))

        dumped = artifact.model_dump(mode="json")
        restored = Artifact.model_validate(dumped)

        self.assertEqual(restored, artifact)
        self.assertEqual(dumped["version_ids"], ["version-2", "version-1"])
        self.assertEqual(dumped["schema_version"], "workbench.artifact/1")


def _imported_modules(path: Path) -> set:
    """Absolute dotted module names referenced by imports in one file."""
    modules = set()
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


if __name__ == "__main__":
    unittest.main()

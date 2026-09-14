import unittest
from datetime import UTC, datetime

from pydantic import ValidationError

from workbench.domain.knowledge import KnowledgeSource, KnowledgeSourceProvenance


class KnowledgeSourceDomainTests(unittest.TestCase):
    def provenance(self):
        return KnowledgeSourceProvenance(
            origin="user", actor_id="user-1", captured_at=datetime.now(UTC)
        )

    def test_source_types_refs_scopes_and_provenance_are_explicit(self):
        asset = KnowledgeSource(
            id="source-1", source_type="asset", source_ref="asset-v1",
            scope="project", project_id="project-1", provenance=self.provenance(),
        )
        manual = KnowledgeSource(
            id="source-2", source_type="manual", scope="workspace",
            workspace_id="workspace-1", provenance=self.provenance(),
        )
        self.assertEqual(asset.model_dump(mode="json")["source_type"], "asset")
        self.assertEqual(asset.model_dump(mode="json")["provenance"]["origin"], "user")
        self.assertIsNone(manual.source_ref)
        self.assertEqual(manual.scope, "workspace")
        self.assertNotIn("vector", asset.model_dump(mode="json"))

    def test_scope_and_reference_rules_reject_ambiguous_sources(self):
        with self.assertRaises(ValidationError):
            KnowledgeSource(id="s", source_type="document", scope="project", provenance=self.provenance())
        with self.assertRaises(ValidationError):
            KnowledgeSource(id="s", source_type="manual", scope="workspace", provenance=self.provenance())
        with self.assertRaises(ValidationError):
            KnowledgeSource(id="s", source_type="manual", scope="industry", project_id="p", provenance=self.provenance())

    def test_lifecycle_is_explicit_and_records_are_immutable(self):
        source = KnowledgeSource(
            id="source-1", source_type="manual", project_id="project-1",
            provenance=self.provenance(), metadata={"nested": {"ok": True}},
        )
        self.assertEqual(source.status, "draft")
        self.assertEqual(source.activate().status, "active")
        archived = source.activate().archive()
        self.assertEqual(archived.status, "archived")
        with self.assertRaises(ValueError): archived.activate()
        with self.assertRaises(TypeError): source.metadata["nested"]["ok"] = False
        with self.assertRaises(ValueError):
            KnowledgeSource(
                id="s", source_type="manual", project_id="p",
                provenance=self.provenance(), metadata={"api_key": "secret"},
            )


if __name__ == "__main__":
    unittest.main()

import unittest
from datetime import UTC, datetime

from pydantic import ValidationError

from workbench.domain.catalog import Catalog, CatalogAttributeDefinition, CatalogItem, CatalogItemVersion, CatalogMediaRef, CatalogSchema, validate_item_attributes
from workbench.domain.collection import CollectionItem, CollectionReferenceCell


class CatalogDomainTests(unittest.TestCase):
    def schema(self):
        return CatalogSchema(id="schema-1", name="Generic", attributes=[
            CatalogAttributeDefinition(key="sku", label="SKU", value_type="text", required=True),
            CatalogAttributeDefinition(key="weight", label="Weight", value_type="number"),
        ])

    def test_catalog_supports_project_and_workspace_scopes_without_industry_fields(self):
        project = Catalog(id="catalog-1", workspace_id="workspace-1", project_id="project-1", scope="project", name="Project catalog", schema=self.schema())
        workspace = Catalog(id="catalog-2", workspace_id="workspace-1", scope="workspace", name="Shared catalog", schema=self.schema())
        self.assertEqual(project.model_dump(mode="json")["schema"]["id"], "schema-1")
        self.assertIsNone(workspace.project_id)
        self.assertNotIn("board", project.model_dump(mode="json"))

    def test_item_version_validates_attributes_and_media_refs(self):
        validate_item_attributes(self.schema(), {"sku": "A-1", "weight": 2})
        with self.assertRaises(ValueError): validate_item_attributes(self.schema(), {})
        version = CatalogItemVersion(id="version-1", catalog_id="catalog-1", item_id="item-1", ordinal=1, attributes={"sku": "A-1"}, media_refs=(CatalogMediaRef(kind="asset_version", ref_id="asset-v1", role="thumbnail"),), created_at=datetime.now(UTC))
        self.assertEqual(version.media_refs[0].kind, "asset_version")
        item = CatalogItem(id="item-1", catalog_id="catalog-1", title="Chair", version_ids=("version-1",), current_version_id="version-1")
        self.assertEqual(item.with_version("version-2").current_version_id, "version-2")
        self.assertEqual(CatalogItem(id="legacy", catalog_id="catalog-1", title="Legacy", version_ids=("version-1",)).current_version_id, "version-1")
        with self.assertRaises(ValidationError): CatalogItem(id="bad", catalog_id="catalog-1", title="Bad", version_ids=("version-1",), current_version_id="version-2")
        with self.assertRaises(ValidationError): Catalog(id="bad", workspace_id="w", project_id="p", scope="workspace", name="Bad", schema=self.schema())

    def test_collection_can_pin_a_specific_catalog_item_version(self):
        row = CollectionItem(id="row-1", order=0, values={"item": CollectionReferenceCell(reference_type="catalog_item_version", reference_id="version-1")})
        self.assertEqual(row.values["item"].reference_id, "version-1")


if __name__ == "__main__": unittest.main()

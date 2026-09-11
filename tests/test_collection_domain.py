import unittest

from pydantic import ValidationError

from workbench.domain.collection import (
    Collection,
    CollectionItem,
    CollectionLiteralCell,
    CollectionReferenceCell,
    CollectionSchema,
    CollectionColumn,
)


class CollectionDomainTests(unittest.TestCase):
    def make_collection(self):
        schema = CollectionSchema(
            id="schema-1",
            name="Reference board",
            columns=[
                CollectionColumn(id="image", key="image", label="Image", value_type="asset_version"),
                CollectionColumn(id="note", key="note", label="Note", value_type="literal"),
            ],
            metadata={"owner": "project"},
        )
        return Collection(
            id="collection-1",
            project_id="project-1",
            name="Moodboard",
            schema=schema,
            items=[
                CollectionItem(
                    id="item-2",
                    order=2,
                    values={
                        "image": CollectionReferenceCell(reference_type="asset_version", reference_id="asset-2"),
                        "note": CollectionLiteralCell(value="second"),
                    },
                ),
                CollectionItem(
                    id="item-1",
                    order=1,
                    values={
                        "image": CollectionReferenceCell(reference_type="asset_version", reference_id="asset-1"),
                        "note": CollectionLiteralCell(value="first"),
                    },
                ),
            ],
            default_view={"mode": "grid", "sort": "order"},
            metadata={"source": "test"},
        )

    def test_collection_round_trips_without_canvas_group_shape(self):
        collection = self.make_collection()
        restored = Collection.model_validate(collection.model_dump(mode="json"))

        self.assertEqual(restored, collection)
        self.assertEqual([item.id for item in restored.items], ["item-2", "item-1"])
        self.assertNotIn("node_ids", restored.model_dump(mode="json"))

    def test_collection_rejects_group_membership_fields(self):
        with self.assertRaises(ValidationError):
            CollectionItem.model_validate({"id": "item-1", "order": 1, "node_ids": ["node-1"]})

    def test_collection_rejects_unknown_or_mismatched_cells(self):
        collection = self.make_collection().model_dump(mode="json")
        collection["items"][0]["values"]["unknown"] = {"type": "literal", "value": "x"}
        with self.assertRaises(ValidationError):
            Collection.model_validate(collection)

        collection = self.make_collection().model_dump(mode="json")
        collection["items"][0]["values"]["image"] = {"type": "literal", "value": "not-an-asset"}
        with self.assertRaises(ValidationError):
            Collection.model_validate(collection)

    def test_collection_requires_unique_item_order_and_column_keys(self):
        collection = self.make_collection().model_dump(mode="json")
        collection["items"][1]["order"] = collection["items"][0]["order"]
        with self.assertRaises(ValidationError):
            Collection.model_validate(collection)

        with self.assertRaises(ValidationError):
            CollectionSchema(
                id="schema-1",
                name="Invalid",
                columns=[
                    {"id": "a", "key": "same", "label": "A", "value_type": "literal"},
                    {"id": "b", "key": "same", "label": "B", "value_type": "literal"},
                ],
            )


if __name__ == "__main__":
    unittest.main()

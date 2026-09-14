import unittest

from pydantic import ValidationError

from workbench.domain.entity import (
    EntityDefinition,
    EntityPropertyDefinition,
    EntityRecord,
    EntitySchema,
    validate_entity_properties,
)


class EntityDomainTests(unittest.TestCase):
    def schema(self):
        return EntitySchema(
            id="schema-1",
            name="Generic entity",
            properties=(
                EntityPropertyDefinition(key="name", label="Name", value_type="text", required=True),
                EntityPropertyDefinition(key="priority", label="Priority", value_type="number"),
            ),
        )

    def test_definition_is_generic_and_schema_driven(self):
        definition = EntityDefinition(id="definition-1", entity_type="project_fact", schema=self.schema())
        record = EntityRecord(
            id="entity-1",
            entity_type=definition.entity_type,
            definition_id=definition.id,
            project_id="project-1",
            properties={"name": "A fact", "priority": 1},
            state="active",
        )
        validate_entity_properties(definition.schema, record.properties)
        self.assertEqual(definition.model_dump(mode="json")["schema"]["id"], "schema-1")
        self.assertEqual(record.model_dump(mode="json")["project_id"], "project-1")
        self.assertNotIn("customer", definition.model_dump(mode="json"))
        self.assertNotIn("room", definition.model_dump(mode="json"))

    def test_schema_rejects_duplicate_properties_and_invalid_property_sets(self):
        with self.assertRaises(ValueError):
            EntitySchema(
                id="schema-1",
                name="Bad",
                properties=(
                    EntityPropertyDefinition(key="same", label="One", value_type="text"),
                    EntityPropertyDefinition(key="same", label="Two", value_type="text"),
                ),
            )
        schema = self.schema()
        with self.assertRaises(ValueError): validate_entity_properties(schema, {})
        with self.assertRaises(ValueError): validate_entity_properties(schema, {"name": "ok", "unknown": True})
        validate_entity_properties(schema, {"name": "ok"})

    def test_records_are_frozen_and_metadata_cannot_carry_credentials(self):
        record = EntityRecord(id="e", entity_type="fact", definition_id="d", project_id="p", properties={"nested": {"ok": True}})
        with self.assertRaises(TypeError): record.properties["nested"]["ok"] = False
        with self.assertRaises(ValueError): EntityRecord(id="e", entity_type="fact", definition_id="d", project_id="p", metadata={"api_key": "secret"})
        with self.assertRaises(ValidationError): EntityRecord(id="e", entity_type="fact", definition_id="d", project_id="p", state="unknown")


if __name__ == "__main__": unittest.main()

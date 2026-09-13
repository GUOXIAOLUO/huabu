import unittest

from workbench.application.execution_input_projection import ExecutionInputProjectionService
from workbench.domain.canvas import InputBinding
from workbench.domain.canvas.models import DefinitionRef
from workbench.domain.collection import Collection, CollectionItem, CollectionLiteralCell, CollectionSchema
from workbench.domain.prompt import PromptRef


def binding(binding_id, *, source_type="literal", source_ref='"hello"', order=0):
    return InputBinding(
        id=binding_id,
        target="task.input",
        source_type=source_type,
        source_ref=source_ref,
        order=order,
    )


def collection():
    return Collection(
        id="shots",
        project_id="project",
        name="Shots",
        schema=CollectionSchema(
            id="shot-schema",
            name="Shot schema",
            columns=[{"id": "prompt", "key": "prompt", "label": "Prompt", "value_type": "literal"}],
        ),
        items=[
            CollectionItem(id="row-b", order=2, values={"prompt": CollectionLiteralCell(value="B")}),
            CollectionItem(id="row-a", order=1, values={"prompt": CollectionLiteralCell(value="A")}),
        ],
        revision=7,
    )


class ExecutionInputProjectionTests(unittest.TestCase):
    def test_freezes_bindings_collection_rows_and_run_context(self):
        service = ExecutionInputProjectionService({"collection": lambda ref: collection()})
        projection = service.project(
            [binding("literal", order=0), binding("shots", source_type="collection", source_ref="shots", order=1)],
            parameters={"quality": "high"},
            skill_ref=DefinitionRef(type="skill", id="skill", version="1"),
            prompt_ref=PromptRef(prompt_id="prompt", version=3),
            model_availability_ref="model-route-v2",
            execution_profile_ref="profile@2",
        )

        self.assertTrue(projection.valid)
        self.assertEqual([item.input_id for item in projection.inputs], ["literal", "shots:row-a", "shots:row-b"])
        self.assertEqual([item.value["row_id"] for item in projection.inputs[1:]], ["row-a", "row-b"])
        self.assertEqual(projection.inputs[1].value["collection_revision"], 7)
        self.assertEqual((projection.prompt_ref.version, projection.model_availability_ref, projection.execution_profile_ref), (3, "model-route-v2", "profile@2"))

    def test_projection_is_independent_after_source_mutation(self):
        source = {"id": "asset-v1", "version": 1, "content": {"text": "before"}}
        projection = ExecutionInputProjectionService({"asset_version": lambda ref: source}).project([binding("asset", source_type="asset_version", source_ref="asset-v1")])
        source["content"]["text"] = "after"

        self.assertEqual(projection.inputs[0].value["content"]["text"], "before")
        self.assertEqual(projection.inputs[0].source_ref, "asset-v1")

    def test_unresolved_or_disabled_input_returns_errors_before_execution(self):
        projection = ExecutionInputProjectionService().project([
            binding("missing", source_type="asset_version", source_ref="asset-v1"),
            InputBinding(id="disabled", target="task.input", source_type="literal", source_ref='"x"', enabled=False),
        ])

        self.assertFalse(projection.valid)
        self.assertEqual({error.code for error in projection.errors}, {"resolver_unavailable", "binding_disabled"})
        self.assertEqual(projection.inputs, ())

    def test_invalid_collection_and_literal_are_reported(self):
        invalid_collection = ExecutionInputProjectionService({"collection": lambda ref: {"id": ref}}).project([binding("collection", source_type="collection", source_ref="shots")])
        invalid_literal = ExecutionInputProjectionService().project([binding("bad", source_ref="not-json")])

        self.assertEqual(invalid_collection.errors[0].code, "collection_invalid")
        self.assertEqual(invalid_literal.errors[0].code, "invalid_literal")


if __name__ == "__main__":
    unittest.main()

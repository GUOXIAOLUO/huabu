import unittest

from workbench.application.binding_resolver import BindingResolutionError, BindingResolver
from workbench.domain.canvas import InputBinding


def binding(binding_id, *, source_type="asset_version", source_ref="asset-1", order=0, enabled=True):
    return InputBinding(
        id=binding_id,
        target="prompt.image",
        source_type=source_type,
        source_ref=source_ref,
        order=order,
        enabled=enabled,
    )


class BindingResolverTests(unittest.TestCase):
    def test_resolves_deterministically_by_order_then_id_without_canvas_edges(self):
        resolver = BindingResolver({"asset_version": lambda ref: {"id": ref}})
        results = resolver.resolve([
            binding("b", order=1, source_ref="asset-b"),
            binding("a", order=1, source_ref="asset-a"),
            binding("c", order=0, source_ref="asset-c"),
        ])
        self.assertEqual([item.binding_id for item in results], ["c", "a", "b"])
        self.assertEqual([item.value for item in results], [{"id": "asset-c"}, {"id": "asset-a"}, {"id": "asset-b"}])

    def test_unresolved_reference_and_future_type_remain_explicit(self):
        results = BindingResolver({"asset_version": lambda ref: None}).resolve([
            binding("missing"),
            binding("future", source_type="collection", source_ref="collection-1"),
        ])
        by_id = {item.binding_id: item for item in results}
        self.assertEqual((by_id["missing"].status, by_id["missing"].reason), ("unresolved", "source_not_found"))
        self.assertEqual((by_id["future"].status, by_id["future"].reason), ("unresolved", "resolver_unavailable"))

    def test_literal_is_normalized_without_invoking_a_resource_resolver(self):
        calls = []
        result = BindingResolver({"literal": lambda ref: calls.append(ref)}).resolve([
            binding("literal", source_type="literal", source_ref='{"quality": 2}'),
            binding("disabled", source_type="literal", source_ref="not-json", enabled=False),
        ])
        by_id = {item.binding_id: item for item in result}
        self.assertEqual(by_id["literal"].value, {"quality": 2})
        self.assertEqual(by_id["literal"].status, "resolved")
        self.assertEqual(by_id["disabled"].status, "disabled")
        self.assertEqual(calls, [])

    def test_invalid_literal_and_duplicate_id_are_typed_errors(self):
        with self.assertRaisesRegex(BindingResolutionError, "literal") as invalid:
            BindingResolver().resolve([binding("bad", source_type="literal", source_ref="not-json")])
        self.assertEqual(invalid.exception.code, "invalid_literal")

        with self.assertRaisesRegex(BindingResolutionError, "duplicate") as duplicate:
            BindingResolver().resolve([binding("same"), binding("same")])
        self.assertEqual(duplicate.exception.code, "duplicate_binding_id")

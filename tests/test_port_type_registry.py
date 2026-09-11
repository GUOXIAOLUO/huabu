import unittest

from workbench.domain.canvas.port_type_registry import (
    PortTypeDefinition,
    PortTypeRegistry,
    create_core_port_type_registry,
)
from workbench.domain.canvas.ports import InputPort, OutputPort, PortSet


class PortTypeRegistryTests(unittest.TestCase):
    def test_core_types_resolve_and_port_sets_use_one_registry(self):
        registry = create_core_port_type_registry()
        resolved = registry.resolve_port_set(PortSet(
            inputs=[InputPort(id="in", accepts=["asset.file"])],
            outputs=[OutputPort(id="out", produces=["asset.cad"])],
        ))
        self.assertEqual([item.id for item in resolved["inputs"]], ["asset.file"])
        self.assertEqual([item.id for item in resolved["outputs"]], ["asset.cad"])
        self.assertTrue(registry.accepts("asset.cad", "asset.file"))
        self.assertTrue(registry.accepts("asset.image", "legacy.any"))
        self.assertFalse(registry.accepts("asset.image", "asset.video"))

    def test_package_extension_registers_through_registry_without_new_node_kind(self):
        registry = create_core_port_type_registry()
        extension = registry.register(PortTypeDefinition("package.cad.surface", "CAD surface", ("asset.cad",)))
        self.assertIs(registry.resolve(extension.id), extension)
        self.assertTrue(registry.accepts("package.cad.surface", "asset.cad"))
        self.assertEqual(registry.resolve("package.cad.surface").id, "package.cad.surface")

    def test_registry_rejects_unknown_or_unordered_extensions(self):
        registry = create_core_port_type_registry()
        with self.assertRaises(LookupError):
            registry.require("future.unknown")
        with self.assertRaises(ValueError):
            registry.register(PortTypeDefinition("package.orphan", "Orphan", ("package.missing",)))
        with self.assertRaises(ValueError):
            registry.register(PortTypeDefinition("asset.image", "Duplicate"))


if __name__ == "__main__":
    unittest.main()

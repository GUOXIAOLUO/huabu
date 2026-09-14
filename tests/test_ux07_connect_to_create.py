import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "static/js/workbench/canvas/command-registry.js"
RECORDS = ROOT / "static/js/workbench/canvas/canvas-app-records.js"
MEDIA_EDITOR = ROOT / "static/js/workbench/canvas/canvas-app-media-editor.js"


class UX07ConnectToCreateTests(unittest.TestCase):
    def test_connection_picker_reuses_shared_picker_and_typed_compatibility(self):
        records = RECORDS.read_text(encoding="utf-8")
        block = records[records.index("function openLinkCreateMenu"):records.index("function openGeneratorNodeMenu")]
        self.assertIn("nodePickerMode = 'connection'", block)
        self.assertIn("picker.setEntries(entries)", block)
        self.assertIn("WorkbenchCanvasPortCompatibility?.isCompatible", block)
        self.assertIn("versionedConnectedCanvasKinds?.includes('classic')", block)

    def test_connection_selection_uses_atomic_graph_service_path(self):
        media = MEDIA_EDITOR.read_text(encoding="utf-8")
        block = media[media.index("async function createVersionedLinkedGroup"):media.index("function createNodeByType")]
        self.assertIn("createNodeAndEdge(canvas.id", block)
        self.assertIn("applyGraphCreationResult", block)
        self.assertNotIn("connections.push", block)

    def test_classic_catalog_exposes_all_supported_legacy_connected_definitions(self):
        registry = REGISTRY.read_text(encoding="utf-8")
        image_start = registry.index("['canvas.create.image'")
        image_end = registry.index("['canvas.create.prompt'", image_start)
        image = registry[image_start:image_end]
        self.assertIn("['classic', 'smart']", image)
        for definition in ("image", "prompt", "loop", "group"):
            self.assertIn(f"['canvas.create.{definition}'", registry)


if __name__ == "__main__":
    unittest.main()

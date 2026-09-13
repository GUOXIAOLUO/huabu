import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PromptResourceUiTests(unittest.TestCase):
    def setUp(self):
        self.source = (ROOT / "static/js/asset-manager.js").read_text(encoding="utf-8")

    def test_prompt_tab_is_a_resource_view_backed_by_canonical_prompt_api(self):
        render_start = self.source.index("function renderPromptManager(){")
        render_end = self.source.index("function renderLegacyPromptManager", render_start)
        render = self.source[render_start:render_end]
        self.assertIn("Prompt Resources", render)
        self.assertIn("data-resource-prompt", render)
        self.assertIn("data-resource-prompt-version", render)
        self.assertNotIn("/api/prompt-libraries", render)
        self.assertNotIn("data-prompt-lib-new", render)
        self.assertIn("data-prompt-compatibility", render)
        self.assertIn("renderLegacyPromptManager", self.source)

    def test_legacy_prompt_library_remains_explicitly_reachable_for_compatibility(self):
        self.assertIn("function renderLegacyPromptManager()", self.source)
        self.assertIn("async function loadLegacyPromptLibraries()", self.source)
        self.assertIn("data-prompt-compatibility", self.source)
        self.assertIn("renderPromptTreeBranch(item)", self.source)
        self.assertIn("/api/prompt-libraries/items", self.source)

        load_all = self.source[self.source.index("async function loadAll()"):self.source.index("function renderPromptManager")]
        self.assertNotIn("apiJson('/api/prompt-libraries')", load_all)

    def test_prompt_resource_operations_list_versions_and_write_new_versions(self):
        self.assertIn("/api/v1/prompts?project_id=", self.source)
        self.assertIn("&q=${encodeURIComponent(String(query || '').trim())}", self.source)
        self.assertIn("searchId === 'promptSearch' && !promptCompatibilityMode", self.source)
        self.assertIn("id === 'promptSearch' && !promptCompatibilityMode", self.source)
        self.assertIn("scheduleResourcePromptSearch", self.source)
        self.assertIn("/api/v1/prompts/${encodeURIComponent(id)}/versions/${version}", self.source)
        self.assertIn("/api/v1/prompts/${encodeURIComponent(resourcePromptEditor.id)}/versions", self.source)
        self.assertIn("method:'POST'", self.source)
        self.assertIn("metadata:{source:'resource_library'}", self.source)
        self.assertIn("source_id", self.source)
        self.assertIn("const editable = entry?.source === 'project'", self.source)
        self.assertIn("${editable ? '新版本' : '只读'}", self.source)
        self.assertIn("activeTab === 'prompts'", self.source)

    def test_asset_manager_prompt_resource_script_is_valid_javascript(self):
        result = subprocess.run(["node", "--check", str(ROOT / "static/js/asset-manager.js")], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()

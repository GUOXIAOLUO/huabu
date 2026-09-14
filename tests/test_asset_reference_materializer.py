import json
import subprocess
import unittest
from pathlib import Path

from workbench.application.asset_reference import AssetVersionReferenceValidator
from workbench.domain.asset import AssetVersionRef


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "static/js/workbench/canvas/asset-reference-materializer.js"


def run_js(program: str) -> dict:
    result = subprocess.run(["node", "-e", program], check=True, capture_output=True, text=True)
    return json.loads(result.stdout)


class AssetReferenceMaterializerTests(unittest.TestCase):
    def test_server_validator_requires_existing_version_in_target_project(self):
        class Assets:
            def get(self, asset_id, *, actor_id):
                if asset_id != "asset-1":
                    raise LookupError("missing asset")
                return type("Asset", (), {"project_id": "project-1", "id": asset_id})()

            def get_version(self, asset_id, version_id, *, actor_id):
                if version_id != "version-2":
                    raise LookupError("missing version")
                return type("Version", (), {"asset_id": asset_id})()

        validator = AssetVersionReferenceValidator(Assets())
        validator.validate(actor_id="user-1", project_id="project-1", reference=AssetVersionRef(asset_id="asset-1", version_id="version-2"))
        with self.assertRaises(PermissionError):
            validator.validate(actor_id="user-1", project_id="project-2", reference=AssetVersionRef(asset_id="asset-1", version_id="version-2"))
        with self.assertRaises(LookupError):
            validator.validate(actor_id="user-1", project_id="project-1", reference=AssetVersionRef(asset_id="asset-1", version_id="missing"))

    def test_server_validator_normalizes_repository_not_found(self):
        from workbench.repositories.asset_repository import AssetRepositoryNotFoundError

        class MissingAssets:
            def get(self, asset_id, *, actor_id):
                raise AssetRepositoryNotFoundError("missing")

            def get_version(self, asset_id, version_id, *, actor_id):
                raise AssetRepositoryNotFoundError("missing")

        validator = AssetVersionReferenceValidator(MissingAssets())
        with self.assertRaises(LookupError):
            validator.validate(actor_id="user-1", project_id="project-1", reference=AssetVersionRef(asset_id="asset-1", version_id="version-2"))

    def test_payload_and_command_keep_only_exact_version_identity(self):
        source = MODULE.read_text()
        result = run_js(f"""
const window = {{}}; global.window = window; eval({json.dumps(source)});
const dt = {{getData: type => type === window.WorkbenchAssetReferenceMaterializer.DATA_TYPE
  ? JSON.stringify({{kind:'asset_version', asset_id:'asset-1', version_id:'version-2', label:'Hero', type:'image', mime_type:'image/png', location:'/secret'}}) : ''}};
const item = window.WorkbenchAssetReferenceMaterializer.payload(dt);
const command = window.WorkbenchAssetReferenceMaterializer.command({{dataTransfer:dt, projectId:'project-1', canvasId:'canvas-1', position:{{x:10,y:20}}, expectedRevision:3}});
console.log(JSON.stringify({{item, command}}));
""")
        self.assertEqual(result["item"]["reference"], {"asset_id": "asset-1", "version_id": "version-2"})
        self.assertNotIn("location", json.dumps(result))
        self.assertEqual(result["command"]["initialConfig"]["asset_version_ref"], result["item"]["reference"])
        self.assertEqual(result["command"]["source"], "asset_reference_drag")

    def test_invalid_payload_is_rejected_and_creation_is_injected(self):
        source = MODULE.read_text()
        result = run_js(f"""
const window = {{}}; global.window = window; eval({json.dumps(source)});
const M = window.WorkbenchAssetReferenceMaterializer; let calls = [];
const valid = {{kind:'asset_version', asset_id:'a', version_id:'v', label:'A'}};
const options = {{payload:M.payload({{getData:() => JSON.stringify(valid)}}), projectId:'p', canvasId:'c', position:{{x:1,y:2}}, createNode: request => {{ calls.push(request); return 'created'; }}}};
const created = M.create(options); M.create({{...options, position:{{x:3,y:4}}}});
let invalid = false; try {{ M.command({{payload:M.payload({{getData:() => JSON.stringify({{kind:'asset_version', asset_id:'a'}})}}), projectId:'p', canvasId:'c', position:{{x:1,y:2}}}}); }} catch (_) {{ invalid = true; }}
console.log(JSON.stringify({{created, calls, invalid}}));
""")
        self.assertEqual(result["created"], "created")
        self.assertEqual(len(result["calls"]), 2)
        self.assertEqual(result["calls"][0]["initialConfig"]["asset_version_ref"], {"asset_id": "a", "version_id": "v"})
        self.assertEqual(result["calls"][1]["initialConfig"]["asset_version_ref"], result["calls"][0]["initialConfig"]["asset_version_ref"])
        self.assertTrue(result["invalid"])

    def test_canvas_wires_reference_drop_without_copying_location(self):
        source = (ROOT / "static/js/workbench/canvas/canvas-app-interaction.js").read_text()
        self.assertIn("WorkbenchAssetReferenceMaterializer?.payload", source)
        self.assertIn("WorkbenchAssetReferenceMaterializer.create", source)
        self.assertIn("asset_version_ref", source)
        self.assertIn("url:'',", source)
        start = source.index("WorkbenchAssetReferenceMaterializer.create")
        self.assertNotIn("content", source[start:start + 2200])


if __name__ == "__main__":
    unittest.main()

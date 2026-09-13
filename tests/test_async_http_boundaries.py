import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class AsyncHttpBoundaryTests(unittest.TestCase):
    def test_async_upload_routes_do_not_call_requests_directly(self):
        tree = ast.parse((ROOT / "main.py").read_text(encoding="utf-8"))
        names = {"upload_image", "upload_comfyui_base64"}
        for node in tree.body:
            if not isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)) or node.name not in names:
                continue
            direct_calls = [
                call for call in ast.walk(node)
                if isinstance(call, ast.Call)
                and isinstance(call.func, ast.Attribute)
                and isinstance(call.func.value, ast.Name)
                and call.func.value.id in {"requests", "urllib"}
            ]
            self.assertFalse(direct_calls, f"{node.name} blocks the event loop with synchronous HTTP")


if __name__ == "__main__":
    unittest.main()

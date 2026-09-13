import unittest

from fastapi import HTTPException

import main


class WorkflowPathValidationTests(unittest.TestCase):
    def test_workflow_path_resolver_accepts_valid_workflow_names(self):
        path = main.workflow_path_from_name("custom/example.json")
        self.assertTrue(path.startswith(main.WORKFLOW_DIR))
        self.assertTrue(path.endswith("/custom/example.json"))

    def test_generate_rejects_invalid_workflow_names_before_execution(self):
        for name in ("../x.json", "/tmp/x.json", "custom\\x.json", "x.yaml"):
            with self.subTest(name=name):
                with self.assertRaises(HTTPException) as caught:
                    main.generate(main.GenerateRequest(workflow_json=name))
                self.assertEqual(caught.exception.status_code, 400)
                self.assertEqual(caught.exception.detail, "Invalid workflow name")


if __name__ == "__main__":
    unittest.main()

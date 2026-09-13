import asyncio
import unittest
from unittest.mock import patch

from fastapi import HTTPException

import main


class StorageCapabilityTests(unittest.TestCase):
    def test_privileged_storage_is_disabled_for_non_loopback_bind_hosts(self):
        self.assertTrue(main.privileged_filesystem_is_enabled_for_host("127.0.0.1"))
        self.assertTrue(main.privileged_filesystem_is_enabled_for_host("localhost"))
        self.assertTrue(main.privileged_filesystem_is_enabled_for_host("::1"))
        self.assertFalse(main.privileged_filesystem_is_enabled_for_host("0.0.0.0"))
        self.assertFalse(main.privileged_filesystem_is_enabled_for_host("::"))

    def test_storage_settings_mutation_is_rejected_in_lan_mode(self):
        with patch.object(main, "WORKBENCH_HOST", "0.0.0.0"), patch.object(main, "save_storage_settings") as save:
            with self.assertRaises(HTTPException) as caught:
                asyncio.run(main.update_storage_settings({"input": "/tmp/unsafe"}))
        self.assertEqual(caught.exception.status_code, 403)
        save.assert_not_called()

    def test_all_storage_endpoints_require_the_privileged_capability_in_lan_mode(self):
        calls = (
            lambda: main.get_storage_settings(),
            lambda: main.list_storage_files(),
            lambda: main.get_storage_file("generated", "image.png"),
            lambda: main.delete_storage_files({"kind": "generated", "items": ["image.png"]}),
        )
        with patch.object(main, "WORKBENCH_HOST", "::"):
            for call in calls:
                with self.subTest(call=call):
                    with self.assertRaises(HTTPException) as caught:
                        asyncio.run(call())
                    self.assertEqual(caught.exception.status_code, 403)


if __name__ == "__main__":
    unittest.main()

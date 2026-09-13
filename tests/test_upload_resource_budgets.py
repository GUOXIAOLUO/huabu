import asyncio
import unittest
from unittest.mock import patch

import main


class _Upload:
    filename = "large.png"
    content_type = "image/png"

    def __init__(self, chunks):
        self.chunks = list(chunks)
        self.read_sizes = []

    async def read(self, size=-1):
        self.read_sizes.append(size)
        return self.chunks.pop(0) if self.chunks else b""


class UploadResourceBudgetTests(unittest.TestCase):
    def test_upload_reader_checks_limits_while_streaming(self):
        upload = _Upload([b"12345"])
        with self.assertRaises(main.HTTPException) as caught:
            asyncio.run(main.read_upload_file_limited(upload, max_bytes=4))
        self.assertEqual(caught.exception.status_code, 413)
        self.assertEqual(upload.read_sizes, [main.UPLOAD_CHUNK_BYTES])

    def test_workflow_import_rejects_oversized_raw_upload_before_parsing(self):
        upload = _Upload([b"12345"])
        upload.filename = "workflow.json"
        with patch.object(main, "WORKFLOW_ZIP_MAX_BYTES", 4), patch.object(main.zipfile, "ZipFile") as zip_file:
            with self.assertRaises(main.HTTPException) as caught:
                asyncio.run(main.import_canvas_workflow(upload))
        self.assertEqual(caught.exception.status_code, 413)
        zip_file.assert_not_called()


if __name__ == "__main__":
    unittest.main()

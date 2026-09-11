import asyncio
import unittest
from unittest.mock import patch

from fastapi import HTTPException

import main


class _Upload:
    def __init__(self, name, chunks):
        self.filename = name
        self.content_type = "image/png"
        self._chunks = list(chunks)

    async def read(self, _size):
        return self._chunks.pop(0) if self._chunks else b""


class _Response:
    status_code = 200

    @staticmethod
    def json():
        return {"name": "stored.png"}


class UploadLimitTests(unittest.TestCase):
    def test_normal_upload_streams_chunks_to_backend(self):
        with patch.object(main.requests, "post", return_value=_Response()) as post:
            result = asyncio.run(main.upload_image([_Upload("a.png", [b"ab", b"cd"])]))
        self.assertEqual(result, {"files": [{"comfy_name": "stored.png"}]})
        self.assertTrue(post.called)

    def test_single_file_and_total_limits_return_413(self):
        with patch.object(main, "UPLOAD_FILE_MAX_BYTES", 3), self.assertRaises(HTTPException) as single:
            asyncio.run(main.upload_image([_Upload("a.png", [b"1234"])]))
        self.assertEqual(single.exception.status_code, 413)
        with patch.object(main, "UPLOAD_FILE_MAX_BYTES", 10), patch.object(main, "UPLOAD_REQUEST_MAX_BYTES", 3), patch.object(main.requests, "post", return_value=_Response()), self.assertRaises(HTTPException) as total:
            asyncio.run(main.upload_image([_Upload("a.png", [b"12"]), _Upload("b.png", [b"34"])]))
        self.assertEqual(total.exception.status_code, 413)

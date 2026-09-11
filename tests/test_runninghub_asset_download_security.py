import asyncio
import socket
import unittest
from unittest.mock import patch

from fastapi import HTTPException

import main


class _Response:
    def __init__(self, *, status_code=200, headers=None, chunks=(b"asset",), payload=None):
        self.status_code = status_code
        self.headers = headers or {"content-type": "image/png"}
        self._chunks = tuple(chunks)
        self._payload = payload or {"code": 0, "data": {"fileName": "uploaded.png"}}

    @property
    def content(self):
        return b"".join(self._chunks)

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError("download failed")

    def json(self):
        return self._payload

    async def aiter_bytes(self):
        for chunk in self._chunks:
            yield chunk

    async def aclose(self):
        return None


class _Client:
    def __init__(self, responses):
        self.responses = list(responses)
        self.sent_urls = []

    async def get(self, url, **_kwargs):
        self.sent_urls.append(url)
        return self.responses.pop(0)

    def build_request(self, _method, url):
        return url

    async def send(self, request, **_kwargs):
        self.sent_urls.append(request)
        return self.responses.pop(0)

    async def post(self, *_args, **_kwargs):
        return _Response()


class RunningHubAssetDownloadSecurityTests(unittest.TestCase):
    provider = {"id": "runninghub", "base_url": "https://www.runninghub.ai", "api_key": "test-key"}

    @staticmethod
    def public_dns(host, *_args, **_kwargs):
        if str(host) == "127.0.0.1":
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 0))]
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0))]

    def test_rejects_loopback_and_private_targets_before_download(self):
        for url in ("http://localhost/asset.png", "http://127.0.0.1/asset.png", "http://[::1]/asset.png", "http://10.0.0.7/asset.png"):
            client = _Client([_Response()])
            with self.subTest(url=url), self.assertRaises(HTTPException) as error:
                asyncio.run(main.runninghub_upload_local_to_filename(client, self.provider, url))
            self.assertEqual(error.exception.status_code, 400)
            self.assertEqual(client.sent_urls, [])

    def test_redirect_to_private_target_is_rejected(self):
        client = _Client([_Response(status_code=302, headers={"location": "http://127.0.0.1/internal"})])
        with patch.object(main.socket, "getaddrinfo", self.public_dns), self.assertRaises(HTTPException) as error:
            asyncio.run(main.runninghub_upload_local_to_filename(client, self.provider, "https://public.example/asset.png"))
        self.assertEqual(error.exception.status_code, 400)
        self.assertEqual(client.sent_urls, ["https://public.example/asset.png"])

    def test_rejects_oversized_response_without_uploading_it(self):
        client = _Client([_Response(chunks=(b"12345",))])
        with patch.object(main.socket, "getaddrinfo", self.public_dns), patch.object(main, "RUNNINGHUB_REMOTE_ASSET_MAX_BYTES", 4), self.assertRaises(HTTPException) as error:
            asyncio.run(main.runninghub_upload_local_to_filename(client, self.provider, "https://public.example/asset.png"))
        self.assertEqual(error.exception.status_code, 413)

    def test_accepts_public_asset_with_streamed_download(self):
        client = _Client([_Response(chunks=(b"ab", b"cd"))])
        with patch.object(main.socket, "getaddrinfo", self.public_dns), patch.object(main, "runninghub_app_headers", return_value={}):
            filename = asyncio.run(main.runninghub_upload_local_to_filename(client, self.provider, "https://public.example/asset.png"))
        self.assertEqual(filename, "uploaded.png")

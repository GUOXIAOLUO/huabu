import unittest
from unittest.mock import patch

from fastapi import HTTPException

import main


class _Response:
    def __init__(self, *, status_code=200, headers=None, chunks=(b"asset",)):
        self.status_code = status_code
        self.headers = headers or {"content-type": "image/png"}
        self._chunks = chunks
        self.closed = False

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError("download failed")

    def iter_content(self, chunk_size=None):
        return iter(self._chunks)

    def close(self):
        self.closed = True


class SafeRemoteFetchTests(unittest.TestCase):
    @staticmethod
    def public_dns(host, *_args, **_kwargs):
        import socket

        if host == "127.0.0.1":
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 0))]
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0))]

    def test_fetch_remote_media_rejects_private_target_before_request(self):
        with patch.object(main.socket, "getaddrinfo", self.public_dns), patch.object(main.requests, "get") as get:
            with self.assertRaises(HTTPException) as caught:
                main.fetch_remote_media_bytes("http://127.0.0.1/asset.png")
        self.assertEqual(caught.exception.status_code, 400)
        get.assert_not_called()

    def test_fetch_remote_media_rejects_redirect_to_private_target(self):
        response = _Response(status_code=302, headers={"location": "http://127.0.0.1/internal"})
        with patch.object(main.socket, "getaddrinfo", self.public_dns), patch.object(main.requests, "get", return_value=response) as get:
            with self.assertRaises(HTTPException) as caught:
                main.fetch_remote_media_bytes("https://public.example/asset.png")
        self.assertEqual(caught.exception.status_code, 400)
        self.assertEqual(get.call_count, 1)
        response.close()


if __name__ == "__main__":
    unittest.main()

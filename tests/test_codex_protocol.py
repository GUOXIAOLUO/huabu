import unittest

from workbench.codex.protocol import (
    CodexProtocolCompatibility,
    CodexProtocolError,
    InitializeResult,
    ProtocolRequest,
    ProtocolResponse,
    parse_server_message,
)


class CodexProtocolTests(unittest.TestCase):
    def test_protocol_messages_validate_and_preserve_wire_aliases(self):
        request = ProtocolRequest(id=1, method="initialize", params={"clientInfo": {}})
        self.assertEqual(request.model_dump(by_alias=True), {"id": 1, "method": "initialize", "params": {"clientInfo": {}}})
        response = parse_server_message(
            b'{"id":1,"result":{"protocolVersion":"2","serverInfo":{"version":"future"}}}'
        )
        self.assertIsInstance(response, ProtocolResponse)
        initialized = InitializeResult.model_validate(response.result)
        self.assertEqual(CodexProtocolCompatibility.validate_initialize(initialized).protocol_version, "2")
        self.assertEqual(initialized.serverInfo["version"], "future")

    def test_protocol_parser_rejects_invalid_envelopes_and_versions(self):
        with self.assertRaises(CodexProtocolError):
            parse_server_message(b'{"id":"not-an-integer","result":{}}')
        with self.assertRaises(CodexProtocolError):
            CodexProtocolCompatibility.validate_initialize(InitializeResult(protocolVersion="1"))
        with self.assertRaises(ValueError):
            ProtocolResponse(id=1, result={}, error={})

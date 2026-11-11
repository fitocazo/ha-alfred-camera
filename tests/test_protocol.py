import base64
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("alfred_client_under_test", ROOT / "custom_components/alfred_snapshot/client.py")
client = importlib.util.module_from_spec(spec)
spec.loader.exec_module(client)

def fake_session(domain="sa-xmpp.my-alfred.com", resource="ivuu31WebViewerABCDEF120000"):
    claims = {"xmpp_jid": f"test@{domain}/{resource}", "exp": 2000000000}
    encoded = base64.urlsafe_b64encode(json.dumps(claims).encode()).decode().rstrip("=")
    return {"uid": "test", "jid": f"test@example.invalid/{resource}", "resource": resource, "kvToken": "test." + encoded + ".test"}

class ProtocolTests(unittest.TestCase):
    def test_snapshot_request_matches_observed_wire_format(self):
        self.assertEqual(base64.b64encode(client.request()).decode(), "EAEYAiABMgYIgAUQ6AI=")
    def test_wire_roundtrip(self):
        for value in (0, 1, 127, 128, 640, 360, 65535):
            self.assertEqual(client.fields(client.integer(1, value))[1], value)
    def test_truncated_payload_is_rejected(self):
        with self.assertRaises(client.ProtocolError):
            client.fields(bytes([50, 5, 1, 2]))
    def test_invalid_varint_is_rejected(self):
        with self.assertRaises(client.ProtocolError):
            client.fields(bytes([128])*11)
    def test_xmpp_jid_is_distinct_from_email_jid(self):
        auth = client.session_from_json(json.dumps(fake_session()))
        self.assertNotEqual(auth["jid"], auth["xmppJid"])
        self.assertTrue(auth["xmppJid"].startswith("test@sa-xmpp.my-alfred.com/"))
    def test_external_domain_is_rejected(self):
        with self.assertRaises(client.AuthError):
            client.session_from_json(json.dumps(fake_session(domain="example.invalid")))
    def test_resource_mismatch_is_rejected(self):
        auth = fake_session()
        auth["resource"] = "another-resource"
        with self.assertRaises(client.AuthError):
            client.session_from_json(json.dumps(auth))

if __name__ == "__main__":
    unittest.main()

"""Exercise actual HTTP serialization without contacting a paid image endpoint."""
import json
import os
from pathlib import Path
import shutil
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import generate_image as g


class Handler(BaseHTTPRequestHandler):
    requests = []

    def log_message(self, *_):
        pass

    def do_GET(self):
        self.requests.append(("GET", self.headers.get("Authorization"), None))
        raw = json.dumps({"data": [{"id": "gpt-image-2.5-sunburst"}]}).encode()
        self.send_response(200)
        self.end_headers()
        self.wfile.write(raw)

    def do_POST(self):
        payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        self.requests.append(("POST", self.headers.get("Authorization"), payload))
        self.send_response(400 if self.path == "/reject" else 200)
        self.end_headers()
        self.wfile.write(json.dumps({"data": [{"b64_json": "cG5n"}]}).encode())


@unittest.skipUnless(shutil.which("curl.exe" if os.name == "nt" else "curl"), "curl unavailable")
class ImageTransportTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.url = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def setUp(self):
        Handler.requests.clear()

    def test_prompt_roundtrip_and_credential_privacy(self):
        payload = {"prompt": '中文方法图\n"quoted" \\ path\t$() `code`', "quality": "high"}
        real_run = g.subprocess.run
        with patch.object(g.subprocess, "run", wraps=real_run) as run:
            response = g.curl_request(self.url + "/images/generations", "private-test-key", payload)
        self.assertIn(b"b64_json", response)
        self.assertEqual(Handler.requests, [("POST", "Bearer private-test-key", payload)])
        command = run.call_args.args[0]
        self.assertNotIn("private-test-key", " ".join(command))
        self.assertNotIn("--insecure", command)
        self.assertEqual(command[command.index("--retry") + 1], "0")

    def test_discovery_uses_same_transport(self):
        with patch.dict(os.environ, {"ASSET_IMAGE_HTTP_TRANSPORT": "curl"}):
            response = g.request_models(self.url + "/models", "test")
        self.assertEqual(response["data"][0]["id"], "gpt-image-2.5-sunburst")
        self.assertEqual(Handler.requests[0][:2], ("GET", "Bearer test"))

    def test_http_rejection_is_not_retried(self):
        with self.assertRaisesRegex(SystemExit, "HTTP 400"):
            g.curl_request(self.url + "/reject", "test", {"prompt": "a"})
        self.assertEqual(len(Handler.requests), 1)

    def test_explicit_proxy_stays_out_of_command_line(self):
        reply = g.subprocess.CompletedProcess([], 0, stdout=b'{"data": []}\n200', stderr=b'')
        with patch.dict(os.environ, {"ASSET_IMAGE_HTTP_PROXY": "http://private-user:private-pass@127.0.0.1:7897"}):
            with patch.object(g.subprocess, "run", return_value=reply) as run:
                g.curl_request(self.url)
        self.assertNotIn("private-pass", " ".join(run.call_args.args[0]))
        self.assertIn(b'proxy = "http://private-user:private-pass@127.0.0.1:7897"', run.call_args.kwargs["input"])

    def test_header_injection_is_rejected_before_request(self):
        with self.assertRaisesRegex(SystemExit, "newline"):
            g.curl_request(self.url, "key\r\nInjected: header")
        self.assertEqual(Handler.requests, [])


if __name__ == "__main__":
    unittest.main()

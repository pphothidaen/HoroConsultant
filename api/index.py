from http.server import BaseHTTPRequestHandler

from api.main import _dispatch


class handler(BaseHTTPRequestHandler):
    def _send_response(self, payload, status=200):
        self.send_response(status)
        self.send_header("Content-Type", payload["headers"].get("Content-Type", "application/json; charset=utf-8"))
        for key, value in payload["headers"].items():
            if key.lower() != "content-type":
                self.send_header(key, value)
        self.end_headers()
        self.wfile.write(payload["body"])

    def do_GET(self):
        headers = {key.lower(): value for key, value in self.headers.items()}
        response = _dispatch("GET", self.path, headers, b"")
        self._send_response(response, response["status"])

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else b""
        headers = {key.lower(): value for key, value in self.headers.items()}
        response = _dispatch("POST", self.path, headers, body)
        self._send_response(response, response["status"])

    def do_OPTIONS(self):
        headers = {key.lower(): value for key, value in self.headers.items()}
        response = _dispatch("OPTIONS", self.path, headers, b"")
        self._send_response(response, response["status"])

    def log_message(self, format, *args):
        return

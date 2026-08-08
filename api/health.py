from http.server import BaseHTTPRequestHandler
import json

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Credentials', 'true')
        self.end_headers()
        response_data = {
            "status": "ok",
            "service": "Computational Metaphysics Engine",
            "version": "1.0.0"
        }
        self.wfile.write(json.dumps(response_data).encode('utf-8'))

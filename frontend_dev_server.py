"""
frontend_dev_server.py - Localhost Frontend Dev Server on port 5173
SIH PS ID: 260001 Prototype

Serves the frontend on http://localhost:5173 and provides an active proxy to http://localhost:8000
for seamless, zero-CORS local development and demonstration.
"""

import http.server
import socketserver
import urllib.request
import urllib.error
import os
import sys

PORT = 5173
BACKEND_TARGET = "http://localhost:8000"
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend", "static")
HTML_FILE = os.path.join(STATIC_DIR, "index.html")

class FrontendDevHandler(http.server.BaseHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        if self.path.startswith("/api/") or self.path.startswith("/health"):
            self.proxy_request("GET")
        elif self.path in ("/", "/index.html", ""):
            self.serve_file(HTML_FILE, "text/html; charset=utf-8")
        else:
            # Check if requested file exists in STATIC_DIR or frontend
            rel_path = self.path.lstrip("/")
            file_path = os.path.join(STATIC_DIR, rel_path)
            if os.path.isfile(file_path):
                ext = os.path.splitext(file_path)[1].lower()
                content_type = "text/html"
                if ext == ".js": content_type = "application/javascript"
                elif ext == ".css": content_type = "text/css"
                elif ext == ".json": content_type = "application/json"
                elif ext == ".svg": content_type = "image/svg+xml"
                elif ext in (".png", ".jpg", ".jpeg"): content_type = f"image/{ext.lstrip('.')}"
                self.serve_file(file_path, content_type)
            else:
                # Fallback to SPA index.html
                self.serve_file(HTML_FILE, "text/html; charset=utf-8")

    def do_POST(self):
        if self.path.startswith("/api/") or self.path.startswith("/health"):
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length) if content_length > 0 else None
            self.proxy_request("POST", body=body)
        else:
            self.send_error(404, "Not Found")

    def serve_file(self, file_path, content_type):
        if not os.path.exists(file_path):
            self.send_error(404, "File Not Found")
            return
        with open(file_path, "rb") as f:
            content = f.read()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def proxy_request(self, method, body=None):
        target_url = f"{BACKEND_TARGET}{self.path}"
        try:
            req_headers = {k: v for k, v in self.headers.items() if k.lower() not in ("host", "content-length")}
            req_headers["User-Agent"] = "FrontendDevProxy/1.0"
            req = urllib.request.Request(target_url, data=body, headers=req_headers, method=method)
            with urllib.request.urlopen(req, timeout=15) as resp:
                resp_body = resp.read()
                self.send_response(resp.status)
                for header, val in resp.getheaders():
                    if header.lower() not in ("access-control-allow-origin", "content-length", "transfer-encoding"):
                        self.send_header(header, val)
                self.send_header("Content-Length", str(len(resp_body)))
                self.end_headers()
                self.wfile.write(resp_body)
        except urllib.error.HTTPError as e:
            err_body = e.read()
            self.send_response(e.code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(err_body)))
            self.end_headers()
            self.wfile.write(err_body)
        except Exception as e:
            err_msg = f'{{"error": "Proxy error", "detail": "{str(e)}"}}\n'.encode("utf-8")
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(err_msg)))
            self.end_headers()
            self.wfile.write(err_msg)

    def log_message(self, format, *args):
        # Keep console output clean
        pass

if __name__ == "__main__":
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), FrontendDevHandler) as httpd:
        print(f"Frontend Dev Server running on http://localhost:{PORT} (Proxying to {BACKEND_TARGET})")
        sys.stdout.flush()
        httpd.serve_forever()

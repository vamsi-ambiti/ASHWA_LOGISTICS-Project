#!/usr/bin/env python
"""
Ashwa Logistics — Dedicated Frontend Server
Serves the customer & admin frontend on http://127.0.0.1:5500 (or fallback 5501) with clean URL routing
and CORS headers enabled.
"""

import http.server
import socketserver
import os
import sys
import socket
import mimetypes
from pathlib import Path
from urllib.parse import urlparse

# Ensure utf-8 console output on Windows
if sys.platform == 'win32' and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

DEFAULT_PORT = 5500
BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR / "frontend"
STATIC_DIR = FRONTEND_DIR / "static"

# URL route mappings
ROUTE_MAP = {
    "/": FRONTEND_DIR / "index.html",
    "/index": FRONTEND_DIR / "index.html",
    "/index.html": FRONTEND_DIR / "index.html",
    "/frontend": FRONTEND_DIR / "index.html",
    "/frontend/": FRONTEND_DIR / "index.html",
    "/frontend/index.html": FRONTEND_DIR / "index.html",

    "/login": FRONTEND_DIR / "login.html",
    "/login/": FRONTEND_DIR / "login.html",
    "/login.html": FRONTEND_DIR / "login.html",
    "/frontend/login.html": FRONTEND_DIR / "login.html",

    "/signup": FRONTEND_DIR / "signup.html",
    "/signup/": FRONTEND_DIR / "signup.html",
    "/signup.html": FRONTEND_DIR / "signup.html",
    "/frontend/signup.html": FRONTEND_DIR / "signup.html",

    "/enquiry": FRONTEND_DIR / "enquiry.html",
    "/enquiry/": FRONTEND_DIR / "enquiry.html",
    "/enquiry.html": FRONTEND_DIR / "enquiry.html",
    "/frontend/enquiry.html": FRONTEND_DIR / "enquiry.html",

    "/contact": FRONTEND_DIR / "contact.html",
    "/contact/": FRONTEND_DIR / "contact.html",
    "/contact.html": FRONTEND_DIR / "contact.html",
    "/frontend/contact.html": FRONTEND_DIR / "contact.html",

    "/admin": FRONTEND_DIR / "admin_login.html",
    "/admin/": FRONTEND_DIR / "admin_login.html",
    "/admin/login": FRONTEND_DIR / "admin_login.html",
    "/admin/login/": FRONTEND_DIR / "admin_login.html",
    "/admin_login.html": FRONTEND_DIR / "admin_login.html",
    "/frontend/admin_login.html": FRONTEND_DIR / "admin_login.html",

    "/admin/dashboard": FRONTEND_DIR / "admin_dashboard.html",
    "/admin/dashboard/": FRONTEND_DIR / "admin_dashboard.html",
    "/admin/dashboard.html": FRONTEND_DIR / "admin_dashboard.html",
    "/admin/dashboard/index.html": FRONTEND_DIR / "admin_dashboard.html",
    "/frontend/admin_dashboard.html": FRONTEND_DIR / "admin_dashboard.html",
    "/frontend/admin/dashboard/index.html": FRONTEND_DIR / "admin_dashboard.html",
    "/admin/login/index.html": FRONTEND_DIR / "admin_login.html",
    "/frontend/admin/login/index.html": FRONTEND_DIR / "admin_login.html",
}

class FrontendRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(FRONTEND_DIR), **kwargs)

    def end_headers(self):
        # Enable CORS and disable aggressive caching for dev server
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        super().end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        clean_path = parsed.path

        # Check clean URL route map
        if clean_path in ROUTE_MAP:
            target_file = ROUTE_MAP[clean_path]
            if target_file.exists():
                return self.serve_file(target_file, "text/html; charset=utf-8")

        # Static assets (support /static/... and /frontend/static/...)
        asset_path = clean_path
        if asset_path.startswith('/frontend/static/'):
            asset_path = asset_path[len('/frontend'):]

        if asset_path.startswith('/static/'):
            rel_path = asset_path[len('/static/'):]
            target_file = STATIC_DIR / rel_path
            if target_file.exists() and target_file.is_file():
                mime, _ = mimetypes.guess_type(str(target_file))
                return self.serve_file(target_file, mime or "application/octet-stream")

        # Reverse proxy backend API calls to Django port 8000
        if clean_path.startswith('/api/'):
            return self.proxy_to_backend()

        # Fall back to standard SimpleHTTPRequestHandler in FRONTEND_DIR
        return super().do_GET()

    def do_POST(self):
        clean_path = urlparse(self.path).path
        if clean_path.startswith('/api/'):
            return self.proxy_to_backend()
        return super().do_POST()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def proxy_to_backend(self):
        import urllib.request
        import urllib.error
        backend_url = f"http://127.0.0.1:8000{self.path}"
        try:
            req_headers = {k: v for k, v in self.headers.items() if k.lower() not in ('host', 'content-length')}
            body = None
            if self.command in ('POST', 'PUT', 'PATCH'):
                content_length = int(self.headers.get('Content-Length', 0))
                if content_length > 0:
                    body = self.rfile.read(content_length)

            req = urllib.request.Request(backend_url, data=body, headers=req_headers, method=self.command)
            with urllib.request.urlopen(req) as resp:
                self.send_response(resp.status)
                for k, v in resp.getheaders():
                    if k.lower() not in ('content-length', 'server', 'date', 'transfer-encoding'):
                        self.send_header(k, v)
                resp_body = resp.read()
                self.send_header('Content-Length', str(len(resp_body)))
                self.end_headers()
                self.wfile.write(resp_body)
        except urllib.error.HTTPError as e:
            self.send_response(e.code)
            for k, v in e.headers.items():
                if k.lower() not in ('content-length', 'server', 'date', 'transfer-encoding'):
                    self.send_header(k, v)
            err_body = e.read()
            self.send_header('Content-Length', str(len(err_body)))
            self.end_headers()
            self.wfile.write(err_body)
        except Exception as e:
            self.send_error(502, f"Backend connection failed: {e}")

    def serve_file(self, file_path: Path, content_type: str):
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_error(500, f"Error serving file: {e}")

    def log_message(self, format, *args):
        # Clean console log
        sys.stdout.write(f"[Frontend Server] {self.address_string()} - {args[0]} - {args[1]}\n")
        sys.stdout.flush()

def is_port_available(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("", port))
            return True
        except OSError:
            return False

def run_server(preferred_port=DEFAULT_PORT):
    socketserver.TCPServer.allow_reuse_address = True
    port = preferred_port
    if not is_port_available(port):
        print(f"[!] Notice: Port {port} is currently busy (e.g., Live Server or another app).")
        # Find next free port
        for candidate in [5501, 3000, 5000, 8080, 8081]:
            if is_port_available(candidate):
                port = candidate
                break
        print(f"[*] Automatically switched to available Port {port}.\n")

    with socketserver.TCPServer(("", port), FrontendRequestHandler) as httpd:
        print("=" * 65)
        print(">> ASHWA LOGISTICS - FRONTEND SERVER RUNNING")
        print("=" * 65)
        print(f"[*] Serving URL       : http://127.0.0.1:{port}/")
        print(f"[*] Customer Home     : http://127.0.0.1:{port}/")
        print(f"[*] Customer Login    : http://127.0.0.1:{port}/login/")
        print(f"[*] Customer Signup   : http://127.0.0.1:{port}/signup/")
        print(f"[*] Admin Portal      : http://127.0.0.1:{port}/admin/login/")
        print(f"[*] Admin Dashboard   : http://127.0.0.1:{port}/admin/dashboard/")
        print(f"[*] Backend API Host  : http://127.0.0.1:8000/api/")
        print("=" * 65)
        print("[*] Press Ctrl+C to stop the frontend server.\n")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n[*] Frontend server stopped.")

if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else DEFAULT_PORT
    run_server(port)


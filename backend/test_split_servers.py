import subprocess
import time
import urllib.request
import json
import sys
import socket
from pathlib import Path

# Ensure utf-8 console output on Windows
if sys.platform == 'win32' and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

def is_port_listening(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(('127.0.0.1', port)) == 0

def test_split_servers():
    print("=" * 60)
    print(">> ASHWA LOGISTICS -- SPLIT SERVER TEST SUITE")
    print("=" * 60)

    backend_proc = None
    frontend_proc = None

    # Determine frontend test port (use 5501 if 5500 is in use by VS Code Live Server)
    frontend_port = 5501 if is_port_listening(5500) else 5500
    print(f"[*] Target Backend Port : 8000")
    print(f"[*] Target Frontend Port: {frontend_port}")

    # Check / Start Backend
    if not is_port_listening(8000):
        print("[*] Starting Backend Server on port 8000...")
        backend_proc = subprocess.Popen(
            [sys.executable, "manage.py", "runserver", "127.0.0.1:8000"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        time.sleep(2)
    else:
        print("[*] Backend Server is already running on port 8000.")

    # Check / Start Frontend
    if not is_port_listening(frontend_port):
        print(f"[*] Starting Frontend Server on port {frontend_port}...")
        frontend_proc = subprocess.Popen(
            [sys.executable, "serve_frontend.py", str(frontend_port)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        time.sleep(2)
    else:
        print(f"[*] Frontend Server is already listening on port {frontend_port}.")

    passed = 0
    failed = 0

    def check(name, cond, details=""):
        nonlocal passed, failed
        if cond:
            print(f"[PASS] {name} {details}")
            passed += 1
        else:
            print(f"[FAIL] {name} {details}")
            failed += 1

    try:
        # 1. Test Frontend Routes
        routes = [
            (f"http://127.0.0.1:{frontend_port}/", "Homepage (index.html)"),
            (f"http://127.0.0.1:{frontend_port}/login/", "Login Page"),
            (f"http://127.0.0.1:{frontend_port}/signup/", "Signup Page"),
            (f"http://127.0.0.1:{frontend_port}/enquiry/", "Enquiry Page"),
            (f"http://127.0.0.1:{frontend_port}/contact/", "Contact Page"),
            (f"http://127.0.0.1:{frontend_port}/admin/login/", "Admin Login Page"),
            (f"http://127.0.0.1:{frontend_port}/admin/dashboard/", "Admin Dashboard Page"),
            (f"http://127.0.0.1:{frontend_port}/static/css/admin.css", "Static Admin CSS"),
            (f"http://127.0.0.1:{frontend_port}/static/js/app.js", "Static App JS")
        ]
        for url, desc in routes:
            try:
                req = urllib.request.Request(url)
                with urllib.request.urlopen(req, timeout=4) as resp:
                    check(f"Frontend Port {frontend_port}: {desc}", resp.status == 200, f"(HTTP {resp.status})")
            except Exception as e:
                check(f"Frontend Port {frontend_port}: {desc}", False, f"(Error: {e})")

        # 2. Test Backend Cross-Origin CORS from Frontend Origin
        api_url = "http://127.0.0.1:8000/api/shipments/PROD88291043/"
        req = urllib.request.Request(api_url, headers={
            'Origin': f'http://127.0.0.1:{frontend_port}',
            'Accept': 'application/json'
        })
        try:
            with urllib.request.urlopen(req, timeout=4) as resp:
                cors_origin = resp.headers.get('Access-Control-Allow-Origin')
                cors_cred = resp.headers.get('Access-Control-Allow-Credentials')
                check("Backend Port 8000: API accessible cross-origin", resp.status == 200)
                check("Backend Port 8000: CORS Allow-Origin header", cors_origin in [f'http://127.0.0.1:{frontend_port}', '*'], f"(Got: {cors_origin})")
                check("Backend Port 8000: CORS Allow-Credentials header", cors_cred == 'true', f"(Got: {cors_cred})")
        except Exception as e:
            check("Backend Port 8000: API accessible with CORS", False, f"(Error: {e})")

        # 3. Test Backend POST API from Frontend Origin
        post_url = "http://127.0.0.1:8000/api/contact/"
        payload = json.dumps({
            'name': 'Split Server Tester',
            'email': 'tester@example.com',
            'message': 'Testing CORS POST from separate frontend'
        }).encode('utf-8')
        req = urllib.request.Request(post_url, data=payload, headers={
            'Origin': f'http://127.0.0.1:{frontend_port}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        try:
            with urllib.request.urlopen(req, timeout=4) as resp:
                body = json.loads(resp.read().decode('utf-8'))
                check("Backend Port 8000: Cross-Origin POST /api/contact/", resp.status == 200 and 'message' in body)
        except Exception as e:
            check("Backend Port 8000: Cross-Origin POST /api/contact/", False, f"(Error: {e})")

    finally:
        # Cleanly terminate child processes started by this script
        if frontend_proc:
            frontend_proc.terminate()
            try:
                frontend_proc.wait(timeout=2)
            except Exception:
                frontend_proc.kill()
        if backend_proc:
            backend_proc.terminate()
            try:
                backend_proc.wait(timeout=2)
            except Exception:
                backend_proc.kill()

    print(f"\n==========================================")
    print(f"SPLIT SERVER VERIFICATION: {passed} PASSED, {failed} FAILED")
    print(f"==========================================\n")
    return failed == 0

if __name__ == '__main__':
    success = test_split_servers()
    sys.exit(0 if success else 1)


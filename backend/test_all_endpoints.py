import os
import sys
import json
from pathlib import Path

# Ensure utf-8 console output on Windows
if sys.platform == 'win32' and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Setup Django environment
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ashwa.settings")

import django
django.setup()

from django.test import Client

def run_tests():
    print("[*] Starting Comprehensive Backend & Admin API Verification...")
    client = Client()
    passed = 0
    failed = 0

    def assert_test(name, condition, extra=""):
        nonlocal passed, failed
        if condition:
            print(f"[PASS] {name} {extra}")
            passed += 1
        else:
            print(f"[FAIL] {name} {extra}")
            failed += 1

    # 1. Django Backend Routing & Decoupling Tests
    res = client.get('/')
    assert_test("Backend Root (/) redirects to /admin/", res.status_code == 302 and res.url == '/admin/')

    res = client.get('/admin/', follow=True)
    assert_test("Django Admin (/admin/) renders official Django page", res.status_code == 200)

    res = client.get('/django-admin/', follow=True)
    assert_test("Django Admin alias (/django-admin/) renders", res.status_code == 200)

    res = client.get('/api/')
    assert_test("Backend API Index (/api/) returns JSON info", res.status_code == 200 and 'service' in res.json())

    # Verify website paths redirect to Frontend server (Port 5500)
    for path, label in [('/login/', 'Login'), ('/signup/', 'Signup'), ('/enquiry/', 'Enquiry'), ('/contact/', 'Contact')]:
        res = client.get(path)
        assert_test(f"Backend {path} redirects to Frontend Server", res.status_code == 302 and '5500' in res.url)

    # 2. Public Tracking API
    res = client.get('/api/shipments/PROD88291043/')
    assert_test("Public Tracking API (PROD88291043)", res.status_code == 200)
    data = res.json()
    assert_test("Tracking Payload contains milestones", 'tracking_history' in data.get('shipment', {}))
    assert_test("Tracking Status is DELIVERED", data.get('shipment', {}).get('status') == 'DELIVERED')

    # 3. Public Enquiry API
    res = client.post(
        '/api/enquiries/',
        data=json.dumps({'name': 'Test User', 'email': 'test@example.com', 'comment': 'Testing enquiry form'}),
        content_type='application/json'
    )
    assert_test("Public Enquiry Submission", res.status_code == 200)

    # 4. Public Contact API
    res = client.post(
        '/api/contact/',
        data=json.dumps({'name': 'Test User', 'email': 'test@example.com', 'message': 'Testing contact message'}),
        content_type='application/json'
    )
    assert_test("Public Contact Submission", res.status_code == 200)

    # 5. Customer Authentication & My Shipments
    res = client.post(
        '/api/login/',
        data=json.dumps({'email': 'rahul@example.com', 'password': 'customer123'}),
        content_type='application/json'
    )
    assert_test("Customer Login (rahul@example.com)", res.status_code == 200)

    res = client.get('/api/me/')
    assert_test("Auth State Check (/api/me/)", res.json().get('authenticated') is True)

    res = client.get('/api/my-shipments/')
    assert_test("Customer My-Shipments API", res.status_code == 200 and len(res.json().get('shipments', [])) > 0)

    # Customer logout
    client.post('/api/logout/')

    # 6. Admin Authentication & Admin Portal APIs
    res = client.post(
        '/api/admin/login/',
        data=json.dumps({'username': 'admin', 'password': 'admin123'}),
        content_type='application/json'
    )
    assert_test("Admin Login (admin / admin123)", res.status_code == 200)

    # Operations Dashboard redirect on backend port
    res = client.get('/admin/dashboard/')
    assert_test("Backend /admin/dashboard/ redirects to Frontend port 5500", res.status_code == 302 and '5500' in res.url)

    # Admin Dashboard Metrics API
    res = client.get('/api/admin/dashboard/')
    assert_test("Admin Dashboard KPI API", res.status_code == 200)
    dash_data = res.json()
    assert_test("Dashboard KPI contains stats & counts", 'stats' in dash_data and 'shipments' in dash_data['stats'])

    # Admin Shipments List API
    res = client.get('/api/admin/shipments/')
    assert_test("Admin Shipments List API", res.status_code == 200 and len(res.json().get('shipments', [])) > 0)

    # Admin Update Shipment Status & Append Milestone
    res = client.post(
        '/api/admin/shipments/PROD77412950/status/',
        data=json.dumps({
            'status': 'OUT_FOR_DELIVERY',
            'location': 'Hyderabad Delivery Center',
            'remarks': 'Assigned to courier van #8'
        }),
        content_type='application/json'
    )
    assert_test("Admin Update Shipment Status & Milestone", res.status_code == 200)

    # Check updated status on public API
    res = client.get('/api/shipments/PROD77412950/')
    assert_test("Shipment status updated to OUT FOR DELIVERY", res.json().get('shipment', {}).get('status') == 'OUT FOR DELIVERY')

    # Admin Enquiries List API
    res = client.get('/api/admin/enquiries/')
    assert_test("Admin Enquiries List API", res.status_code == 200)

    # Admin Contact Messages List API
    res = client.get('/api/admin/contact-messages/')
    assert_test("Admin Contact Messages List API", res.status_code == 200)

    # Admin Users List API
    res = client.get('/api/admin/users/')
    assert_test("Admin Users List API", res.status_code == 200)

    print("\n==========================================")
    print(f"VERIFICATION SUMMARY: {passed} PASSED, {failed} FAILED")
    print("==========================================\n")
    return failed == 0

if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)

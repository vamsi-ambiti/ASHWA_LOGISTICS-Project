import os
import sys
from pathlib import Path

# Add backend directory to sys.path
current_dir = Path(__file__).resolve().parent
backend_dir = current_dir / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ashwa.settings")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

# Ensure database migrations and demo seed are applied on startup (critical for Render PostgreSQL)
try:
    from django.core.management import call_command
    call_command('migrate', interactive=False)
except Exception as e:
    print(f"[Ashwa Startup Migrate] {e}")

try:
    from django.contrib.auth.models import User
    if not User.objects.filter(is_superuser=True).exists():
        try:
            from seed_data import seed_database
            seed_database()
        except Exception as e:
            print(f"[Ashwa Startup Seed] {e}")
except Exception as e:
    print(f"[Ashwa User Check] {e}")


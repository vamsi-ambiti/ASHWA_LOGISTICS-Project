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


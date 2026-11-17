from pathlib import Path
import os
import sys
import pymysql
import dj_database_url
pymysql.install_as_MySQLdb()

# Load environment variables from .env if available
try:
    from dotenv import load_dotenv
    # Check root, backend, and CONFIGURATION directories for .env
    current_dir = Path(__file__).resolve().parent
    base_dir = current_dir.parent
    root_dir = base_dir.parent
    for env_path in [root_dir / '.env', base_dir / '.env', root_dir / 'CONFIGURATION' / '.env']:
        if env_path.exists():
            load_dotenv(env_path)
            break
except ImportError:
    pass

# Try to register pymysql as MySQLdb if needed
try:
    import pymysql
    pymysql.install_as_MySQLdb()
except ImportError:
    pass

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = BASE_DIR.parent
FRONTEND_DIR = ROOT_DIR / 'frontend'

# Security settings
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'ashwa-production-secret-key-fallback-render-2026')
DEBUG = os.getenv('DJANGO_DEBUG', 'False').lower() == 'true'
ALLOWED_HOSTS = [
    h.strip()
    for h in os.getenv('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1,.onrender.com,testserver').split(',')
    if h.strip()
]

# Application definition
INSTALLED_APPS = [
    'corsheaders',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'logistics.apps.LogisticsConfig',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'ashwa.urls'

# Templates configuration pointing to frontend/templates and frontend/
TEMPLATE_DIRS = []
if (FRONTEND_DIR / 'templates').exists():
    TEMPLATE_DIRS.append(FRONTEND_DIR / 'templates')
if FRONTEND_DIR.exists():
    TEMPLATE_DIRS.append(FRONTEND_DIR)
if (BASE_DIR / 'templates').exists():
    TEMPLATE_DIRS.append(BASE_DIR / 'templates')

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': TEMPLATE_DIRS,
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'ashwa.wsgi.application'

default_db_url = os.getenv('DATABASE_URL') or f"sqlite:///{BASE_DIR / 'db.sqlite3'}"
DATABASES = {
    'default': dj_database_url.config(
        default=default_db_url,
        conn_max_age=600,
        conn_health_checks=True,
    )
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

# Static and media files
STATIC_URL = '/static/'
STATIC_DIRS = []
if (FRONTEND_DIR / 'static').exists():
    STATIC_DIRS.append(FRONTEND_DIR / 'static')
if (BASE_DIR / 'static').exists():
    STATIC_DIRS.append(BASE_DIR / 'static')

STATICFILES_DIRS = STATIC_DIRS
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'
WHITENOISE_USE_FINDERS = True

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Session and CSRF configuration for smooth client-side interactions
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_AGE = 86400 * 7  # 7 days

# CORS Configuration for separated Frontend & Backend servers
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'x-session-token',
    'x-user-id',
]

CSRF_TRUSTED_ORIGINS = [
    'https://*.onrender.com',
    'https://ashwa-logistics.onrender.com',
    'http://127.0.0.1:5500',
    'http://localhost:5500',
    'http://127.0.0.1:5501',
    'http://localhost:5501',
    'http://127.0.0.1:3000',
    'http://localhost:3000',
    'http://127.0.0.1:5000',
    'http://localhost:5000',
    'http://127.0.0.1:5173',
    'http://localhost:5173',
    'http://127.0.0.1:8080',
    'http://localhost:8080',
    'http://127.0.0.1:8000',
    'http://localhost:8000',
]


# Email settings
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True

EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')

DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
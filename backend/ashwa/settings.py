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
DEBUG = os.getenv('DJANGO_DEBUG', 'False').lower() == 'true'
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')
if not SECRET_KEY:
    raise RuntimeError('DJANGO_SECRET_KEY must be configured in the environment.')
ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv('DJANGO_ALLOWED_HOSTS', '127.0.0.1,localhost,testserver').split(',')
    if host.strip()
]
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

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

# Database configuration: use DATABASE_URL, explicit MySQL environment values, or local SQLite.
def configure_database():
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        return {
            'default': dj_database_url.config(
                default=database_url,
                conn_max_age=600,
                conn_health_checks=True,
            )
        }

    if os.getenv('DB_ENGINE', '').strip() == 'django.db.backends.mysql':
        return {
            'default': {
                'ENGINE': 'django.db.backends.mysql',
                'NAME': os.getenv('DB_NAME', 'ashwa_logistics'),
                'USER': os.getenv('DB_USER', 'root'),
                'PASSWORD': os.getenv('DB_PASSWORD', ''),
                'HOST': os.getenv('DB_HOST', '127.0.0.1'),
                'PORT': os.getenv('DB_PORT', '3306'),
            }
        }

    return {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

DATABASES = configure_database()

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
STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Session and CSRF configuration for smooth client-side interactions
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_AGE = 86400 * 7  # 7 days
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# CORS is only open during local development; the hosted app is same-origin.
CORS_ALLOW_ALL_ORIGINS = DEBUG
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
    origin.strip()
    for origin in os.getenv(
        'DJANGO_CSRF_TRUSTED_ORIGINS',
        'http://127.0.0.1:5500,http://localhost:5500,http://127.0.0.1:8000,http://localhost:8000',
    ).split(',')
    if origin.strip()
]


# Email settings
EMAIL_BACKEND = os.getenv(
    'EMAIL_BACKEND',
    'django.core.mail.backends.smtp.EmailBackend'
)
EMAIL_ENABLED = os.getenv('EMAIL_ENABLED', 'false').lower() in {'1', 'true', 'yes'}
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'true').lower() in {'1', 'true', 'yes'}
EMAIL_TIMEOUT = int(os.getenv('EMAIL_TIMEOUT', '5'))

EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')

DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER)

from pathlib import Path
import os
from django.contrib.messages import constants as messages
import cloudinary
import cloudinary.uploader
import cloudinary.api
import sys
import json
import dj_database_url  # ← IMPORTANTE: Agregar esta importación
from dotenv import load_dotenv  # ← Para cargar variables de entorno

# Cargar variables de entorno desde .env (solo para desarrollo local)
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# ============================================
# SECRET KEY - Usar variable de entorno o generar una nueva
# ============================================
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-7xx+3%9o4ni5#7s$0)3lyjb8g4albmz533@^+3w)1hm$v$06^)')

# Silenciar warnings específicos
import warnings
warnings.filterwarnings("ignore", module="admin_interface.templatetags")

# ============================================
# DEBUG - Siempre False en producción
# ============================================
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

# ============================================
# ALLOWED_HOSTS - Configuración corregida
# ============================================
ALLOWED_HOSTS = [
    'biblioteca-production-b2fa.up.railway.app',  # ← Tu dominio correcto
    '.up.railway.app',  # ← Permite todos los subdominios de Railway
    '127.0.0.1',
    'localhost',
    'healthcheck.railway.app',
    '0.0.0.0',
]

# ============================================
# Application definition
# ============================================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Cloudinary (solo para imágenes y PDFs pequeños)
    'cloudinary',
    'cloudinary_storage',
    
    # Apps propias
    'biblioartdis.apps.BiblioartdisConfig',
    
    # Aplicaciones adicionales
    'django_extensions',
    'django_filters',
    'django_cleanup.apps.CleanupConfig',
    'rest_framework',
    'widget_tweaks',
    'import_export',
    'django_session_timeout',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_session_timeout.middleware.SessionTimeoutMiddleware',
]

ROOT_URLCONF = 'arteydis.urls'

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

# ============================================
# TEMPLATES - ¡CORREGIDO! Ahora busca en la carpeta templates/
# ============================================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates',  # ← ¡ESTA ES LA CLAVE! Busca en la raíz/templates/
            BASE_DIR / 'biblioartdis' / 'templates',  # ← También busca en la app
        ],
        'APP_DIRS': True,  # ← Busca en templates/ de cada app instalada
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# ============================================
# LOGGING - Mejorado para producción
# ============================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'default',
        },
        'file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'django_errors.log'),
            'maxBytes': 10 * 1024 * 1024,
            'backupCount': 5,
            'formatter': 'default',
        },
    },
    'formatters': {
        'default': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['console', 'file'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': False,
        },
        'biblioartdis': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        'cloudinary': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': True,
        },
    },
}

# Crear directorio de logs si no existe
if not os.path.exists(os.path.join(BASE_DIR, 'logs')):
    os.makedirs(os.path.join(BASE_DIR, 'logs'))

MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'
LOGIN_REDIRECT_URL = '/inicio/'
LOGOUT_REDIRECT_URL = '/'
LOGIN_URL = '/'

WSGI_APPLICATION = 'arteydis.wsgi.application'

# ============================================
# BASE DE DATOS - CORREGIDA CON dj_database_url
# ============================================
# Usar variable de entorno DATABASE_URL (Recomendado para Railway)
DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL:
    # Usar la URL de la variable de entorno (Railway)
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
            ssl_require=True
        )
    }
else:
    # Fallback para desarrollo local - CREDENCIALES DE SUPABASE
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'postgres',
            'USER': 'postgres.vmwkbkvsthswxshcwhmp',
            'PASSWORD': 'cnPd.fxp4x.5kMQ2',
            'HOST': 'aws-1-us-east-1.pooler.supabase.com',
            'PORT': '6543',
            'OPTIONS': {
                'sslmode': 'require',
            },
            'CONN_MAX_AGE': 60,
            'CONN_HEALTH_CHECKS': True,
        }
    }

# ============================================
# Password validation
# ============================================
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 9},
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Configuración de timeout de sesión
SESSION_EXPIRE_SECONDS = 3600
SESSION_EXPIRE_AFTER_LAST_ACTIVITY = True
SESSION_TIMEOUT_REDIRECT = '/'

# ============================================
# Internationalization
# ============================================
LANGUAGE_CODE = 'es'
TIME_ZONE = 'America/La_Paz'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Configuración de mensajes
MESSAGE_TAGS = {
    messages.DEBUG: 'alert-info',
    messages.INFO: 'alert-info',
    messages.SUCCESS: 'alert-success',
    messages.WARNING: 'alert-warning',
    messages.ERROR: 'alert-danger',
}

X_FRAME_OPTIONS = 'SAMEORIGIN'

# ============================================
# CONFIGURACIÓN DE ARCHIVOS ESTÁTICOS
# ============================================
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# ============================================
# CONFIGURACIÓN DE CLOUDINARY - Usar variables de entorno
# ============================================
cloudinary.config(
    cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME', 'dnnl3rije'),
    api_key=os.environ.get('CLOUDINARY_API_KEY', '372388277625767'),
    api_secret=os.environ.get('CLOUDINARY_API_SECRET', '1Gjjfdf968eIypjxyu_nr3fo2Mk'),
    secure=True
)

CLOUDINARY_STORAGE = {
    'CLOUD_NAME': os.environ.get('CLOUDINARY_CLOUD_NAME', 'dnnl3rije'),
    'API_KEY': os.environ.get('CLOUDINARY_API_KEY', '372388277625767'),
    'API_SECRET': os.environ.get('CLOUDINARY_API_SECRET', '1Gjjfdf968eIypjxyu_nr3fo2Mk'),
    'SECURE': True,
}

# Usar Cloudinary Storage SOLO para imágenes y PDFs pequeños
DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
MEDIA_URL = '/media/'

# ============================================
# CONFIGURACIÓN DE GOOGLE DRIVE
# ============================================
GOOGLE_DRIVE_CREDENTIALS_JSON = os.environ.get('GOOGLE_DRIVE_CREDENTIALS_JSON')
if GOOGLE_DRIVE_CREDENTIALS_JSON:
    try:
        GOOGLE_DRIVE_CREDENTIALS = json.loads(GOOGLE_DRIVE_CREDENTIALS_JSON)
        print("✅ Google Drive credentials loaded successfully")
    except json.JSONDecodeError as e:
        GOOGLE_DRIVE_CREDENTIALS = None
        print(f"❌ Error decoding Google Drive credentials: {e}")
else:
    GOOGLE_DRIVE_CREDENTIALS = None
    print("⚠️ GOOGLE_DRIVE_CREDENTIALS_JSON not found")

GOOGLE_DRIVE_FOLDER_ID = os.environ.get('GOOGLE_DRIVE_FOLDER_ID', '')

# ============================================
# CONFIGURACIÓN DE EMAIL - Usar variables de entorno
# ============================================
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 465
EMAIL_USE_SSL = True
EMAIL_USE_TLS = False
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
if EMAIL_HOST_USER and EMAIL_HOST_PASSWORD:
    DEFAULT_FROM_EMAIL = f'Biblioteca ARTyDIS <{EMAIL_HOST_USER}>'
    print("✅ Email configured successfully")
else:
    DEFAULT_FROM_EMAIL = 'Biblioteca ARTyDIS <noreply@example.com>'
    print("⚠️ Email credentials not configured")
EMAIL_TIMEOUT = 30

# ============================================
# CONFIGURACIONES DE SEGURIDAD PARA PRODUCCIÓN
# ============================================
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# HSTS - Desactivado temporalmente para pruebas
# SECURE_HSTS_SECONDS = 31536000
# SECURE_HSTS_INCLUDE_SUBDOMAINS = True
# SECURE_HSTS_PRELOAD = True

CSRF_TRUSTED_ORIGINS = [
    'https://biblioteca-production-b2fa.up.railway.app',  # ← Tu dominio correcto
]

CSRF_COOKIE_HTTPONLY = False
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_AGE = 3600

# ============================================
# CONFIGURACIONES ADICIONALES
# ============================================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
SILENCED_SYSTEM_CHECKS = ['security.W019']
IMPORT_EXPORT_USE_TRANSACTIONS = True
IMPORT_EXPORT_SKIP_ADMIN_LOG = False

# ============================================
# CONFIGURACIÓN PARA EVITAR SEÑALES DUPLICADAS
# ============================================
IS_MANAGEMENT_COMMAND = 'manage.py' in sys.argv[0] if sys.argv else False

# ============================================
# CONFIGURACIÓN ADICIONAL PARA EMAIL
# ============================================
EMAIL_USE_LOCALTIME = True
EMAIL_SSL_CERTFILE = None
EMAIL_SSL_KEYFILE = None

# ============================================
# LÍMITES DE SUBIDA DE ARCHIVOS
# ============================================
DATA_UPLOAD_MAX_NUMBER_FIELDS = 10000
DATA_UPLOAD_MAX_NUMBER_FILES = 100
DATA_UPLOAD_MAX_FILE_SIZE = 1024 * 1024 * 500  # 500 MB